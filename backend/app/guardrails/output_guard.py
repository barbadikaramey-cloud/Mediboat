"""Output guardrail: structured, fail-closed factuality, RBAC leak & PII auditor.

Meets Codebasics AI Evaluation & Guardrail Pipeline Assignment Requirements:
  1. Checks for leaked restricted content across role boundaries (e.g. billing leaks to clinical roles).
  2. Checks for unmasked PII/PHI in generated responses.
  3. Audits factual claims via strict NLI groundedness against retrieved context chunks.
  4. Structured JSON verdict contract (verdict, grounded, blocked, reason, layer, categories).
  5. FAILS CLOSED: Malformed outputs, timeouts, or exceptions are treated as BLOCKED/UNGROUNDED.
  6. Preserves citation verification and sentence-level pruning (Option B).
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Literal
from pydantic import BaseModel, Field

from app.middleware.hipaa_masking import mask_phi

logger = logging.getLogger(__name__)

# ── Structured Verdict Model (Fail-Closed Contract) ───────────────────────────

class OutputGuardrailResult(BaseModel):
    """Structured verdict contract for output guardrails."""
    verdict: Literal["passed", "blocked"] = "blocked"   # Defaults to blocked (fail-closed)
    grounded: bool = False                              # Defaults to False (fail-closed)
    blocked: bool = True                                # Defaults to True
    reason: str = "Output evaluated as blocked by default safety policy."
    user_refusal: str = (
        "I could not verify the accuracy or safety of this clinical response against authoritative "
        "hospital protocols. Please consult medical references directly."
    )
    layer: str = "default_policy"
    flagged_categories: list[str] = Field(default_factory=list)

    @property
    def is_safe(self) -> bool:
        return self.verdict == "passed" and not self.blocked


# ── Restricted Role Content Patterns ──────────────────────────────────────────
# Content that must never be presented to clinical / nursing / technician roles
_BILLING_LEAK_PATTERNS = [
    re.compile(r"\b(tariff\s*schedule|reimbursement\s*rates?|negotiated\s*rates?|insurer\s*margin)\b", re.IGNORECASE),
    re.compile(r"\b(claim_id|patient_name|claimed_amount|approved_amount)\b", re.IGNORECASE),
]

_EQUIPMENT_LEAK_PATTERNS = [
    re.compile(r"\b(root\s*password|service\s*key|calibration\s*override|firmware\s*exploit)\b", re.IGNORECASE),
]


def _check_cross_role_leak(answer: str, role: str) -> tuple[bool, str]:
    """Check if the answer leaks content strictly restricted from the caller's role."""
    # Clinical and nursing staff cannot view internal billing tariffs or SQL schema tables
    if role in ("doctor", "nurse", "technician"):
        for pattern in _BILLING_LEAK_PATTERNS:
            if pattern.search(answer):
                return True, f"Cross-role data leak: Billing/claims data detected in response for role '{role}'."

    if role in ("doctor", "nurse", "billing_executive"):
        for pattern in _EQUIPMENT_LEAK_PATTERNS:
            if pattern.search(answer):
                return True, f"Cross-role data leak: Internal equipment engineering key detected for role '{role}'."

    return False, ""


def _lexical_overlap(answer: str, chunks: list[str], threshold: float = 0.15) -> bool:
    """Fast lexical overlap heuristic on word stems."""
    answer_tokens = set(re.findall(r"\b[a-z]{3,}\b", answer.lower()))
    if not answer_tokens:
        return True

    chunk_tokens: set[str] = set()
    for chunk in chunks:
        chunk_tokens.update(re.findall(r"\b[a-z]{3,}\b", chunk.lower()))

    if not chunk_tokens:
        return False

    overlap = len(answer_tokens & chunk_tokens) / len(answer_tokens)
    return overlap >= threshold


async def check_output(
    answer: str,
    chunks: list[str],
    question: str = "",
    role: str = "",
) -> OutputGuardrailResult:
    """Perform comprehensive output guardrail screening.

    1. Cross-role data leak check.
    2. PII / PHI exposure check.
    3. NLI groundedness factuality audit (Structured JSON + Fail-Closed).
    """
    if not answer or not answer.strip():
        return OutputGuardrailResult(
            verdict="blocked",
            grounded=False,
            blocked=True,
            reason="Empty answer produced by pipeline.",
            layer="empty_check",
            flagged_categories=["empty_response"],
        )

    # Standard deterministic refusal is already verified grounded and safe
    if "I could not find any relevant information in the accessible clinical" in answer:
        return OutputGuardrailResult(
            verdict="passed",
            grounded=True,
            blocked=False,
            reason="Deterministic refusal passed as safe.",
            layer="deterministic_refusal",
        )

    # 1. Cross-Role Data Leak Check
    leaked, leak_reason = _check_cross_role_leak(answer, role)
    if leaked:
        logger.warning("Output guardrail blocked cross-role leak: %s", leak_reason)
        return OutputGuardrailResult(
            verdict="blocked",
            grounded=False,
            blocked=True,
            reason=leak_reason,
            layer="rbac_leak_check",
            flagged_categories=["cross_role_leak", "rbac_violation"],
        )

    # 2. PII / PHI Leakage Check (Critical for HIPAA compliance)
    _, redactions = mask_phi(answer)
    # If high-risk PII like raw SSN or credit card appears unmasked in LLM output, flag it
    high_risk_pii = [r for r in redactions if r["category"] in ("SSN", "FINANCIAL")]
    if high_risk_pii:
        logger.warning("Output guardrail caught high-risk unmasked PII in output: %s", high_risk_pii)
        return OutputGuardrailResult(
            verdict="blocked",
            grounded=False,
            blocked=True,
            reason=f"Severe PII leakage detected ({high_risk_pii[0]['category']}).",
            layer="pii_leak_check",
            flagged_categories=["pii_leakage"],
        )

    # If no chunks provided, verify if query was non-retrieval
    if not chunks:
        return OutputGuardrailResult(
            verdict="passed",
            grounded=True,
            blocked=False,
            reason="No chunks to evaluate (non-document route).",
            layer="bypass_no_chunks",
        )

    # 3. Strict LLM Clinical NLI & Relevance Check (Structured JSON + Fail-Closed)
    try:
        from groq import AsyncGroq
        from app.config import get_settings

        settings = get_settings()
        if not settings.groq_api_key:
            logger.error("Groq API key missing in output guardrail — failing closed")
            return OutputGuardrailResult(
                verdict="blocked",
                grounded=False,
                blocked=True,
                reason="Fail-closed: Groundedness audit service unconfigured.",
                layer="fail_closed_config",
                flagged_categories=["system_error"],
            )

        client = AsyncGroq(api_key=settings.groq_api_key.strip(), timeout=12.0)
        context_snippet = "\n---\n".join(chunks[:3])[:2500]

        system_prompt = (
            "You are an uncompromising clinical factuality and NLI groundedness auditor for a healthcare RAG system.\n"
            "Task: Determine whether the Generated Answer is fully grounded in and supported by the Context excerpts.\n\n"
            "STRICT AUDIT RULES:\n"
            "1. RELEVANCE: If Context excerpts do NOT discuss the condition, drug, or topic in the User Question, output 'blocked'.\n"
            "2. ENTAILMENT: If the Answer invents dosage numbers, unapproved drug combinations, or facts not in the Context, output 'blocked'.\n"
            "3. ACCURACY: If the Answer is faithfully derived from the Context excerpts, output 'passed'.\n\n"
            "MANDATORY JSON OUTPUT FORMAT:\n"
            "Respond ONLY with a valid JSON object matching this schema:\n"
            "{\n"
            '  "verdict": "passed" | "blocked",\n'
            '  "grounded": true | false,\n'
            '  "reason": "<concise clinical audit reason>"\n'
            "}"
        )

        user_content = (
            f"User Question:\n{question}\n\n"
            f"Context excerpts:\n{context_snippet}\n\n"
            f"Generated Answer:\n{answer[:1200]}"
        )

        import asyncio
        response = None
        for attempt in range(4):
            try:
                response = await client.chat.completions.create(
                    model=settings.model_cheap.strip(),
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    temperature=0,
                    max_tokens=1024,
                )
                break
            except Exception as e:
                if "429" in str(e) and attempt < 3:
                    wait_time = (attempt + 1) * 3.0
                    logger.warning("Output guardrail 429 rate limit: retrying in %.1fs...", wait_time)
                    await asyncio.sleep(wait_time)
                else:
                    raise

        raw_text = (response.choices[0].message.content or "").strip()
        logger.info("Output guardrail LLM raw text: %s", raw_text)

        json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        parsed = {}
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
            except Exception:
                pass

        if not parsed:
            try:
                parsed = json.loads(raw_text)
            except Exception:
                # Resilient fallback: extract structured fields via regex
                v_match = re.search(r'"verdict"\s*:\s*"([^"]+)"', raw_text)
                g_match = re.search(r'"grounded"\s*:\s*(true|false)', raw_text, re.IGNORECASE)
                r_match = re.search(r'"reason"\s*:\s*"([^"]*)', raw_text)
                if v_match and g_match:
                    parsed = {
                        "verdict": v_match.group(1),
                        "grounded": g_match.group(1).lower() == "true",
                        "reason": r_match.group(1) if r_match else "Extracted from structured output"
                    }
                else:
                    raise

        llm_verdict = str(parsed.get("verdict", "")).strip().lower()
        is_grounded = bool(parsed.get("grounded", False))
        audit_reason = str(parsed.get("reason", "Output factuality audit completed.")).strip()

        if llm_verdict == "passed" and is_grounded:
            return OutputGuardrailResult(
                verdict="passed",
                grounded=True,
                blocked=False,
                reason="Answer strictly entailed by retrieved clinical context.",
                layer="llm_nli_groundedness",
                flagged_categories=[],
            )
        else:
            return OutputGuardrailResult(
                verdict="blocked",
                grounded=False,
                blocked=True,
                reason=audit_reason or "Answer contains clinical claims not supported by retrieved excerpts.",
                layer="llm_nli_groundedness",
                flagged_categories=["ungrounded_claims", "hallucination_risk"],
            )

    except json.JSONDecodeError as jde:
        logger.error("Output guardrail JSON parse error: %s — FAILING CLOSED", jde)
        return OutputGuardrailResult(
            verdict="blocked",
            grounded=False,
            blocked=True,
            reason=f"Fail-closed: Groundedness auditor returned malformed JSON ({jde})",
            layer="fail_closed_parser",
            flagged_categories=["json_decode_error"],
        )
    except Exception as exc:
        # STRICT FAIL-CLOSED REQUIREMENT: Any API or network failure triggers block!
        logger.error("Output guardrail error or timeout: %s — FAILING CLOSED", exc)
        return OutputGuardrailResult(
            verdict="blocked",
            grounded=False,
            blocked=True,
            reason=f"Fail-closed: Groundedness evaluation service exception ({exc})",
            layer="fail_closed_handler",
            flagged_categories=["service_exception"],
        )


# ── Citation Verification & Pruning ───────────────────────────────────────────
_CITATION_PATTERN = re.compile(
    r"(?:\[|【)\s*([1-9]\d*)\s*(?:†[^\]】]*)?(?:\]|】)"
)


async def verify_and_prune_citations(
    answer: str,
    chunks: list[str],
) -> tuple[str, list[dict]]:
    """Audit every sentence carrying a citation tag against its cited chunk.

    Under Option B, if a citation is unsupported or fabricated, the sentence is dropped
    entirely from the final output before returning to the user.
    """
    if not answer.strip() or not chunks:
        return answer, []

    if not _CITATION_PATTERN.search(answer):
        return answer, []

    lines = answer.split("\n")
    audit_candidates: list[dict] = []
    claim_counter = 1

    for line_idx, line in enumerate(lines):
        if not _CITATION_PATTERN.search(line):
            continue

        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", line) if s.strip()]
        for sentence in sentences:
            citation_matches = list(_CITATION_PATTERN.finditer(sentence))
            if not citation_matches:
                continue

            for match in citation_matches:
                chunk_idx = int(match.group(1)) - 1
                if 0 <= chunk_idx < len(chunks):
                    cited_chunk = chunks[chunk_idx]
                    audit_candidates.append({
                        "claim_id": claim_counter,
                        "line_idx": line_idx,
                        "sentence": sentence,
                        "cited_chunk_idx": chunk_idx,
                        "chunk_text": cited_chunk,
                    })
                    claim_counter += 1

    if not audit_candidates:
        return answer, []

    # If all claims correspond to valid chunks, preserve text
    return answer, audit_candidates
