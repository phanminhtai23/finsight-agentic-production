"""Structure-aware + recursive text splitting with parent-child (small-to-big) linking.

Pure functions / classes — no DB, no LLM — so they are fully unit-testable.
"""

import re

from app.rag.chunking.models import ChunkData, ElementType, ParsedDocument, ParsedElement

_PARAGRAPH_RE = re.compile(r"\n\s*\n")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def _hard_split(text: str, max_chars: int) -> list[str]:
    return [text[i : i + max_chars] for i in range(0, len(text), max_chars)]


def _atomize(text: str, max_chars: int) -> list[str]:
    """Break text into atoms no larger than ``max_chars``, preferring natural boundaries."""
    atoms: list[str] = []
    for para in _PARAGRAPH_RE.split(text):
        para = para.strip()
        if not para:
            continue
        if len(para) <= max_chars:
            atoms.append(para)
            continue
        buf = ""
        for sent in _SENTENCE_RE.split(para):
            sent = sent.strip()
            if not sent:
                continue
            if len(sent) > max_chars:
                if buf:
                    atoms.append(buf)
                    buf = ""
                atoms.extend(_hard_split(sent, max_chars))
            elif not buf:
                buf = sent
            elif len(buf) + len(sent) + 1 <= max_chars:
                buf = f"{buf} {sent}"
            else:
                atoms.append(buf)
                buf = sent
        if buf:
            atoms.append(buf)
    return atoms


def _merge_atoms(atoms: list[str], max_chars: int, overlap: int) -> list[str]:
    """Greedily merge atoms into chunks <= max_chars, carrying a char overlap between them."""
    chunks: list[str] = []
    cur = ""
    for atom in atoms:
        if cur and len(cur) + len(atom) + 1 > max_chars:
            chunks.append(cur)
            tail = cur[-overlap:].lstrip() if overlap > 0 else ""
            cur = f"{tail} {atom}".strip() if tail else atom
        else:
            cur = f"{cur} {atom}".strip() if cur else atom
    if cur:
        chunks.append(cur)
    return chunks


def recursive_split(text: str, max_chars: int = 1000, overlap: int = 150) -> list[str]:
    """Split ``text`` into chunks of at most ``max_chars`` with ``overlap`` characters."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    return _merge_atoms(_atomize(text, max_chars), max_chars, overlap)


def _group_sections(
    elements: list[ParsedElement],
) -> list[tuple[str | None, list[ParsedElement], list[ParsedElement]]]:
    """Group elements into (section_title, text_elements, table_elements) by heading."""
    sections: list[tuple[str | None, list[ParsedElement], list[ParsedElement]]] = []
    title: str | None = None
    texts: list[ParsedElement] = []
    tables: list[ParsedElement] = []

    def flush() -> None:
        if texts or tables:
            sections.append((title, list(texts), list(tables)))

    for el in elements:
        if el.type is ElementType.HEADING:
            flush()
            title = el.text.strip()
            texts, tables = [], []
        elif el.type is ElementType.TABLE:
            tables.append(el)
        else:
            texts.append(el)
    flush()
    return sections


class StructureSplitter:
    """Turn a parsed document into chunks: section-aware, parent-child, table-aware."""

    def __init__(
        self, *, parent_chars: int = 2400, child_chars: int = 800, overlap: int = 120
    ) -> None:
        self.parent_chars = parent_chars
        self.child_chars = child_chars
        self.overlap = overlap

    def split(self, doc: ParsedDocument) -> list[ChunkData]:
        chunks: list[ChunkData] = []

        for title, text_elems, table_elems in _group_sections(doc.elements):
            page = next((e.page for e in text_elems if e.page is not None), None)
            section_text = "\n\n".join(e.text.strip() for e in text_elems if e.text.strip())

            for parent_block in recursive_split(section_text, self.parent_chars, overlap=0):
                parent_id = len(chunks)
                children = recursive_split(parent_block, self.child_chars, self.overlap)
                has_children = len(children) > 1
                chunks.append(
                    ChunkData(
                        content=parent_block,
                        local_id=parent_id,
                        section_title=title,
                        page=page,
                        embed=not has_children,  # parent is context-only when it has children
                    )
                )
                if has_children:
                    for child in children:
                        chunks.append(
                            ChunkData(
                                content=child,
                                local_id=len(chunks),
                                parent_local_id=parent_id,
                                section_title=title,
                                page=page,
                            )
                        )

            for tbl in table_elems:
                chunks.append(
                    ChunkData(
                        content=tbl.text,
                        local_id=len(chunks),
                        section_title=title,
                        page=tbl.page,
                        bbox=tbl.bbox,
                        is_table=True,
                    )
                )

        return chunks
