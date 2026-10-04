import asyncio
import sys

from app.config import get_settings
from app.services.ollama import OllamaClient
from app.services.rag import InMemoryRAG


async def main(question: str) -> None:
    settings = get_settings()
    ollama = OllamaClient(
        settings.ollama_base_url,
        settings.ollama_chat_model,
        settings.ollama_embed_model,
        settings.ollama_timeout_seconds,
    )
    rag = InMemoryRAG(
        ollama,
        settings.knowledge_path,
        settings.rag_top_k,
        settings.rag_min_similarity,
        settings.fallback_message,
    )
    await rag.initialize()
    answer = await rag.answer(question)
    print(answer.text)
    print(f"\nFuentes: {', '.join(answer.sources) or 'ninguna'}")
    print(f"Similitud: {answer.best_similarity:.3f}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit('Uso: python scripts/ask.py "¿Cuál es el horario?"')
    asyncio.run(main(" ".join(sys.argv[1:])))
