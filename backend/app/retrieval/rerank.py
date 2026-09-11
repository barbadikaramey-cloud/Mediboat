"""CrossEncoder reranker: narrows top-K candidates to top-N for the LLM.

This is the primary token optimization step: instead of sending top-10
chunks to the LLM, we load the cross-encoder locally (CPU-only, free),
jointly score query+chunk, and forward only the reranked top-3.

The cross-encoder sees: "[SEP]".join([query, chunk_text])
This is more accurate than cosine similarity for relevance scoring.
"""
from __future__ import annotations

import logging

from sentence_transformers import CrossEncoder

from app.config import get_settings
from app.observability import logfire_info, logfire_span
from app.retrieval.hybrid_search import RetrievedChunk

logger = logging.getLogger(__name__)

# Module-level singleton — loaded once, reused across all requests
_cross_encoder: CrossEncoder | None = None


def _get_cross_encoder() -> CrossEncoder:
    global _cross_encoder
    if _cross_encoder is None:
        settings = get_settings()
        logger.info("Loading CrossEncoder: %s", settings.reranker_model)
        # Explicitly disable low_cpu_mem_usage to prevent meta-tensor loading
        # (newer transformers defaults to True, which loads an empty model shell
        # with meta tensors, then fills weights — but CrossEncoder.predict()
        # calls model.to(device) before weights are filled, causing
        # "Cannot copy out of meta tensor" errors).
        _cross_encoder = CrossEncoder(
            settings.reranker_model,
            max_length=512,
            device="cpu",
            automodel_args={"low_cpu_mem_usage": False},
        )
    return _cross_encoder


def rerank(
    query: str,
    chunks: list[RetrievedChunk],
    top_n: int | None = None,
    **kwargs,
) -> list[RetrievedChunk]:
    """Rerank retrieved chunks using CrossEncoder; return top_n reranked chunks without floor filtering.
    Relevance, factuality, and refusal decisions are strictly enforced by the downstream NLI prompts.

    Args:
        query:  The user's original or contextualized question.
        chunks: Broad candidate set (e.g. from hybrid search).
        top_n:  Number of top reranked chunks to return (default: settings.rerank_top_n).

    Returns:
        List of RetrievedChunk sorted by CrossEncoder score desc, truncated to top_n.
    """
    settings = get_settings()
    n = top_n or settings.rerank_top_n

    if not chunks:
        return []

    with logfire_span(
        "retrieval.cross_encoder_rerank",
        query=query[:100],
        candidate_count=len(chunks),
        top_n=n,
    ):
        model = _get_cross_encoder()

        # Map known document page topics so isolated subheadings (e.g. 'Antimicrobial therapy')
        # retain their parent clinical condition (e.g. 'Community-Acquired Pneumonia')
        _PAGE_TOPICS: dict[str, dict[int, str]] = {
            "treatment_protocols.pdf": {
                2: "Type 2 Diabetes Mellitus",
                3: "Hypertension - Stage 2",
                4: "Community-Acquired Pneumonia",
                5: "Acute Myocardial Infarction - NSTEMI",
                6: "Paediatric Fever Management",
                7: "Dengue Fever",
                8: "Acute Exacerbation of COPD",
                9: "Key Drug Interactions & Cautions",
            }
        }

        # Build (query, passage) pairs for joint scoring, including parent topic and section context
        def _scoring_text(chunk: RetrievedChunk) -> str:
            parent_topic = _PAGE_TOPICS.get(chunk.source_document, {}).get(chunk.page_number or 0, "")
            header_parts = []
            if parent_topic:
                header_parts.append(parent_topic)
            if chunk.section_title and chunk.section_title != parent_topic:
                header_parts.append(chunk.section_title)
            prefix = " - ".join(header_parts)
            prefix_str = f"[{prefix}]\n" if prefix else ""
            return f"{prefix_str}{chunk.text}"

        pairs = [(query, _scoring_text(c)) for c in chunks]
        scores: list[float] = model.predict(pairs, show_progress_bar=False).tolist()

        # Attach CE scores and sort descending
        scored = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)

        # Log reranking reordering and individual scores
        for new_rank, (score, chunk) in enumerate(scored[:max(n, 5)]):
            original_rank = chunks.index(chunk)
            logfire_info(
                "Rerank [{orig}→{new}] score={score:.4f} | {doc} | {sec}",
                orig=original_rank,
                new=new_rank,
                score=score,
                doc=chunk.source_document,
                sec=chunk.section_title[:60] if chunk.section_title else "(no section)",
            )

        # Keep top_n reranked chunks (no floor filtering; strong NLI prompts govern refusal)
        top_chunks: list[RetrievedChunk] = []
        for score, chunk in scored[:n]:
            chunk.score = score  # update score to CE score for transparency
            top_chunks.append(chunk)

        logfire_info(
            "Reranked {candidates} candidates -> top {kept} chunks (floor disabled, NLI prompt enforces relevance)",
            candidates=len(chunks),
            kept=len(top_chunks),
            top_score=top_chunks[0].score if top_chunks else None,
        )
        return top_chunks
