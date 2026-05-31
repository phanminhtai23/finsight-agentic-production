"""Document parsers: PDF, DOCX, and scanned images (OCR).

Each parser implements the ``DocumentParser`` protocol and is chosen by file extension via
``ParserRegistry`` — adding a new format means adding a parser, not editing existing code
(Open/Closed principle). Parsing produces located ``ParsedElement``s (text/heading/table with
page + bbox) that feed the chunking pipeline.
"""

from __future__ import annotations

import io
import os
import statistics
from pathlib import Path
from typing import Protocol

from app.rag.chunking.models import ElementType, ParsedDocument, ParsedElement

# Tesseract languages for OCR. Vietnamese first (financial reports are often scanned VN PDFs);
# install the language data in the image (tesseract-ocr-vie). Falls back to English if missing.
_OCR_LANG = os.getenv("OCR_LANGUAGES", "vie+eng")


class ParserError(RuntimeError):
    pass


def _ocr_image(img) -> str:  # noqa: ANN001
    """Run Tesseract on a PIL image, falling back to English if the configured language data
    isn't installed."""
    import pytesseract

    try:
        return pytesseract.image_to_string(img, lang=_OCR_LANG).strip()
    except pytesseract.TesseractError:
        return pytesseract.image_to_string(img).strip()  # default language only


class DocumentParser(Protocol):
    extensions: tuple[str, ...]

    def parse(self, path: str, *, title: str) -> ParsedDocument: ...


def _bbox(coords) -> dict | None:  # noqa: ANN001
    if not coords:
        return None
    x0, y0, x1, y1 = coords
    return {"x0": float(x0), "y0": float(y0), "x1": float(x1), "y1": float(y1)}


def _rows_to_markdown(rows: list[list]) -> str:
    cleaned = [[("" if c is None else str(c)).strip() for c in row] for row in rows if row]
    if not cleaned:
        return ""
    width = max(len(r) for r in cleaned)
    cleaned = [r + [""] * (width - len(r)) for r in cleaned]
    header = "| " + " | ".join(cleaned[0]) + " |"
    sep = "| " + " | ".join("---" for _ in range(width)) + " |"
    body = ["| " + " | ".join(r) + " |" for r in cleaned[1:]]
    return "\n".join([header, sep, *body])


class PdfParser:
    extensions = (".pdf",)

    def parse(self, path: str, *, title: str) -> ParsedDocument:
        import fitz  # PyMuPDF

        elements: list[ParsedElement] = []
        doc = fitz.open(path)
        try:
            for page_no, page in enumerate(doc, start=1):
                blocks = self._page_blocks(page, page_no)
                # Scanned page (no embedded text) → render it and OCR.
                if not blocks:
                    ocr = self._ocr_page(page, page_no)
                    if ocr is not None:
                        blocks = [ocr]
                elements.extend(blocks)
            page_count = doc.page_count
        finally:
            doc.close()

        elements.extend(self._tables(path))
        return ParsedDocument(
            title=title, file_type="pdf", elements=elements, page_count=page_count
        )

    @staticmethod
    def _ocr_page(page, page_no: int) -> ParsedElement | None:  # noqa: ANN001
        """OCR a page image when it has no extractable text layer (scanned PDF)."""
        try:
            from PIL import Image

            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text = _ocr_image(img)
        except Exception:  # noqa: BLE001 - OCR is best-effort per page
            return None
        if not text:
            return None
        return ParsedElement(text=text, type=ElementType.TEXT, page=page_no)

    @staticmethod
    def _page_blocks(page, page_no: int) -> list[ParsedElement]:  # noqa: ANN001
        data = page.get_text("dict")
        spans = [
            span
            for block in data.get("blocks", [])
            for line in block.get("lines", [])
            for span in line.get("spans", [])
        ]
        sizes = [s["size"] for s in spans if s.get("text", "").strip()]
        median = statistics.median(sizes) if sizes else 0.0

        out: list[ParsedElement] = []
        for block in data.get("blocks", []):
            lines = block.get("lines", [])
            if not lines:
                continue
            text = " ".join(span["text"] for line in lines for span in line["spans"]).strip()
            if not text:
                continue
            block_size = max(
                (span["size"] for line in lines for span in line["spans"]), default=median
            )
            is_heading = median and block_size > median * 1.25 and len(text) < 80
            out.append(
                ParsedElement(
                    text=text,
                    type=ElementType.HEADING if is_heading else ElementType.TEXT,
                    page=page_no,
                    bbox=_bbox(block.get("bbox")),
                )
            )
        return out

    @staticmethod
    def _tables(path: str) -> list[ParsedElement]:
        try:
            import pdfplumber
        except ImportError:  # pragma: no cover
            return []
        out: list[ParsedElement] = []
        try:
            with pdfplumber.open(path) as pdf:
                for page_no, page in enumerate(pdf.pages, start=1):
                    for table in page.find_tables():
                        markdown = _rows_to_markdown(table.extract())
                        if markdown:
                            out.append(
                                ParsedElement(
                                    text=markdown,
                                    type=ElementType.TABLE,
                                    page=page_no,
                                    bbox=_bbox(table.bbox),
                                )
                            )
        except Exception:  # noqa: BLE001 - table extraction is best-effort
            return out
        return out


class DocxParser:
    extensions = (".docx",)

    def parse(self, path: str, *, title: str) -> ParsedDocument:
        import docx

        document = docx.Document(path)
        elements: list[ParsedElement] = []
        for para in document.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            style = (para.style.name or "").lower() if para.style else ""
            etype = ElementType.HEADING if style.startswith("heading") else ElementType.TEXT
            elements.append(ParsedElement(text=text, type=etype, page=None))

        for table in document.tables:
            rows = [[cell.text for cell in row.cells] for row in table.rows]
            markdown = _rows_to_markdown(rows)
            if markdown:
                elements.append(ParsedElement(text=markdown, type=ElementType.TABLE, page=None))

        return ParsedDocument(title=title, file_type="docx", elements=elements)


class ImageParser:
    extensions = (".png", ".jpg", ".jpeg", ".tiff", ".bmp")

    def parse(self, path: str, *, title: str) -> ParsedDocument:
        try:
            from PIL import Image
        except ImportError as exc:  # pragma: no cover
            raise ParserError("OCR dependencies not available") from exc
        try:
            text = _ocr_image(Image.open(path))
        except Exception as exc:  # noqa: BLE001
            raise ParserError(
                "OCR failed — is the Tesseract binary installed and on PATH?"
            ) from exc
        elements = [ParsedElement(text=text, type=ElementType.TEXT, page=1)] if text else []
        return ParsedDocument(title=title, file_type="image", elements=elements, page_count=1)


class ParserRegistry:
    def __init__(self, parsers: list[DocumentParser] | None = None) -> None:
        self._parsers = parsers or [PdfParser(), DocxParser(), ImageParser()]

    def for_extension(self, ext: str) -> DocumentParser:
        ext = ext.lower()
        for parser in self._parsers:
            if ext in parser.extensions:
                return parser
        raise ParserError(f"Unsupported file type: {ext}")

    def parse(self, path: str, *, title: str | None = None) -> ParsedDocument:
        ext = Path(path).suffix
        return self.for_extension(ext).parse(path, title=title or Path(path).name)
