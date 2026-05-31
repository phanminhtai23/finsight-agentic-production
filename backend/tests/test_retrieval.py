"""Unit tests for RRF fusion and citation building (pure)."""

from app.rag.retrieval.citation import build_citations, format_sources_block
from app.rag.retrieval.fusion import reciprocal_rank_fusion
from app.rag.retrieval.models import RetrievedChunk


def test_rrf_rewards_items_ranked_high_in_both_lists():
    vector = ["a", "b", "c"]
    keyword = ["b", "a", "d"]
    fused = reciprocal_rank_fusion([vector, keyword])
    ids = [item for item, _ in fused]
    # "a" and "b" appear in both lists near the top → ahead of single-list "c"/"d"
    assert set(ids[:2]) == {"a", "b"}
    assert "c" in ids and "d" in ids


def test_rrf_empty():
    assert reciprocal_rank_fusion([]) == []


def test_build_citations_numbers_and_truncates():
    long = "x" * 500
    chunks = [
        RetrievedChunk(
            chunk_id="1",
            content="Revenue grew 18%.",
            score=0.9,
            document_id="doc1",
            document_title="Q3.pdf",
            page=4,
            cloudinary_url="http://u/4",
        ),
        RetrievedChunk(
            chunk_id="2",
            content=long,
            score=0.5,
            document_id="doc1",
            document_title="Q3.pdf",
            page=7,
        ),
    ]
    cites = build_citations(chunks)
    assert [c.index for c in cites] == [1, 2]
    assert cites[1].snippet.endswith("…")
    assert len(cites[1].snippet) <= 241

    block = format_sources_block(cites)
    assert "[1] Q3.pdf — p.4  http://u/4" in block
    assert "[2] Q3.pdf — p.7" in block
