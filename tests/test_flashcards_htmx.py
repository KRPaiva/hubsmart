from sqlalchemy import select

from app.models.study import FlashcardDeck, StudyToolLink
from tests.support import DatabaseTestCase


class FlashcardsHtmxTests(DatabaseTestCase):
    def test_create_card_and_grade_through_htmx_routes(self) -> None:
        with self.make_client() as client:
            deck_response = client.post(
                "/workspace/flashcard-decks",
                data={"title": "Biologia", "description": "Células"},
                headers={"HX-Request": "true"},
            )

        deck = self.db.scalar(select(FlashcardDeck).where(FlashcardDeck.title == "Biologia"))
        self.assertEqual(deck_response.status_code, 200)
        self.assertIsNotNone(deck)

        with self.make_client() as client:
            card_response = client.post(
                f"/workspace/flashcard-decks/{deck.id}/flashcards",
                data={"front": "DNA", "back": "Material genético", "tags": "bio"},
                headers={"HX-Request": "true"},
            )

        link = self.db.scalar(
            select(StudyToolLink).where(StudyToolLink.workspace_id == self.workspace_id)
        )
        self.assertEqual(card_response.status_code, 200)
        self.assertIn("Flashcard criado", card_response.text)
        self.assertIsNotNone(link)

        with self.make_client() as client:
            review_response = client.get("/workspace/reviews", headers={"HX-Request": "true"})
            graded_response = client.post(
                f"/workspace/reviews/{link.id}/grade",
                data={"result": "correct"},
                headers={"HX-Request": "true"},
            )

        self.assertEqual(review_response.status_code, 200)
        self.assertIn("DNA", review_response.text)
        self.assertEqual(graded_response.status_code, 200)
        self.assertIn("Revisão salva", graded_response.text)

    def test_grade_route_accepts_earlier_review_context(self) -> None:
        with self.make_client() as client:
            deck_response = client.post(
                "/workspace/flashcard-decks",
                data={"title": "História", "description": "Brasil"},
                headers={"HX-Request": "true"},
            )
        self.assertEqual(deck_response.status_code, 200)

        deck = self.db.scalar(select(FlashcardDeck).where(FlashcardDeck.title == "História"))
        with self.make_client() as client:
            client.post(
                f"/workspace/flashcard-decks/{deck.id}/flashcards",
                data={"front": "Independência", "back": "1822", "tags": "história"},
                headers={"HX-Request": "true"},
            )

        link = self.db.scalar(
            select(StudyToolLink).where(StudyToolLink.workspace_id == self.workspace_id)
        )
        with self.make_client() as client:
            for _ in range(2):
                client.post(
                    f"/workspace/reviews/{link.id}/grade",
                    data={"result": "correct"},
                    headers={"HX-Request": "true"},
                )
            response = client.post(
                f"/workspace/reviews/{link.id}/grade",
                data={"result": "correct", "context": "review_earlier"},
                headers={"HX-Request": "true"},
            )

        self.db.refresh(link)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(link.interval_days, 12)

    def test_grade_route_rejects_unknown_context(self) -> None:
        with self.make_client() as client:
            client.post(
                "/workspace/flashcard-decks",
                data={"title": "Geografia", "description": "Clima"},
                headers={"HX-Request": "true"},
            )
        deck = self.db.scalar(select(FlashcardDeck).where(FlashcardDeck.title == "Geografia"))
        with self.make_client() as client:
            client.post(
                f"/workspace/flashcard-decks/{deck.id}/flashcards",
                data={"front": "Clima", "back": "Conjunto de condições atmosféricas", "tags": "geo"},
                headers={"HX-Request": "true"},
            )
        link = self.db.scalar(
            select(StudyToolLink).where(StudyToolLink.workspace_id == self.workspace_id)
        )

        with self.make_client() as client:
            response = client.post(
                f"/workspace/reviews/{link.id}/grade",
                data={"result": "correct", "context": "unsupported"},
                headers={"HX-Request": "true"},
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn("contexto inválido", response.text)
