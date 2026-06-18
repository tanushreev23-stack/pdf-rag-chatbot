from pydantic_settings import BaseSettings
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent.parent / ".env"

class Settings(BaseSettings):
    pinecone_api_key: str
    groq_api_key: str
    pinecone_index_name: str = "pdf-chatbot"
    app_env: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = str(env_path)

settings = Settings()