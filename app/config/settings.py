import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # LLM Settings
    LLM_PROVIDER: str = Field(default="groq", description="groq, ollama, openai, gemini, or mock")
    LLM_MODEL: str = Field(default="openai/gpt-oss-20b", description="Model name")
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", description="Ollama endpoint")
    
    GROQ_API_KEY: Optional[str] = Field(default=None, description="Groq API key")
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API key")
    
    # Vector Database Settings
    CHROMA_PERSIST_DIRECTORY: str = Field(
        default=str(ROOT_DIR / "chroma_db"), 
        description="Directory for persistent ChromaDB storage"
    )
    CHROMA_COLLECTION_NAME: str = Field(
        default="government_schemes", 
        description="Name of the ChromaDB collection"
    )
    DATA_SCHEMES_DIRECTORY: str = Field(
        default=str(ROOT_DIR / "data" / "schemes"),
        description="Directory storing official scheme documents"
    )
    
    # Retrieval Tuning
    MAX_RETRIEVAL_RESULTS: int = Field(default=4, description="Maximum chunks to retrieve")
    SIMILARITY_THRESHOLD: float = Field(default=0.85, description="Max cosine distance threshold")
    
    # Debug / Logging
    DEBUG: bool = Field(default=False)

settings = Settings()
