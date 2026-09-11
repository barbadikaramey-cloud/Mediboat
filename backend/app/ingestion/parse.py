"""Document parsing and chunking using Docling + HybridChunker.

Each chunk produced carries full metadata:
  source_document, collection, access_roles, section_title, chunk_type

The embedded text prepends the parent section heading to every paragraph/table
chunk so the LLM has structural context even when only top-3 are passed.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.transforms.chunker.base import BaseChunk

from app.config import get_settings
from app.rbac import ROLE_COLLECTIONS

logger = logging.getLogger(__name__)

# ── Collection → access_roles map (inverse of ROLE_COLLECTIONS) ────────────────
COLLECTION_ACCESS_ROLES: dict[str, list[str]] = {}
for role, collections in ROLE_COLLECTIONS.items():
    for col in collections:
        COLLECTION_ACCESS_ROLES.setdefault(col, [])
        if role not in COLLECTION_ACCESS_ROLES[col]:
            COLLECTION_ACCESS_ROLES[col].append(role)


@dataclass
class ParsedChunk:
    """A single chunk ready for embedding and upsert."""
    text: str                        # heading-prefixed text sent to embedder
    raw_text: str                    # clean text without heading prefix
    source_document: str             # filename (no path)
    collection: str                  # e.g. "clinical"
    access_roles: list[str]          # roles allowed to see this chunk
    section_title: str               # nearest parent heading
    chunk_type: str                  # text | table | heading | code
    page_number: int | None = None


def _infer_chunk_type(chunk: BaseChunk) -> str:
    """Heuristically determine chunk type from Docling metadata."""
    meta = getattr(chunk, "meta", None)
    if meta is None:
        return "text"
    # Docling sets doc_items with labels
    doc_items = getattr(meta, "doc_items", [])
    for item in doc_items:
        label = str(getattr(item, "label", "")).lower()
        if "table" in label:
            return "table"
        if "heading" in label or "title" in label:
            return "heading"
        if "code" in label:
            return "code"
    return "text"


def _get_section_title(chunk: BaseChunk) -> str:
    """Extract the closest heading from chunk metadata."""
    meta = getattr(chunk, "meta", None)
    if meta is None:
        return ""
    headings = getattr(meta, "headings", None)
    if headings:
        return headings[-1] if isinstance(headings, list) else str(headings)
    return ""


def _get_page_number(chunk: BaseChunk) -> int | None:
    """Extract page number if available."""
    meta = getattr(chunk, "meta", None)
    if meta is None:
        return None
    doc_items = getattr(meta, "doc_items", [])
    for item in doc_items:
        prov = getattr(item, "prov", [])
        if prov:
            return getattr(prov[0], "page_no", None)
    return None


def parse_document(file_path: Path, collection: str) -> list[ParsedChunk]:
    """Parse a single PDF or Markdown file and return a list of ParsedChunks.

    Steps:
      1. Docling converts the file to a structured Document object
      2. HybridChunker splits by section/paragraph/table boundaries first,
         then applies a token-size limit as a second pass
      3. Each chunk gets heading-prefixed text + full metadata
    """
    settings = get_settings()
    logger.info("Parsing %s (collection=%s)", file_path.name, collection)

    # ── 1. Docling conversion ──────────────────────────────────────────────────
    pipeline_opts = PdfPipelineOptions(do_table_structure=True)
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_opts)
        }
    )
    result = converter.convert(str(file_path))
    doc = result.document

    # ── 2. HybridChunker ──────────────────────────────────────────────────────
    chunker = HybridChunker(
        tokenizer="BAAI/bge-small-en-v1.5",   # same tokenizer as embedder
        max_tokens=settings.chunk_token_limit,
        merge_peers=True,                       # merge short adjacent peers
    )
    chunks = list(chunker.chunk(doc))

    # ── 3. Build ParsedChunk objects ──────────────────────────────────────────
    access_roles = COLLECTION_ACCESS_ROLES.get(collection, [])
    parsed: list[ParsedChunk] = []

    for chunk in chunks:
        raw_text = chunk.text.strip()
        if not raw_text:
            continue

        section_title = _get_section_title(chunk)
        chunk_type = _infer_chunk_type(chunk)
        page_no = _get_page_number(chunk)

        # Prefix with section heading for richer embedding context
        if section_title and not raw_text.startswith(section_title):
            embedded_text = f"{section_title}\n\n{raw_text}"
        else:
            embedded_text = raw_text

        parsed.append(ParsedChunk(
            text=embedded_text,
            raw_text=raw_text,
            source_document=file_path.name,
            collection=collection,
            access_roles=access_roles,
            section_title=section_title,
            chunk_type=chunk_type,
            page_number=page_no,
        ))

    logger.info("  -> %d chunks from %s", len(parsed), file_path.name)
    return parsed


def parse_collection_dir(docs_dir: Path) -> dict[str, list[ParsedChunk]]:
    """Walk docs_dir/<collection>/ subdirectories and parse all documents.

    Returns: {collection_name: [ParsedChunk, ...]}
    """
    all_chunks: dict[str, list[ParsedChunk]] = {}
    supported = {".pdf", ".md", ".markdown", ".txt"}

    for collection_dir in sorted(docs_dir.iterdir()):
        if not collection_dir.is_dir():
            continue
        collection = collection_dir.name
        chunks: list[ParsedChunk] = []
        for fp in sorted(collection_dir.iterdir()):
            if fp.suffix.lower() not in supported:
                continue
            try:
                chunks.extend(parse_document(fp, collection))
            except Exception as exc:
                logger.error("Failed to parse %s: %s", fp.name, exc, exc_info=True)
        if chunks:
            all_chunks[collection] = chunks

    return all_chunks
