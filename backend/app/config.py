from pydantic_settings import BaseSettings
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent.parent / ".env"

class Settings(BaseSettings):
    pinecone_api_key: str
    groq_api_key: str
    pinecone_index_name: str = "pdf-chatbot"
    app_env: str = "development"
    log_level: str = "INFO"
    mongodb_uri: str
    mongodb_db: str = "pdf_chatbot"

    class Config:
        env_file = str(env_path)
        extra = "ignore"          # ← this line ignores extra params like appName

settings = Settings()