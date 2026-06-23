from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.utils.logger import logger
import datetime

client = None
db = None

async def connect_db():
    global client, db
    try:
        client = AsyncIOMotorClient(settings.mongodb_uri)
        db = client[settings.mongodb_db]
        await client.admin.command('ping')
        logger.info("✅ MongoDB connected successfully!")
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        raise

async def disconnect_db():
    global client
    if client:
        client.close()
        logger.info("MongoDB disconnected")

def get_db():
    return db

# ─── SESSIONS ───────────────────────────

async def create_session(session_id: str, filename: str, chunks: int, pages: int):
    collection = db["sessions"]
    await collection.insert_one({
        "session_id": session_id,
        "filename": filename,
        "chunks_stored": chunks,
        "pages_processed": pages,
        "created_at": datetime.datetime.utcnow(),
        "message_count": 0
    })
    logger.info(f"Session saved to MongoDB: {session_id}")

async def get_session(session_id: str):
    collection = db["sessions"]
    return await collection.find_one({"session_id": session_id})

async def get_all_sessions():
    collection = db["sessions"]
    cursor = collection.find({}).sort("created_at", -1)
    sessions = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        sessions.append(doc)
    return sessions

async def delete_session_db(session_id: str):
    await db["sessions"].delete_one({"session_id": session_id})
    await db["messages"].delete_many({"session_id": session_id})
    logger.info(f"Session deleted from MongoDB: {session_id}")

# ─── MESSAGES ───────────────────────────

async def save_message(session_id: str, role: str, content: str, sources: list = []):
    collection = db["messages"]
    await collection.insert_one({
        "session_id": session_id,
        "role": role,
        "content": content,
        "sources": sources,
        "timestamp": datetime.datetime.utcnow(),
        "time": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    })
    await db["sessions"].update_one(
        {"session_id": session_id},
        {"$inc": {"message_count": 1}}
    )

async def get_messages(session_id: str):
    collection = db["messages"]
    cursor = collection.find(
        {"session_id": session_id}
    ).sort("timestamp", 1)
    messages = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        messages.append(doc)
    return messages