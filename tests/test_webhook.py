import unittest
from dataclasses import dataclass

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.rag import RAGAnswer
from app.services.whatsapp import extract_text_messages, normalize_whatsapp_recipient


class FakeRAG:
    ready = True
    entries = [object()]

    async def answer(self, question: str) -> RAGAnswer:
        return RAGAnswer(text=f"Respuesta: {question}", sources=("FAQ",), best_similarity=0.9)


@dataclass
class FakeWhatsApp:
    sent: list[tuple[str, str]]

    async def send_text(self, recipient: str, text: str) -> None:
        self.sent.append((recipient, text))


def make_client() -> tuple[TestClient, FakeWhatsApp]:
    settings = Settings(
        whatsapp_verify_token="token-prueba",
        whatsapp_app_secret=None,
    )
    whatsapp = FakeWhatsApp(sent=[])
    app = create_app(settings=settings, rag_service=FakeRAG(), whatsapp_client=whatsapp)
    return TestClient(app), whatsapp


class WebhookTests(unittest.TestCase):
    def test_verify_webhook(self) -> None:
        client, _ = make_client()
        with client:
            response = client.get(
                "/webhook",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": "token-prueba",
                    "hub.challenge": "12345",
                },
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "12345")

    def test_receive_text_message(self) -> None:
        client, whatsapp = make_client()
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "id": "wamid.unique-test",
                                        "from": "5215555555555",
                                        "type": "text",
                                        "text": {"body": "¿Cuál es el horario?"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        with client:
            response = client.post("/webhook", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            whatsapp.sent,
            [("5215555555555", "Respuesta: ¿Cuál es el horario?")],
        )

    def test_extract_text_messages_ignores_status_updates(self) -> None:
        payload = {"entry": [{"changes": [{"value": {"statuses": []}}]}]}
        self.assertEqual(extract_text_messages(payload), [])

    def test_normalize_legacy_mexican_mobile_number(self) -> None:
        self.assertEqual(
            normalize_whatsapp_recipient("5212224404412"),
            "522224404412",
        )

    def test_normalize_recipient_preserves_other_numbers(self) -> None:
        self.assertEqual(
            normalize_whatsapp_recipient("+1 (555) 163-6184"),
            "15551636184",
        )


if __name__ == "__main__":
    unittest.main()
