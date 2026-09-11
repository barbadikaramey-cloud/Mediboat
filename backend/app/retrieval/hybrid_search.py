"""Hybrid retrieval: dense + sparse (BM25) search via Qdrant native fusion.

A single Qdrant query fuses dense cosine similarity and BM25 sparse scores
using Reciprocal Rank Fusion (RRF) — no two-query merge in app code.

The RBAC filter is applied server-side inside the same Qdrant query, so
restricted documents never reach the application layer.
"""
from __future__ import annotations

import logging
import hashlib
import re
from dataclasses import dataclass

from fastembed import TextEmbedding, SparseTextEmbedding
from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.http.models import (
    Filter,
    FusionQuery,
    NamedSparseVector,
    NamedVector,
    Prefetch,
    SparseVector,
    SearchRequest,
)

from app.config import get_settings
from app.observability import logfire_info, logfire_span
from app.rbac import build_qdrant_filter

logger = logging.getLogger(__name__)

# Module-level model singletons (loaded once, reused across requests)
_dense_model: TextEmbedding | None = None
_sparse_model: SparseTextEmbedding | None = None


def _get_dense_model() -> TextEmbedding:
    global _dense_model
    if _dense_model is None:
        settings = get_settings()
        logger.info("Loading dense embedding model: %s", settings.embed_model)
        # A single ONNX thread avoids large arena allocations on small
        # Windows development machines.
        _dense_model = TextEmbedding(settings.embed_model, threads=1)
    return _dense_model


def _get_sparse_model() -> SparseTextEmbedding:
    global _sparse_model
    if _sparse_model is None:
        logger.info("Loading BM25 sparse model")
        _sparse_model = SparseTextEmbedding("Qdrant/bm25", threads=1)
    return _sparse_model


def _get_qdrant_client() -> QdrantClient:
    from pathlib import Path
    settings = get_settings()
    url = settings.qdrant_url.strip() if settings.qdrant_url else ""
    if url and not ("<" in url or "..." in url):
        return QdrantClient(url=url, api_key=settings.qdrant_api_key)
    storage_path = str(Path(__file__).parent.parent.parent / "data" / "qdrant_storage")
    return QdrantClient(path=storage_path)


@dataclass
class RetrievedChunk:
    """A single retrieved chunk with payload and score."""
    id: str
    score: float
    text: str
    source_document: str
    collection: str
    access_roles: list[str]
    section_title: str
    chunk_type: str
    page_number: int | None


def _chunk_fingerprint(chunk: RetrievedChunk) -> str:
    """Return a stable identity for a document passage.

    Qdrant point IDs are deliberately not used here: older ingestion runs used
    random UUIDs, so the same passage can exist under multiple point IDs.
    """
    normalized_text = " ".join(re.sub(r"\s+", " ", chunk.text).split())
    identity = "\x1f".join(
        (
            chunk.collection,
            chunk.source_document,
            chunk.section_title,
            str(chunk.page_number or ""),
            normalized_text,
        )
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def deduplicate_chunks(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """Keep the highest-ranked instance of each identical document passage.

    This protects retrieval from duplicate historical points and ensures the
    reranker and LLM receive diverse evidence rather than repeated context.
    """
    unique: list[RetrievedChunk] = []
    seen: set[str] = set()
    for chunk in chunks:
        fingerprint = _chunk_fingerprint(chunk)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        unique.append(chunk)
    return unique


def _embed_query_dense(query: str) -> list[float]:
    model = _get_dense_model()
    vectors = list(model.embed([query]))
    return vectors[0].tolist()


def _embed_query_sparse(query: str) -> SparseVector:
    model = _get_sparse_model()
    sparse_vecs = list(model.embed([query]))
    sv = sparse_vecs[0]
    return SparseVector(indices=sv.indices.tolist(), values=sv.values.tolist())


def hybrid_search(
    query: str,
    role: str,
    top_k: int | None = None,
) -> list[RetrievedChunk]:
    """Run a hybrid dense+sparse search with RBAC filter.

    Uses Qdrant's native Prefetch + Fusion (RRF) in a single network call.
    The RBAC filter on metadata.collection is applied server-side, before
    any result is returned to this function.

    Args:
        query: Natural language question from the user.
        role:  User's role (extracted from JWT — never from client body).
        top_k: Number of candidates to retrieve (default: settings.retrieval_top_k).

    Returns:
        List of RetrievedChunk objects, sorted by fusion score descending.
    """
    settings = get_settings()
    k = top_k or settings.retrieval_top_k
    collection_name = settings.qdrant_collection

    with logfire_span("retrieval.hybrid_search", role=role, top_k=k, collection=collection_name):
        # Build RBAC filter server-side
        rbac_filter: Filter = build_qdrant_filter(role)

        # Embed query with both models
        with logfire_span("retrieval.embed_query"):
            dense_vec = _embed_query_dense(query)
            sparse_vec = _embed_query_sparse(query)
            logfire_info(
                "Query embedded: dense_dim={dim}, sparse_nonzeros={nonzeros}",
                dim=len(dense_vec),
                nonzeros=len(sparse_vec.indices),
            )

        logfire_info(
            "Executing Qdrant RRF native fusion | role={role} | k={k} | collection={collection}",
            role=role,
            k=k,
            collection=collection_name,
        )

        client = _get_qdrant_client()

        # Single Qdrant query with Prefetch + RRF Fusion (no app-side merge)
        with logfire_span("retrieval.qdrant_query_points"):
            results = client.query_points(
                collection_name=collection_name,
                prefetch=[
                    # Dense branch
                    Prefetch(
                        query=dense_vec,
                        using="dense",
                        filter=rbac_filter,
                        limit=k,
                    ),
                    # Sparse (BM25) branch
                    Prefetch(
                        query=sparse_vec,
                        using="sparse",
                        filter=rbac_filter,
                        limit=k,
                    ),
                ],
                query=FusionQuery(fusion="rrf"),  # Reciprocal Rank Fusion
                limit=k,
                with_payload=True,
            )

        chunks: list[RetrievedChunk] = []
        for point in results.points:
            payload = point.payload or {}
            meta = payload.get("metadata", {})
            chunks.append(
                RetrievedChunk(
                    id=str(point.id),
                    score=point.score,
                    text=payload.get("text") or payload.get("embedded_text") or payload.get("content") or "",
                    source_document=meta.get("source_document", ""),
                    collection=meta.get("collection", ""),
                    access_roles=meta.get("access_roles", []),
                    section_title=meta.get("section_title", ""),
                    chunk_type=meta.get("chunk_type", "text"),
                    page_number=meta.get("page_number") or meta.get("page"),
                )
            )

        unique_chunks = deduplicate_chunks(chunks)
        duplicate_count = len(chunks) - len(unique_chunks)
        if duplicate_count:
            logger.warning(
                "Dropped %d duplicate Qdrant passages before reranking. "
                "Reingest with --recreate to permanently remove legacy duplicates.",
                duplicate_count,
            )

        logfire_info(
            "Hybrid search completed: {count} points returned (top fusion score={top_score:.4f})",
            count=len(unique_chunks),
            top_score=unique_chunks[0].score if unique_chunks else 0.0,
        )
        return unique_chunks
