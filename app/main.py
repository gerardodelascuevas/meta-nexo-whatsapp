import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request

from app.api.webhook import router as webhook_router
from app.config import Settings, get_settings
from app.services.ollama import OllamaClient
from app.services.rag import InMemoryRAG
from app.services.whatsapp import WhatsAppClient


def create_app(
    settings: Settings | None = None,
    rag_service: Any | None = None,
    whatsapp_client: Any | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    logging.basicConfig(
        level=getattr(logging, resolved_settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    ollama = OllamaClient(
        base_url=resolved_settings.ollama_base_url,
        chat_model=resolved_settings.ollama_chat_model,
        embed_model=resolved_settings.ollama_embed_model,
        timeout_seconds=resolved_settings.ollama_timeout_seconds,
    )
    rag = rag_service or InMemoryRAG(
        ollama=ollama,
        knowledge_path=resolved_settings.knowledge_path,
        top_k=resolved_settings.rag_top_k,
        min_similarity=resolved_settings.rag_min_similarity,
        fallback_message=resolved_settings.fallback_message,
    )
    whatsapp = whatsapp_client or WhatsAppClient(
        access_token=resolved_settings.whatsapp_access_token,
        phone_number_id=resolved_settings.whatsapp_phone_number_id,
        graph_version=resolved_settings.whatsapp_graph_version,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = resolved_settings
        app.state.rag = rag
        app.state.whatsapp = whatsapp
        if not rag.ready:
            logging.getLogger(__name__).info("Creando índice RAG en memoria...")
            await rag.initialize()
            logging.getLogger(__name__).info(
                "Índice RAG listo con %d entradas.", len(rag.entries)
            )
        yield

    api = FastAPI(title=resolved_settings.app_name, version="0.1.0", lifespan=lifespan)
    api.include_router(webhook_router)

    @api.get("/")
    async def root() -> dict[str, str]:
        return {"name": resolved_settings.app_name, "docs": "/docs", "health": "/health"}

    @api.get("/health")
    async def health(request: Request) -> dict[str, Any]:
        current_rag = request.app.state.rag
        return {
            "status": "ok" if current_rag.ready else "starting",
            "knowledge_entries": len(current_rag.entries),
            "chat_model": resolved_settings.ollama_chat_model,
            "embed_model": resolved_settings.ollama_embed_model,
        }

    return api


app = create_app()
