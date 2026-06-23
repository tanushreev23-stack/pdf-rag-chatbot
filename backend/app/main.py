from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import pdf, chat, sessions
from app.utils.logger import logger
from app.services.database import connect_db, disconnect_db
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="PDF RAG Chatbot",
    description="Upload a PDF and ask questions using AI",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pdf.router)
app.include_router(chat.router)
app.include_router(sessions.router)

@app.get("/")
async def root():
    return {"status": "running", "message": "PDF RAG Chatbot API is live!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    await connect_db()
    logger.info("PDF RAG Chatbot API started!")
    logger.info("Docs at: http://localhost:8000/docs")

@app.on_event("shutdown")
async def shutdown_event():
    await disconnect_db()