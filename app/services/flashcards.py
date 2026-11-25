from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.study import Flashcard, FlashcardDeck, Page
from app.schemas import CreateFlashcardDeckPayload, FlashcardPayload
from app.services import study_reviews
from app.services.persistence import id_for, parse_uuid


def comma_tags(value: str) -> list[str]:
    return [tag.strip() for tag in value.split(",") if tag.strip()]


def deck_query(db: Session, workspace_id: UUID, deck_id: str | UUID) -> FlashcardDeck | None:
    uuid_value = parse_uuid(deck_id)
    if not uuid_value:
        return None
    return db.scalar(
        select(FlashcardDeck).where(
            FlashcardDeck.workspace_id == workspace_id,
            FlashcardDeck.id == uuid_value,
            FlashcardDeck.deleted_at.is_(None),
        )
    )


def card_to_dict(card: Flashcard) -> dict[str, Any]:
    return {
        "id": id_for(card),
        "deck_id": str(card.deck_id),
        "front": card.front,
        "back": card.back,
        "tags": card.tags or [],
        "position": card.position,
    }


def deck_to_dict(db: Session, deck: FlashcardDeck) -> dict[str, Any]:
    cards = db.scalars(
        select(Flashcard)
        .where(Flashcard.deck_id == deck.id, Flashcard.deleted_at.is_(None))
        .order_by(Flashcard.position, Flashcard.front)
    ).all()
    return {
        "id": id_for(deck),
        "title": deck.title,
        "description": deck.description,
        "card_count": len(cards),
        "flashcards": [card_to_dict(card) for card in cards],
    }


def list_decks(db: Session, workspace_id: UUID) -> list[dict[str, Any]]:
    rows = db.execute(
        select(FlashcardDeck, func.count(Flashcard.id))
        .outerjoin(
            Flashcard, (Flashcard.deck_id == FlashcardDeck.id) & Flashcard.deleted_at.is_(None)
        )
        .where(FlashcardDeck.workspace_id == workspace_id, FlashcardDeck.deleted_at.is_(None))
        .group_by(FlashcardDeck.id)
        .order_by(FlashcardDeck.created_at, FlashcardDeck.title)
    ).all()
    return [
        {
            "id": id_for(deck),
            "title": deck.title,
            "description": deck.description,
            "card_count": int(card_count or 0),
        }
        for deck, card_count in rows
    ]


def load_deck(db: Session, workspace_id: UUID, deck_id: str | UUID) -> dict[str, Any] | None:
    deck = deck_query(db, workspace_id, deck_id)
    return deck_to_dict(db, deck) if deck else None


def create_deck(
    db: Session, workspace_id: UUID, user_id: UUID, payload: CreateFlashcardDeckPayload
) -> dict[str, Any]:
    page = Page(
        workspace_id=workspace_id,
        created_by_user_id=user_id,
        title=f"Deck: {payload.title}",
        content={"blocks": []},
        attributes={"source": "flashcard_deck"},
    )
    db.add(page)
    db.flush()

    deck = FlashcardDeck(
        workspace_id=workspace_id,
        page_id=page.id,
        created_by_user_id=user_id,
        title=payload.title,
        description=payload.description,
    )
    db.add(deck)
    db.flush()
    study_reviews.ensure_deck_flow(db, workspace_id, user_id, deck.id, page.id, deck.title)
    db.commit()
    return deck_to_dict(db, deck)


def next_card_position(db: Session, deck_id: UUID) -> int:
    max_position = db.scalar(
        select(func.coalesce(func.max(Flashcard.position), -1)).where(
            Flashcard.deck_id == deck_id, Flashcard.deleted_at.is_(None)
        )
    )
    return int(max_position or -1) + 1


def create_flashcard(
    db: Session,
    workspace_id: UUID,
    user_id: UUID,
    deck_id: str | UUID,
    payload: FlashcardPayload,
) -> dict[str, Any] | None:
    deck = deck_query(db, workspace_id, deck_id)
    if not deck:
        return None
    card = Flashcard(
        deck_id=deck.id,
        workspace_id=workspace_id,
        created_by_user_id=user_id,
        front=payload.front,
        back=payload.back,
        tags=payload.tags or [],
        position=next_card_position(db, deck.id),
    )
    db.add(card)
    db.flush()
    flow = study_reviews.ensure_deck_flow(
        db, workspace_id, user_id, deck.id, deck.page_id, deck.title
    )
    study_reviews.create_tool_link(db, workspace_id, user_id, flow, card)
    db.commit()
    return card_to_dict(card)
