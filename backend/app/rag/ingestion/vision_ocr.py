"""Gemini Vision OCR — transcribe a page image when a PDF/image has no text layer.

Used by the ingestion parsers for *scanned* documents: the page is rendered to PNG and Gemini
(multimodal) transcribes it, preserving numbers and tables. Higher quality than classic OCR for
Vietnamese financial reports, and uses the same Gemini key the app already has.
"""

import base64
from functools import lru_cache

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential_jitter

from app.core.llm import GeminiTextGenerator, build_chat_model
from app.core.logging import get_logger
from app.core.resilience import is_transient_error

log = get_logger(__name__)

_PROMPT = (
    "You are a precise OCR and document-extraction engine. Transcribe ALL text from this image of "
    "a financial-document page in natural reading order. Preserve the original language. Render any "
    "tables as GitHub-flavored Markdown tables and keep every number EXACTLY as shown (do not round "
    "or reformat). Do not summarize, translate, explain, or add anything that is not in the image. "
    "If the page has no readable text, reply with nothing."
)


@lru_cache
def _model() -> BaseChatModel:
    return build_chat_model(temperature=0.0)


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential_jitter(initial=1.0, max=20.0),
    retry=retry_if_exception(is_transient_error),
    reraise=True,
)
def _invoke(message: HumanMessage) -> object:
    return _model().invoke([message])


def extract_text_from_image(png_bytes: bytes) -> str:
    """Return the text Gemini reads from a page image (empty string if none / on failure)."""
    b64 = base64.b64encode(png_bytes).decode("ascii")
    message = HumanMessage(
        content=[
            {"type": "text", "text": _PROMPT},
            {"type": "image_url", "image_url": f"data:image/png;base64,{b64}"},
        ]
    )
    try:
        resp = _invoke(message)
    except Exception as exc:  # noqa: BLE001 - best effort per page
        log.warning("vision_ocr_failed", error=str(exc))
        return ""
    return GeminiTextGenerator._to_text(resp.content).strip()
