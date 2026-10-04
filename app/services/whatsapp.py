import hashlib
import hmac
from typing import Any

import httpx


def normalize_whatsapp_recipient(number: str) -> str:
    """Normalize legacy Mexican mobile wa_ids for Cloud API outbound messages."""
    digits = "".join(character for character in number if character.isdigit())
    if digits.startswith("521") and len(digits) == 13:
        return "52" + digits[3:]
    return digits


def verify_meta_signature(body: bytes, signature: str | None, app_secret: str | None) -> bool:
    if not app_secret:
        return True
    if not signature or not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        app_secret.encode("utf-8"), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def extract_text_messages(payload: dict[str, Any]) -> list[dict[str, str]]:
    extracted: list[dict[str, str]] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []) or []:
                text = message.get("text", {}).get("body")
                sender = message.get("from")
                message_id = message.get("id")
                if message.get("type") == "text" and text and sender and message_id:
                    extracted.append(
                        {"from": sender, "text": text.strip(), "id": message_id}
                    )
    return extracted


class WhatsAppClient:
    def __init__(
        self,
        access_token: str | None,
        phone_number_id: str | None,
        graph_version: str,
    ) -> None:
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.graph_version = graph_version

    async def send_text(self, recipient: str, text: str) -> None:
        if not self.access_token or not self.phone_number_id:
            raise RuntimeError(
                "Faltan WHATSAPP_ACCESS_TOKEN o WHATSAPP_PHONE_NUMBER_ID."
            )

        url = (
            f"https://graph.facebook.com/{self.graph_version}/"
            f"{self.phone_number_id}/messages"
        )
        normalized_recipient = normalize_whatsapp_recipient(recipient)
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": normalized_recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text[:4000]},
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.is_error:
                try:
                    error_detail = response.json()
                except ValueError:
                    error_detail = response.text[:2000]
                raise RuntimeError(
                    "Meta rechazó el mensaje "
                    f"(HTTP {response.status_code}): {error_detail}"
                )
