from datetime import UTC, datetime, timedelta
from typing import Any

DEFAULT_EASE_FACTOR = 2.5
MIN_EASE_FACTOR = 1.3


def utc_now() -> datetime:
    return datetime.now(UTC)


def initial_state(now: datetime | None = None) -> dict[str, Any]:
    current_time = now or utc_now()
    return {
        "due_at": current_time,
        "last_reviewed_at": None,
        "interval_days": 0,
        "repetition_count": 0,
        "ease_factor": DEFAULT_EASE_FACTOR,
        "lapse_count": 0,
        "review_count": 0,
    }


def bounded_quality(quality: int) -> int:
    return min(max(int(quality), 0), 5)


def next_ease_factor(ease_factor: float, quality: int) -> float:
    quality = bounded_quality(quality)
    next_value = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    return round(max(MIN_EASE_FACTOR, next_value), 4)


def adjust_interval_for_context(
    interval_days: int,
    context: str | None = None,
) -> int:
    """
    Ajusta o intervalo sugerido com base em um contexto opcional.

    Sem contexto reconhecido, mantém o intervalo original.
    O contexto 'review_earlier' antecipa a próxima revisão em 25%.
    """
    interval = max(1, int(interval_days))
    normalized_context = str(context or "").strip().lower()

    if normalized_context == "review_earlier":
        return max(1, round(interval * 0.75))

    return interval


def apply_review(
    state: dict[str, Any],
    quality: int,
    reviewed_at: datetime | None = None,
    context: str | None = None,
) -> dict[str, Any]:
    quality = bounded_quality(quality)
    current_time = reviewed_at or utc_now()
    previous_interval = int(state.get("interval_days") or 0)
    previous_repetition = int(state.get("repetition_count") or 0)
    previous_ease = float(state.get("ease_factor") or DEFAULT_EASE_FACTOR)
    lapse_count = int(state.get("lapse_count") or 0)
    review_count = int(state.get("review_count") or 0) + 1

    if quality < 3:
        repetition_count = 0
        interval_days = 1
        lapse_count += 1
    else:
        if previous_repetition == 0:
            interval_days = 1
        elif previous_repetition == 1:
            interval_days = 6
        else:
            interval_days = max(1, round(previous_interval * previous_ease))
        repetition_count = previous_repetition + 1

    interval_days = adjust_interval_for_context(interval_days, context)
    ease_factor = next_ease_factor(previous_ease, quality)
    due_at = current_time + timedelta(days=interval_days)

    return {
        "due_at": due_at,
        "last_reviewed_at": current_time,
        "interval_days": interval_days,
        "repetition_count": repetition_count,
        "ease_factor": ease_factor,
        "lapse_count": lapse_count,
        "review_count": review_count,
    }


def quality_from_flashcard_result(result: str) -> int:
    normalized = str(result or "").strip().lower()
    if normalized in {"correct", "acerto", "acertei", "certo"}:
        return 5
    if normalized in {"partial", "parcial", "quase"}:
        return 3
    return 2


def quality_from_quiz_accuracy(accuracy: int | float) -> int:
    value = float(accuracy or 0)
    if value <= 40:
        return 2
    if value <= 69:
        return 3
    if value <= 84:
        return 4
    return 5
