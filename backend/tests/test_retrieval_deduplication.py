from app.retrieval.hybrid_search import RetrievedChunk, deduplicate_chunks
from app.ingestion.ingest import _point_id
from app.ingestion.parse import ParsedChunk


def _chunk(id: str, score: float, text: str = "Clinical passage") -> RetrievedChunk:
    return RetrievedChunk(
        id=id,
        score=score,
        text=text,
        source_document="protocol.pdf",
        collection="clinical",
        access_roles=["doctor"],
        section_title="Treatment",
        chunk_type="text",
        page_number=9,
    )


def test_deduplicate_chunks_keeps_highest_ranked_historical_copy() -> None:
    first = _chunk("newer-id", 0.9)
    legacy_copy = _chunk("older-id", 0.8)
    distinct = _chunk("distinct-id", 0.7, "A different clinical passage")

    result = deduplicate_chunks([first, legacy_copy, distinct])

    assert [chunk.id for chunk in result] == ["newer-id", "distinct-id"]


def test_deduplicate_chunks_keeps_same_text_from_different_pages() -> None:
    page_nine = _chunk("page-nine", 0.9)
    page_ten = _chunk("page-ten", 0.8)
    page_ten.page_number = 10

    assert [chunk.id for chunk in deduplicate_chunks([page_nine, page_ten])] == [
        "page-nine",
        "page-ten",
    ]


def test_ingestion_point_id_is_stable_for_an_unchanged_chunk() -> None:
    chunk = ParsedChunk(
        text="Treatment\n\nClinical passage",
        raw_text="Clinical passage",
        source_document="protocol.pdf",
        collection="clinical",
        access_roles=["doctor"],
        section_title="Treatment",
        chunk_type="text",
        page_number=9,
    )

    assert _point_id(chunk) == _point_id(chunk)
