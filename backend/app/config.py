"""Application configuration.

All settings are driven by environment variables so the embedding model,
vector store, and LLM can be swapped independently (BRD NFR: Maintainability).
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM (Groq, BRD section 15)
    groq_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"

    # Embeddings (BRD section 15)
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    # Vector store (BRD section 15)
    vector_store: str = "faiss"

    # Retrieval (BRD FR-07)
    top_k: int = 5
    similarity_threshold: float = 0.45

    # Chunking (BRD section 12.2)
    chunk_size: int = 512
    chunk_overlap: int = 64

    # Limits (BRD NFR: Scalability)
    max_resume_pages: int = 5
    max_jd_words: int = 1500

    # Privacy (BRD NFR: Security / Privacy)
    persist_session_data: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
