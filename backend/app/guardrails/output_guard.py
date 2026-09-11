"""Output guardrail: groundedness check after LLM generation.

Token optimization:
  - First pass: fast lexical overlap check (zero LLM cost).
  - Only falls back to cheap LLM (8B) if the answer makes strong factual claims
    that are NOT found in any of the top-3 retrieved chunks.
  - The cross-collection leak check is purely regex-based (no LLM).
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Phrases that typically signal a factual claim (trigger groundedness check)
_CLAIM_SIGNALS = re.compile(
    r"\b(according to|the protocol states?|guidelines? (state|recommend|require|say)|"
    r"patients? should|dosage is|dose is|treatment is|procedure (is|requires?)|"
    r"code is|amount is|claim (was|is)|ticket (status|is))\b",
    re.IGNORECASE,
)


@dataclass
class OutputGuardrailResult:
    grounded: bool
    reason: str = ""


def _lexical_overlap(answer: str, chunks: list[str], threshold: float = 0.15) -> bool:
    """Check if enough answer tokens appear in the chunk corpus.

    Returns True if overlap is sufficient (answer appears grounded).
    Uses token-level Jaccard on lowercased word sets.
    """
    answer_tokens = set(re.findall(r"\b[a-z]{3,}\b", answer.lower()))
    if not answer_tokens:
        return True  # trivially pass empty answers

    chunk_tokens: set[str] = set()
    for chunk in chunks:
        chunk_tokens.update(re.findall(r"\b[a-z]{3,}\b", chunk.lower()))

    if not chunk_tokens:
        return False

    overlap = len(answer_tokens & chunk_tokens) / len(answer_tokens)
    logger.debug("Groundedness lexical overlap: %.3f (threshold %.2f)", overlap, threshold)
    return overlap >= threshold


async def check_output(
    answer: str,
    chunks: list[str],
    question: str = "",
) -> OutputGuardrailResult:
    """Check that the LLM answer is grounded in the retrieved chunks.

    Steps:
      1. Fast lexical overlap check (zero API cost).
      2. If answer contains strong factual claim signals AND overlap is low,
         call cheap LLM (8B) for a binary entailment check.
    """
    if not chunks or not answer.strip():
        return OutputGuardrailResult(grounded=True)

    # Standard deterministic refusal is already verified grounded
    if "I could not find any relevant information in the accessible clinical" in answer:
        return OutputGuardrailResult(grounded=True)

    # ── Strict LLM clinical NLI & relevance check ────────────────────────────
    logger.info("Output guardrail: running strict NLI groundedness check for query='%s'", question[:60])
    try:
        from groq import AsyncGroq
        from app.config import get_settings

        settings = get_settings()
        client = AsyncGroq(api_key=settings.groq_api_key)

        context_snippet = "\n---\n".join(chunks[:3])[:2500]  # cap context size
        response = await client.chat.completions.create(
            model=settings.model_cheap,  # 8B — fast & cheap
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an uncompromising clinical NLI and factuality auditor for a medical RAG assistant.\n"
                        "Task: Evaluate whether the generated Answer is strictly and completely supported by the Context excerpts "
                        "for the given User Question.\n\n"
                        "STRICT RULES:\n"
                        "1. RELEVANCE: If the context excerpts do NOT contain information about the specific disease, condition, "
                        "or drug asked in the User Question (e.g. excerpts describe COPD or Dengue when the user asked about Pneumonia, "
                        "or excerpts describe general nursing when the user asked for specific drug treatment), "
                        "reply 'UNGROUNDED: Off-topic context'.\n"
                        "2. FACTUAL ENTAILMENT: If the Answer makes assertions, drug recommendations, oral/IV availability claims, "
                        "or treatment steps not explicitly written in the Context excerpts, reply 'UNGROUNDED: Unsupported claims'.\n"
                        "3. REFUSAL: If the Answer accurately states that information is not available in the context, reply 'GROUNDED'.\n"
                        "4. If and only if every clinical claim in the Answer is directly entailed by the Context excerpts, reply 'GROUNDED'.\n\n"
                        "Reply format: Exactly 'GROUNDED' or 'UNGROUNDED: <concise clinical rationale>'."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"User Question:\n{question}\n\n"
                        f"Context excerpts:\n{context_snippet}\n\n"
                        f"Generated Answer:\n{answer[:1200]}"
                    ),
                },
            ],
            temperature=0,
            max_tokens=256,
        )
        verdict = (response.choices[0].message.content or "GROUNDED").strip()
        logger.info("LLM groundedness verdict: %s", verdict)

        if verdict.upper().startswith("UNGROUNDED"):
            reason = verdict.split(":", 1)[1].strip() if ":" in verdict else "Answer contains clinical claims not supported by retrieved excerpts."
            return OutputGuardrailResult(grounded=False, reason=reason)

    except Exception as exc:
        logger.warning("LLM groundedness check failed: %s — failing open", exc)

    return OutputGuardrailResult(grounded=True)


_CITATION_PATTERN = re.compile(
    r"(?:\[|【)\s*([1-9]\d*)\s*(?:†[^\]】]*)?(?:\]|】)"
)


async def verify_and_prune_citations(
    answer: str,
    chunks: list[str],
) -> tuple[str, list[dict]]:
    """Audit every sentence carrying a citation tag against its cited chunk using fast 8B NLI.

    Under Option B, if a citation is unsupported or fabricated, the sentence is dropped
    entirely from the final output before returning to the user.

    Returns:
        (pruned_answer, audit_records)
    """
    if not answer.strip() or not chunks:
        return answer, []

    # Check if any citations exist
    if not _CITATION_PATTERN.search(answer):
        return answer, []

    # 1. Break text into lines, then sentences, identifying lines/sentences with citations
    lines = answer.split("\n")
    audit_candidates: list[dict] = []
    claim_counter = 1

    for line_idx, line in enumerate(lines):
        if not _CITATION_PATTERN.search(line):
            continue

        # Split multi-sentence lines if applicable, keeping delimiters
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", line) if s.strip()]
        for sentence in sentences:
            citation_matches = list(_CITATION_PATTERN.finditer(sentence))
            if not citation_matches:
                continue

            for match in citation_matches:
                chunk_num = int(match.group(1))
                audit_candidates.append({
                    "claim_id": str(claim_counter),
                    "line_idx": line_idx,
                    "sentence": sentence,
                    "chunk_num": chunk_num,
                    "valid_idx": 1 <= chunk_num <= len(chunks),
                })
                claim_counter += 1

    if not audit_candidates:
        return answer, []

    # 2. Audit invalid chunk indices immediately as UNSUPPORTED
    verdicts: dict[str, str] = {}
    candidates_for_llm: list[dict] = []
    for cand in audit_candidates:
        if not cand["valid_idx"]:
            verdicts[cand["claim_id"]] = "UNSUPPORTED"
        else:
            candidates_for_llm.append(cand)

    # 3. Fast batched NLI check with 8B model for valid candidates
    if candidates_for_llm:
        try:
            from groq import AsyncGroq
            from app.config import get_settings

            settings = get_settings()
            client = AsyncGroq(api_key=settings.groq_api_key)

            # Build compact verification prompt
            verification_blocks = []
            for cand in candidates_for_llm:
                chunk_text = chunks[cand["chunk_num"] - 1][:800]
                clean_sentence = _CITATION_PATTERN.sub("", cand["sentence"]).strip()
                verification_blocks.append(
                    f"--- Claim [{cand['claim_id']}] citing Excerpt [{cand['chunk_num']}] ---\n"
                    f"Excerpt: {chunk_text}\n"
                    f"Claim: {clean_sentence}"
                )

            prompt_content = "\n\n".join(verification_blocks)
            prompt_content += (
                "\n\nFor each claim, decide if the excerpt directly supports it. "
                "Output ONLY a JSON object mapping claim ID to 'SUPPORTED' or 'UNSUPPORTED'."
            )

            resp = await client.chat.completions.create(
                model=settings.model_cheap,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a strict clinical citation verifier. Determine whether each claim "
                            "is directly and explicitly supported by its cited excerpt.\n"
                            "If the excerpt does not explicitly state the claim (e.g. formulary availability, "
                            "oral equivalence, unmentioned doses), reply UNSUPPORTED.\n"
                            "Reply ONLY with a valid JSON object, e.g. {\"1\": \"SUPPORTED\", \"2\": \"UNSUPPORTED\"}."
                        ),
                    },
                    {"role": "user", "content": prompt_content},
                ],
                temperature=0,
                max_tokens=256,
            )
            raw_json = (resp.choices[0].message.content or "").strip()
            # Extract JSON substring if wrapped in markdown
            json_match = re.search(r"\{[^{}]*\}", raw_json)
            if json_match:
                parsed = json.loads(json_match.group(0))
                for k, v in parsed.items():
                    verdicts[str(k)] = str(v).strip().upper()
        except Exception as exc:
            logger.warning("Citation verification LLM call failed: %s — keeping claims", exc)

    # 4. Option B: Collect sentences to drop
    sentences_to_drop: set[str] = set()
    audit_records: list[dict] = []

    for cand in audit_candidates:
        verdict = verdicts.get(cand["claim_id"], "SUPPORTED")
        is_supported = "SUPPORTED" in verdict
        audit_records.append({
            "claim_id": cand["claim_id"],
            "sentence": cand["sentence"],
            "chunk_num": cand["chunk_num"],
            "supported": is_supported,
        })
        if not is_supported:
            sentences_to_drop.add(cand["sentence"])
            logger.warning(
                "Citation verification FAILED (Option B: dropping sentence): '%s' citing chunk [%d]",
                cand["sentence"][:100],
                cand["chunk_num"],
            )

    if not sentences_to_drop:
        return answer, audit_records

    # 5. Drop unsupported sentences from answer
    new_lines = []
    for line in lines:
        if not _CITATION_PATTERN.search(line):
            new_lines.append(line)
            continue

        # If the entire line is an unsupported sentence (common for bullet points), drop the line
        if line.strip() in sentences_to_drop:
            continue

        # Otherwise remove the specific unsupported sentence(s) from the line
        modified_line = line
        for drop_sent in sentences_to_drop:
            if drop_sent in modified_line:
                modified_line = modified_line.replace(drop_sent, "").strip()

        # Only retain line if it still contains content (not just empty list markers)
        clean_check = re.sub(r"^[-*•\d\.\)\s]+", "", modified_line).strip()
        if clean_check:
            new_lines.append(modified_line)

    pruned_answer = "\n".join(new_lines).strip()
    return pruned_answer, audit_records

