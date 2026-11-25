import unittest
from datetime import UTC, datetime, timedelta

from freezegun import freeze_time

from app.services import spaced_repetition


class SpacedRepetitionTests(unittest.TestCase):
    def test_initial_state(self) -> None:
        now = datetime(2026, 5, 27, tzinfo=UTC)
        state = spaced_repetition.initial_state(now)

        self.assertEqual(state["due_at"], now)
        self.assertEqual(state["ease_factor"], 2.5)
        self.assertEqual(state["interval_days"], 0)
        self.assertEqual(state["repetition_count"], 0)

    def test_successive_correct_reviews_use_sm2_intervals(self) -> None:
        now = datetime(2026, 5, 27, tzinfo=UTC)
        state = spaced_repetition.initial_state(now)

        first = spaced_repetition.apply_review(state, 5, now)
        second = spaced_repetition.apply_review(first, 5, now)
        third = spaced_repetition.apply_review(second, 5, now)

        self.assertEqual(first["interval_days"], 1)
        self.assertEqual(second["interval_days"], 6)
        self.assertEqual(third["interval_days"], 16)
        self.assertEqual(third["repetition_count"], 3)

    def test_wrong_review_resets_repetition_and_schedules_tomorrow(self) -> None:
        now = datetime(2026, 5, 27, tzinfo=UTC)
        state = spaced_repetition.apply_review(spaced_repetition.initial_state(now), 5, now)
        wrong = spaced_repetition.apply_review(state, 2, now)

        self.assertEqual(wrong["interval_days"], 1)
        self.assertEqual(wrong["repetition_count"], 0)
        self.assertEqual(wrong["lapse_count"], 1)

    def test_apply_review_sets_utc_review_and_due_dates(self) -> None:
        now = datetime(2026, 5, 27, 12, 30, tzinfo=UTC)
        state = spaced_repetition.initial_state(now)

        reviewed = spaced_repetition.apply_review(state, 4, now)

        self.assertEqual(reviewed["last_reviewed_at"], now)
        self.assertEqual(reviewed["due_at"], now + timedelta(days=1))
        self.assertEqual(reviewed["review_count"], 1)

    def test_ease_factor_never_goes_below_minimum(self) -> None:
        now = datetime(2026, 5, 27, tzinfo=UTC)
        state = {
            **spaced_repetition.initial_state(now),
            "ease_factor": 1.31,
            "interval_days": 10,
            "repetition_count": 3,
        }

        reviewed = spaced_repetition.apply_review(state, 0, now)

        self.assertEqual(reviewed["ease_factor"], spaced_repetition.MIN_EASE_FACTOR)
        self.assertEqual(reviewed["interval_days"], 1)

    def test_bounded_quality_accepts_out_of_range_values(self) -> None:
        self.assertEqual(spaced_repetition.bounded_quality(-20), 0)
        self.assertEqual(spaced_repetition.bounded_quality(99), 5)

    @freeze_time("2026-05-27 15:00:00", tz_offset=0)
    def test_initial_state_defaults_to_current_utc_time(self) -> None:
        state = spaced_repetition.initial_state()

        self.assertEqual(state["due_at"], datetime(2026, 5, 27, 15, 0, tzinfo=UTC))

    def test_quality_mapping(self) -> None:
        self.assertEqual(spaced_repetition.quality_from_flashcard_result("Acertei"), 5)
        self.assertEqual(spaced_repetition.quality_from_flashcard_result("Errei"), 2)
        self.assertEqual(spaced_repetition.quality_from_quiz_accuracy(40), 2)
        self.assertEqual(spaced_repetition.quality_from_quiz_accuracy(41), 3)
        self.assertEqual(spaced_repetition.quality_from_quiz_accuracy(70), 4)
        self.assertEqual(spaced_repetition.quality_from_quiz_accuracy(85), 5)

    
    def test_context_without_adjustment_preserves_interval(self) -> None:
        self.assertEqual(
            spaced_repetition.adjust_interval_for_context(10),
            10,
        )

    def test_review_earlier_context_reduces_interval(self) -> None:
        self.assertEqual(
            spaced_repetition.adjust_interval_for_context(
                10,
                "review_earlier",
            ),
            8,
        )

    def test_unknown_context_preserves_interval(self) -> None:
        self.assertEqual(
            spaced_repetition.adjust_interval_for_context(
                10,
                "unknown_context",
            ),
            10,
        )

    def test_context_adjustment_never_goes_below_one_day(self) -> None:
        self.assertEqual(
            spaced_repetition.adjust_interval_for_context(
                1,
                "review_earlier",
            ),
            1,
        )

