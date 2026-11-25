from sqlalchemy import func, select

from app.models.study import FlashcardReview, StudyReviewLog, StudyToolLink
from app.schemas import CreateFlashcardDeckPayload, FlashcardPayload
from app.services import flashcards, study_reviews
from tests.support import DatabaseTestCase


class StudyReviewServiceTests(DatabaseTestCase):
    def create_review_item(self) -> StudyToolLink:
        deck = flashcards.create_deck(
            self.db,
            self.workspace_id,
            self.user_id,
            CreateFlashcardDeckPayload(title="Matemática", description="Funções"),
        )
        flashcards.create_flashcard(
            self.db,
            self.workspace_id,
            self.user_id,
            deck["id"],
            FlashcardPayload(
                front="O que é domínio?", back="Conjunto de entradas.", tags=["funções"]
            ),
        )
        return self.db.scalar(
            select(StudyToolLink).where(StudyToolLink.workspace_id == self.workspace_id)
        )

    def test_created_flashcard_enters_due_queue(self) -> None:
        link = self.create_review_item()

        context = study_reviews.review_context(self.db, self.workspace_id)

        self.assertIsNotNone(link)
        self.assertEqual(context["due_count"], 1)
        self.assertEqual(context["item"]["id"], str(link.id))

    def test_grade_flashcard_review_applies_sm2_and_logs_review(self) -> None:
        link = self.create_review_item()

        result = study_reviews.grade_flashcard_review(
            self.db, self.workspace_id, self.user_id, link.id, quality=5
        )
        self.db.refresh(link)

        self.assertEqual(result["quality"], 5)
        self.assertEqual(link.interval_days, 1)
        self.assertEqual(link.repetition_count, 1)
        self.assertEqual(link.review_count, 1)
        self.assertEqual(
            self.db.scalar(select(func.count()).select_from(StudyReviewLog)),
            1,
        )
        self.assertEqual(
            self.db.scalar(select(func.count()).select_from(FlashcardReview)),
            1,
        )

    def test_wrong_review_resets_repetition_and_increments_lapse(self) -> None:
        link = self.create_review_item()

        study_reviews.grade_flashcard_review(
            self.db, self.workspace_id, self.user_id, link.id, quality=5
        )
        study_reviews.grade_flashcard_review(
            self.db, self.workspace_id, self.user_id, link.id, quality=2
        )
        self.db.refresh(link)

        self.assertEqual(link.repetition_count, 0)
        self.assertEqual(link.interval_days, 1)
        self.assertEqual(link.lapse_count, 1)
        self.assertEqual(link.review_count, 2)

    def test_context_anticipates_next_review_and_is_logged(self) -> None:
        link = self.create_review_item()

        study_reviews.grade_flashcard_review(
            self.db, self.workspace_id, self.user_id, link.id, quality=5
        )
        study_reviews.grade_flashcard_review(
            self.db, self.workspace_id, self.user_id, link.id, quality=5
        )
        result = study_reviews.grade_flashcard_review(
            self.db,
            self.workspace_id,
            self.user_id,
            link.id,
            quality=5,
            context="review_earlier",
        )
        self.db.refresh(link)

        self.assertEqual(link.interval_days, 12)
        self.assertEqual(result["item"]["interval_days"], 12)
        latest_log = self.db.scalar(
            select(StudyReviewLog).order_by(StudyReviewLog.reviewed_at.desc())
        )
        self.assertEqual(latest_log.answers, {"context": "review_earlier"})
