import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://study_user:study_pass@localhost:5432/study_assistant"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    groq_api_key: str = ""
    groq_chat_model: str = "llama-3.3-70b-versatile"
    google_api_key: str = ""
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    n8n_webhook_url: str = "http://localhost:5678/webhook"
    collection_name: str = "document_chunks"
    chunk_size: int = 1000
    chunk_overlap: int = 100
    retrieval_top_k: int = 20

settings = Settings(
    database_url=os.getenv("DATABASE_URL", "postgresql://study_user:study_pass@localhost:5432/study_assistant"),
    qdrant_host=os.getenv("QDRANT_HOST", "localhost"),
    qdrant_port=int(os.getenv("QDRANT_PORT", "6333")),
    groq_api_key=os.getenv("GROQ_API_KEY", ""),
    google_api_key=os.getenv("GOOGLE_API_KEY", ""),
    n8n_webhook_url=os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook"),
)
