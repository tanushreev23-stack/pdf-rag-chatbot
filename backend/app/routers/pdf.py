from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.pdf_processor import extract_documents
from app.services.rag_chain import vector_store
from app.services.database import create_session
from app.utils.logger import logger
import uuid

router = APIRouter(prefix="/api/v1", tags=["PDF"])
BATCH_SIZE = 100

@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files accepted")
    try:
        contents = await file.read()
        if len(contents) > 500 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large. Max 500MB")

        session_id = str(uuid.uuid4())[:8]
        logger.info(f"Upload started | file: {file.filename} | session: {session_id}")

        documents = extract_documents(contents, file.filename)
        if not documents:
            raise HTTPException(status_code=422, detail="Could not extract text from PDF")

        for i in range(0, len(documents), BATCH_SIZE):
            batch = documents[i:i + BATCH_SIZE]
            vector_store.add_documents(batch)
            logger.info(f"Batch {i//BATCH_SIZE + 1} uploaded")

        # Save session to MongoDB
        await create_session(
            session_id=session_id,
            filename=file.filename,
            chunks=len(documents),
            pages=documents[-1].metadata["page"]
        )

        return {
            "success": True,
            "session_id": session_id,
            "filename": file.filename,
            "chunks_stored": len(documents),
            "pages_processed": documents[-1].metadata["page"],
            "message": f"PDF uploaded! {len(documents)} chunks indexed."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")