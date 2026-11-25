from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.study import Flashcard, FlashcardReview, StudyFlow, StudyReviewLog, StudyToolLink
from app.services import spaced_repetition
from app.services.persistence import id_for, parse_uuid, state_for_log, utc_now
from app.services.study_flow_constants import (
    FLOW_STATUS_READY,
    REVIEW_STATIC_FLASHCARD,
    SOURCE_MANUAL_FLASHCARD,
    TOOL_FLASHCARD,
)

REVIEW_DUE_PREVIEW_LIMIT = 25


class StudyReviewError(RuntimeError):
    pass


def state_from_link(link: StudyToolLink) -> dict[str, Any]:
    return {
        "due_at": link.due_at,
        "last_reviewed_at": link.last_reviewed_at,
        "interval_days": link.interval_days,
        "repetition_count": link.repetition_count,
        "ease_factor": link.ease_factor,
        "lapse_count": link.lapse_count,
        "review_count": link.review_count,
    }


def apply_state_to_link(link: StudyToolLink, state: dict[str, Any]) -> None:
    link.due_at = state["due_at"]
    link.last_reviewed_at = state["last_reviewed_at"]
    link.interval_days = state["interval_days"]
    link.repetition_count = state["repetition_count"]
    link.ease_factor = state["ease_factor"]
    link.lapse_count = state["lapse_count"]
    link.review_count = state["review_count"]


def deck_flow_query(db: Session, workspace_id: UUID, deck_id: UUID) -> StudyFlow | None:
    return db.scalar(
        select(StudyFlow)
        .where(
            StudyFlow.workspace_id == workspace_id,
            StudyFlow.content_hash == str(deck_id),
            StudyFlow.deleted_at.is_(None),
        )
        .limit(1)
    )


def create_deck_flow(
    db: Session,
    workspace_id: UUID,
    user_id: UUID,
    deck_id: UUID,
    page_id: UUID | None,
    title: str,
) -> StudyFlow:
    flow = StudyFlow(
        workspace_id=workspace_id,
        page_id=page_id,
        created_by_user_id=user_id,
        title=f"Revisão SM2: {title}",
        content_hash=str(deck_id),
        source_excerpt=f"Flashcards do deck {title}",
        status=FLOW_STATUS_READY,
        attributes={"deck_id": str(deck_id), "source": SOURCE_MANUAL_FLASHCARD},
    )
    db.add(flow)
    db.flush()
    return flow


def ensure_deck_flow(
    db: Session,
    workspace_id: UUID,
    user_id: UUID,
    deck_id: UUID,
    page_id: UUID | None,
    title: str,
) -> StudyFlow:
    flow = deck_flow_query(db, workspace_id, deck_id)
    if flow:
        return flow
    return create_deck_flow(db, workspace_id, user_id, deck_id, page_id, title)


def create_tool_link(
    db: Session,
    workspace_id: UUID,
    user_id: UUID,
    flow: StudyFlow,
    flashcard: Flashcard,
) -> StudyToolLink:
    existing = db.scalar(
        select(StudyToolLink)
        .where(
            StudyToolLink.workspace_id == workspace_id,
            StudyToolLink.tool_type == TOOL_FLASHCARD,
            StudyToolLink.tool_id == flashcard.id,
            StudyToolLink.deleted_at.is_(None),
        )
        .limit(1)
    )
    if existing:
        return existing

    initial = spaced_repetition.initial_state()
    link = StudyToolLink(
        workspace_id=workspace_id,
        study_flow_id=flow.id,
        page_id=flow.page_id,
        created_by_user_id=user_id,
        tool_type=TOOL_FLASHCARD,
        tool_id=flashcard.id,
        source_type=SOURCE_MANUAL_FLASHCARD,
        review_mode=REVIEW_STATIC_FLASHCARD,
        due_at=initial["due_at"],
        last_reviewed_at=initial["last_reviewed_at"],
        interval_days=initial["interval_days"],
        repetition_count=initial["repetition_count"],
        ease_factor=initial["ease_factor"],
        lapse_count=initial["lapse_count"],
        review_count=initial["review_count"],
        tags=flashcard.tags or [],
        attributes={"deck_id": str(flashcard.deck_id)},
    )
    db.add(link)
    db.flush()
    return link


def link_query(db: Session, workspace_id: UUID, item_id: str | UUID) -> StudyToolLink | None:
    uuid_value = parse_uuid(item_id)
    if not uuid_value:
        return None
    return db.scalar(
        select(StudyToolLink).where(
            StudyToolLink.workspace_id == workspace_id,
            StudyToolLink.id == uuid_value,
            StudyToolLink.deleted_at.is_(None),
        )
    )


def due_items(
    db: Session,
    workspace_id: UUID,
    now: datetime | None = None,
    limit: int | None = None,
) -> list[StudyToolLink]:
    current_time = now or utc_now()
    statement = (
        select(StudyToolLink)
        .where(
            StudyToolLink.workspace_id == workspace_id,
            StudyToolLink.deleted_at.is_(None),
            StudyToolLink.due_at <= current_time,
        )
        .order_by(StudyToolLink.due_at, StudyToolLink.created_at)
    )
    if limit:
        statement = statement.limit(limit)
    return list(db.scalars(statement).all())


def due_count(db: Session, workspace_id: UUID, now: datetime | None = None) -> int:
    current_time = now or utc_now()
    return int(
        db.scalar(
            select(func.count())
            .select_from(StudyToolLink)
            .where(
                StudyToolLink.workspace_id == workspace_id,
                StudyToolLink.deleted_at.is_(None),
                StudyToolLink.due_at <= current_time,
            )
        )
        or 0
    )


def next_upcoming_item(db: Session, workspace_id: UUID) -> StudyToolLink | None:
    return db.scalar(
        select(StudyToolLink)
        .where(StudyToolLink.workspace_id == workspace_id, StudyToolLink.deleted_at.is_(None))
        .order_by(StudyToolLink.due_at, StudyToolLink.created_at)
        .limit(1)
    )


def link_to_dict(db: Session, link: StudyToolLink) -> dict[str, Any]:
    card = db.get(Flashcard, link.tool_id)
    resource = None
    title = "Flashcard removido"
    if card:
        title = card.front
        resource = {
            "id": str(card.id),
            "front": card.front,
            "back": card.back,
            "tags": card.tags or [],
            "deck_id": str(card.deck_id),
        }
    return {
        "id": id_for(link),
        "study_flow_id": str(link.study_flow_id),
        "tool_type": link.tool_type,
        "tool_id": str(link.tool_id),
        "title": title,
        "resource": resource,
        "due_at": link.due_at,
        "due_at_br": link.due_at.strftime("%d/%m/%Y") if link.due_at else "",
        "last_reviewed_at": link.last_reviewed_at,
        "interval_days": link.interval_days,
        "repetition_count": link.repetition_count,
        "ease_factor": link.ease_factor,
        "lapse_count": link.lapse_count,
        "review_count": link.review_count,
        "tags": link.tags or [],
    }


def links_to_dicts(db: Session, links: list[StudyToolLink]) -> list[dict[str, Any]]:
    return [link_to_dict(db, link) for link in links]


def review_context(
    db: Session,
    workspace_id: UUID,
    item_id: str | UUID | None = None,
    feedback: dict[str, Any] | None = None,
) -> dict[str, Any]:
    due_review_items = due_items(db, workspace_id, limit=REVIEW_DUE_PREVIEW_LIMIT)
    if item_id:
        link = link_query(db, workspace_id, item_id)
    elif due_review_items:
        link = due_review_items[0]
    else:
        link = next_upcoming_item(db, workspace_id)

    return {
        "item": link_to_dict(db, link) if link else None,
        "due_items": links_to_dicts(db, due_review_items),
        "due_count": due_count(db, workspace_id),
        "feedback": feedback,
    }


def create_review_log(
    db: Session,
    user_id: UUID,
    link: StudyToolLink,
    quality: int,
    result: str,
    previous_state: dict[str, Any],
    next_state: dict[str, Any],
    errors: list[dict[str, Any]] | None = None,
    context: str | None = None,
) -> StudyReviewLog:
    log = StudyReviewLog(
        workspace_id=link.workspace_id,
        user_id=user_id,
        study_tool_link_id=link.id,
        tool_type=link.tool_type,
        tool_id=link.tool_id,
        quality=quality,
        result=result,
        previous_state=state_for_log(previous_state),
        next_state=state_for_log(next_state),
        answers={"context": context} if context else {},
        errors=errors or [],
        reviewed_at=next_state["last_reviewed_at"],
    )
    db.add(log)
    return log


def quality_for_grade(result: str | None, quality: int | None) -> int:
    if quality is not None:
        return spaced_repetition.bounded_quality(quality)
    return spaced_repetition.quality_from_flashcard_result(result or "wrong")


def grade_flashcard_review(
    db: Session,
    workspace_id: UUID,
    user_id: UUID,
    item_id: str | UUID,
    result: str | None = None,
    quality: int | None = None,
    context: str | None = None,
) -> dict[str, Any]:
    link = link_query(db, workspace_id, item_id)
    if not link or link.tool_type != TOOL_FLASHCARD:
        raise StudyReviewError("Item de flashcard não encontrado.")

    card = db.get(Flashcard, link.tool_id)
    if not card:
        raise StudyReviewError("Flashcard não encontrado.")

    grade_quality = quality_for_grade(result, quality)
    normalized_result = "correct" if grade_quality >= 3 else "wrong"
    previous_state = state_from_link(link)
    next_state = spaced_repetition.apply_review(
        previous_state, grade_quality, context=context
    )
    apply_state_to_link(link, next_state)
    create_review_log(
        db,
        user_id,
        link,
        grade_quality,
        normalized_result,
        previous_state,
        next_state,
        errors=[]
        if normalized_result == "correct"
        else [{"prompt": card.front, "answer": card.back, "tags": card.tags or []}],
        context=context,
    )
    db.add(
        FlashcardReview(
            flashcard_id=card.id,
            workspace_id=workspace_id,
            user_id=user_id,
            result=normalized_result,
            reviewed_at=next_state["last_reviewed_at"],
            metadata_={"study_tool_link_id": str(link.id), "quality": grade_quality},
        )
    )
    db.commit()
    return {
        "item": link_to_dict(db, link),
        "quality": grade_quality,
        "result": normalized_result,
        "next_due_at": link.due_at,
        "next_due_at_br": link.due_at.strftime("%d/%m/%Y"),
    }
