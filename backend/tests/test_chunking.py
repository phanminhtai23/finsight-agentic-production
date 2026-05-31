"""Unit tests for the chunking logic (pure, no DB/LLM)."""

from app.rag.chunking.models import ElementType, ParsedDocument, ParsedElement
from app.rag.chunking.splitter import StructureSplitter, recursive_split


def test_recursive_split_respects_max_chars_no_overlap():
    text = ". ".join(f"sentence number {i}" for i in range(200))
    chunks = recursive_split(text, max_chars=100, overlap=0)
    assert len(chunks) > 1
    assert all(len(c) <= 100 for c in chunks)


def test_recursive_split_short_text_single_chunk():
    assert recursive_split("a short text", max_chars=100) == ["a short text"]


def test_recursive_split_overlap_carries_context():
    text = ". ".join(f"unique_token_{i} filler words here" for i in range(50))
    chunks = recursive_split(text, max_chars=120, overlap=40)
    assert len(chunks) > 2


def _doc() -> ParsedDocument:
    long_text = " ".join(f"Revenue line {i} grew strongly this period." for i in range(120))
    return ParsedDocument(
        title="Q3 Report",
        file_type="pdf",
        elements=[
            ParsedElement("Income Statement", ElementType.HEADING, page=1),
            ParsedElement(long_text, ElementType.TEXT, page=1),
            ParsedElement("| Metric | Value |\n| Revenue | 1250 |", ElementType.TABLE, page=2),
        ],
    )


def test_structure_splitter_parent_child_and_table():
    chunks = StructureSplitter(parent_chars=600, child_chars=200, overlap=40).split(_doc())

    parents = [c for c in chunks if c.parent_local_id is None and not c.is_table]
    children = [c for c in chunks if c.parent_local_id is not None]
    tables = [c for c in chunks if c.is_table]

    assert parents and children and tables
    # children point at a real parent
    parent_ids = {c.local_id for c in parents}
    assert all(c.parent_local_id in parent_ids for c in children)
    # a parent that has children is context-only (not embedded)
    parents_with_children = {c.parent_local_id for c in children}
    assert all(not c.embed for c in parents if c.local_id in parents_with_children)
    # tables are embedded standalone with their page metadata
    assert all(t.embed and t.page == 2 for t in tables)
    # section title propagated
    assert all(c.section_title == "Income Statement" for c in chunks)
