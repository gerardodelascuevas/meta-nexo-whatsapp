import json
import logging
import time
from collections import OrderedDict
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response

from app.services.whatsapp import extract_text_messages, verify_meta_signature


logger = logging.getLogger(__name__)
router = APIRouter()


class MessageDeduplicator:
    def __init__(self, ttl_seconds: int = 3600, max_items: int = 5000) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_items = max_items
        self._seen: OrderedDict[str, float] = OrderedDict()

    def claim(self, message_id: str) -> bool:
        now = time.monotonic()
        while self._seen:
            _, oldest = next(iter(self._seen.items()))
            if now - oldest <= self.ttl_seconds:
                break
            self._seen.popitem(last=False)

        if message_id in self._seen:
            return False
        self._seen[message_id] = now
        while len(self._seen) > self.max_items:
            self._seen.popitem(last=False)
        return True


deduplicator = MessageDeduplicator()


@router.get("/webhook")
async def verify_webhook(request: Request) -> Response:
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    expected_token = request.app.state.settings.whatsapp_verify_token

    if mode == "subscribe" and token == expected_token and challenge:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="No se pudo verificar el webhook.")


@router.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks) -> dict[str, str]:
    body = await request.body()
    settings = request.app.state.settings
    if not verify_meta_signature(
        body,
        request.headers.get("x-hub-signature-256"),
        settings.whatsapp_app_secret,
    ):
        raise HTTPException(status_code=401, detail="Firma de Meta inválida.")

    try:
        payload: dict[str, Any] = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="JSON inválido.") from exc

    for message in extract_text_messages(payload):
        if deduplicator.claim(message["id"]):
            background_tasks.add_task(
                process_message,
                request.app,
                message["from"],
                message["text"],
                message["id"],
            )
    return {"status": "accepted"}


async def process_message(app: Any, sender: str, text: str, message_id: str) -> None:
    try:
        answer = await app.state.rag.answer(text)
        logger.info(
            "Respuesta generada message_id=%s similarity=%.3f sources=%s",
            message_id,
            answer.best_similarity,
            list(answer.sources),
        )
        await app.state.whatsapp.send_text(sender, answer.text)
    except Exception:
        logger.exception("No se pudo procesar message_id=%s", message_id)
