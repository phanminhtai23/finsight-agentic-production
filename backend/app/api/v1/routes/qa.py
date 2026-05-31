"""RAG question-answering endpoint."""

from fastapi import APIRouter

from app.api.deps import QAServiceDep
from app.schemas.qa import AnswerOut, AskRequest, CitationOut

router = APIRouter()


@router.post("/ask", response_model=AnswerOut)
async def ask(body: AskRequest, qa: QAServiceDep) -> AnswerOut:
    """Answer a question from indexed documents, with inline citations."""
    result = await qa.answer(body.question, document_ids=body.document_ids)
    return AnswerOut(
        answer=result.answer,
        citations=[CitationOut(**c.to_dict()) for c in result.citations],
    )
