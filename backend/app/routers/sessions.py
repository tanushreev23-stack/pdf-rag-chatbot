from fastapi import APIRouter, HTTPException
from app.services.database import get_all_sessions, get_session, delete_session_db
from app.utils.logger import logger

router = APIRouter(prefix="/api/v1", tags=["Sessions"])

@router.get("/sessions")
async def list_sessions():
    sessions = await get_all_sessions()
    return {"sessions": sessions}

@router.get("/sessions/{session_id}")
async def get_one_session(session_id: str):
    session = await get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session["_id"] = str(session["_id"])
    return session

@router.delete("/sessions/{session_id}")
async def remove_session(session_id: str):
    await delete_session_db(session_id)
    logger.info(f"Session deleted: {session_id}")
    return {"success": True, "message": "Session deleted"}