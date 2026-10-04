import tempfile
import unittest
from pathlib import Path

from app.services.rag import cosine_similarity, load_markdown_entries, meaningful_tokens


class RAGTests(unittest.TestCase):
    def test_load_markdown_entries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            knowledge = Path(directory) / "faq.md"
            knowledge.write_text(
                "# FAQ\n\n## Horario\n\nAbrimos a las ocho.\n\n"
                "## Pago\n\nAceptamos tarjeta.\n",
                encoding="utf-8",
            )

            entries = load_markdown_entries(knowledge)

        self.assertEqual([entry.title for entry in entries], ["Horario", "Pago"])
        self.assertEqual(entries[0].content, "Abrimos a las ocho.")

    def test_cosine_similarity(self) -> None:
        self.assertAlmostEqual(cosine_similarity([1.0, 0.0], [1.0, 0.0]), 1.0)
        self.assertAlmostEqual(cosine_similarity([1.0, 0.0], [0.0, 1.0]), 0.0)

    def test_meaningful_tokens_normalizes_accents(self) -> None:
        self.assertEqual(meaningful_tokens("¿Qué garantía ofrecen?"), {"garantia"})


if __name__ == "__main__":
    unittest.main()
