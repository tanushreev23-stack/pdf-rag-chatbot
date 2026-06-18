from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel
from app.services.rag_chain import build_rag_chain
from app.utils.logger import logger
import time

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/v1", tags=["Chat"])

class QuestionRequest(BaseModel):
    question: str
    session_id: str

@router.post("/ask")
@limiter.limit("10/minute")
async def ask_question(request: Request, body: QuestionRequest):
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    if not body.session_id.strip():
        raise HTTPException(status_code=400, detail="Session ID missing.")
    try:
        logger.info(f"Question | session: {body.session_id} | q: {body.question}")
        start = time.time()
        chain, retriever = build_rag_chain(namespace=body.session_id)
        source_docs = retriever.invoke(body.question)
        answer = chain.invoke(body.question)
        elapsed = round(time.time() - start, 2)
        sources = [
            {
                "page": doc.metadata.get("page"),
                "source": doc.metadata.get("source"),
                "preview": doc.page_content[:100] + "..."
            }
            for doc in source_docs
        ]
        logger.info(f"Answer in {elapsed}s | session: {body.session_id}")
        return {
            "success": True,
            "answer": answer,
            "sources": sources,
            "response_time_seconds": elapsed
        }
    except Exception as e:
        logger.error(f"Question failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get answer: {str(e)}")