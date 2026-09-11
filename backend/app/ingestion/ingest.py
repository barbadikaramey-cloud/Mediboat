"""Embed + upsert parsed chunks to Qdrant with dense + sparse vectors.

Run once (offline) before starting the backend:
    uv run python -m app.ingestion.ingest

Architecture:
  - Dense vectors  : FastEmbed BAAI/bge-small-en-v1.5 (384-dim)
  - Sparse vectors : FastEmbed Qdrant/bm25 (native Qdrant sparse format)
  - Single Qdrant query fuses both via RRF — no two-query app-side merge

Collection schema uses named vectors:
  "dense"  → VectorParams(size=384, distance=Cosine)
  "sparse" → SparseVectorParams()
"""
from __future__ import annotations

import logging
import argparse
import hashlib
import uuid
from pathlib import Path
from typing import Any

from fastembed import TextEmbedding, SparseTextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    PointStruct,
    SparseVector,
    SparseVectorParams,
    PayloadSchemaType,
    VectorParams,
    VectorsConfig,
)

from app.config import get_settings
from app.ingestion.parse import ParsedChunk, parse_collection_dir

logger = logging.getLogger(__name__)

DENSE_MODEL = "BAAI/bge-small-en-v1.5"
SPARSE_MODEL = "Qdrant/bm25"
DENSE_DIM = 384
BATCH_SIZE = 8  # keep ONNX memory use low on local machines
_POINT_ID_NAMESPACE = uuid.UUID("c0133b6c-18e5-4b83-a2d7-2aef2b1e0649")


def _point_id(chunk: ParsedChunk) -> str:
    """Create a repeatable ID so re-ingesting unchanged content is an upsert."""
    content_hash = hashlib.sha256(chunk.raw_text.encode("utf-8")).hexdigest()
    identity = "\x1f".join(
        (
            chunk.collection,
            chunk.source_document,
            chunk.section_title,
            str(chunk.page_number or ""),
            chunk.chunk_type,
            content_hash,
        )
    )
    return str(uuid.uuid5(_POINT_ID_NAMESPACE, identity))


# ── Qdrant client (module-level singleton) ─────────────────────────────────────
def _get_client() -> QdrantClient:
    settings = get_settings()
    url = settings.qdrant_url.strip() if settings.qdrant_url else ""
    if url and not ("<" in url or "..." in url):
        return QdrantClient(url=url, api_key=settings.qdrant_api_key)
    # Local persistent fallback on disk when cloud url not configured
    storage_path = str(Path(__file__).parent.parent.parent / "data" / "qdrant_storage")
    return QdrantClient(path=storage_path)


# ── Collection setup ───────────────────────────────────────────────────────────
def ensure_collection(client: QdrantClient, collection_name: str) -> None:
    """Create Qdrant collection with named dense + sparse vectors if it doesn't exist."""
    existing = {c.name for c in client.get_collections().collections}
    if collection_name not in existing:
        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "dense": VectorParams(size=DENSE_DIM, distance=Distance.COSINE),
            },
            sparse_vectors_config={
                "sparse": SparseVectorParams(),
            },
        )
        logger.info("Created collection '%s'", collection_name)
    else:
        logger.info("Collection '%s' already exists", collection_name)

    for field in ("metadata.collection", "metadata.access_roles"):
        try:
            client.create_payload_index(
                collection_name=collection_name,
                field_name=field,
                field_schema=PayloadSchemaType.KEYWORD,
                wait=True,
            )
            logger.info("Ensured keyword payload index: %s", field)
        except Exception as exc:
            if "already exists" not in str(exc).lower():
                raise


# ── Batched embedding helpers ──────────────────────────────────────────────────
def _batch(lst: list, size: int):
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


def embed_and_upsert(
    client: QdrantClient,
    collection_name: str,
    chunks: list[ParsedChunk],
) -> None:
    """Compute dense + sparse vectors and upsert to Qdrant in batches."""
    dense_model = TextEmbedding(DENSE_MODEL, threads=1)
    sparse_model = SparseTextEmbedding(SPARSE_MODEL, threads=1)

    texts = [c.text for c in chunks]
    logger.info("Embedding %d chunks (batch_size=%d)…", len(chunks), BATCH_SIZE)

    total_upserted = 0
    for batch_chunks in _batch(chunks, BATCH_SIZE):
        batch_texts = [c.text for c in batch_chunks]

        # Dense embeddings
        dense_vecs = list(dense_model.embed(batch_texts))

        # Sparse embeddings (returns SparseEmbedding objects)
        sparse_vecs = list(sparse_model.embed(batch_texts))

        points: list[PointStruct] = []
        for chunk, dvec, svec in zip(batch_chunks, dense_vecs, sparse_vecs):
            point_id = _point_id(chunk)
            payload: dict[str, Any] = {
                "metadata": {
                    "source_document": chunk.source_document,
                    "collection": chunk.collection,
                    "access_roles": chunk.access_roles,
                    "section_title": chunk.section_title,
                    "chunk_type": chunk.chunk_type,
                    "page_number": chunk.page_number,
                },
                "text": chunk.raw_text,       # stored for reranker + citation
                "embedded_text": chunk.text,  # heading-prefixed version
            }

            points.append(
                PointStruct(
                    id=point_id,
                    vector={
                        "dense": dvec.tolist(),
                        "sparse": SparseVector(
                            indices=svec.indices.tolist(),
                            values=svec.values.tolist(),
                        ),
                    },
                    payload=payload,
                )
            )

        client.upsert(collection_name=collection_name, points=points, wait=True)
        total_upserted += len(points)
        logger.info("  Upserted %d / %d points", total_upserted, len(chunks))

    logger.info("Done. Total upserted: %d", total_upserted)


# ── Main entry point ───────────────────────────────────────────────────────────
def main() -> None:
    """Parse all documents and upsert to Qdrant. Run once before starting backend."""
    import sys
    parser = argparse.ArgumentParser(description="Ingest MediBot documents into Qdrant.")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete and rebuild the configured collection before ingesting.",
    )
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )

    settings = get_settings()
    collection_name = settings.qdrant_collection

    docs_dir = Path(__file__).parent.parent.parent / "data" / "docs"
    if not docs_dir.exists():
        logger.error("docs_dir not found: %s", docs_dir)
        sys.exit(1)

    client = _get_client()
    if args.recreate:
        existing = {c.name for c in client.get_collections().collections}
        if collection_name in existing:
            logger.warning("Deleting collection '%s' before full rebuild", collection_name)
            client.delete_collection(collection_name=collection_name)
    ensure_collection(client, collection_name)

    logger.info("Parsing documents from %s", docs_dir)
    all_chunks = parse_collection_dir(docs_dir)

    total = sum(len(v) for v in all_chunks.values())
    logger.info("Parsed %d total chunks across %d collections", total, len(all_chunks))

    flat_chunks = [chunk for chunks in all_chunks.values() for chunk in chunks]
    embed_and_upsert(client, collection_name, flat_chunks)

    # Verification
    info = client.get_collection(collection_name)
    logger.info(
        "Ingestion complete. Collection '%s' has %d points.",
        collection_name,
        info.points_count,
    )
    logger.info(
        "\nBreakdown by collection:"
    )
    for col, chunks in sorted(all_chunks.items()):
        logger.info("  %-20s %d chunks", col, len(chunks))


if __name__ == "__main__":
    main()
