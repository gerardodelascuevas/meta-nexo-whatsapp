from typing import Any

import httpx


class OllamaClient:
    def __init__(
        self,
        base_url: str,
        chat_model: str,
        embed_model: str,
        timeout_seconds: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.chat_model = chat_model
        self.embed_model = embed_model
        self.timeout = httpx.Timeout(timeout_seconds, connect=10.0)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        payload = {"model": self.embed_model, "input": texts}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/api/embed", json=payload)
            response.raise_for_status()

        embeddings = response.json().get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise RuntimeError("Ollama devolvió embeddings incompletos.")
        return embeddings

    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        payload: dict[str, Any] = {
            "model": self.chat_model,
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {"temperature": 0.1},
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()

        content = response.json().get("message", {}).get("content", "").strip()
        if not content:
            raise RuntimeError("Ollama devolvió una respuesta vacía.")
        return content
