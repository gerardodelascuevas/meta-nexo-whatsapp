from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Nexo IA"
    log_level: str = "INFO"

    whatsapp_verify_token: str = "cambia-este-token"
    whatsapp_access_token: str | None = None
    whatsapp_phone_number_id: str | None = None
    whatsapp_app_secret: str | None = None
    whatsapp_graph_version: str = "v25.0"

    ollama_base_url: str = "http://ollama:11434"
    ollama_chat_model: str = "llama3.2:1b"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_timeout_seconds: float = 120.0

    knowledge_path: Path = Path("/app/knowledge/preguntas_frecuentes.md")
    rag_top_k: int = Field(default=2, ge=1, le=10)
    rag_min_similarity: float = Field(default=0.42, ge=-1.0, le=1.0)
    fallback_message: str = (
        "No encontré esa información en mis preguntas frecuentes. "
        "Puedo ayudarte con horarios, garantía, pagos y cotizaciones."
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
