from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.db import SessionLocal
from app.models.study import FlashcardDeck
from app.schemas import CreateFlashcardDeckPayload, FlashcardPayload
from app.services.bootstrap import ensure_dev_context
from app.services.flashcards import create_deck, create_flashcard


def run() -> None:
    db = SessionLocal()
    try:
        user, workspace = ensure_dev_context(db)
        existing = db.scalar(
            select(FlashcardDeck).where(
                FlashcardDeck.workspace_id == workspace.id,
                FlashcardDeck.title == "SM2 Demo",
                FlashcardDeck.deleted_at.is_(None),
            )
        )
        if existing:
            print("Seed já existe.")
            return

        deck = create_deck(
            db,
            workspace.id,
            user.id,
            CreateFlashcardDeckPayload(
                title="SM2 Demo",
                description="Cartões de exemplo para testar repetição espaçada.",
            ),
        )
        samples = [
            FlashcardPayload(
                front="Qual é o primeiro intervalo do SM2 após um acerto inicial?",
                back="1 dia.",
                tags=["sm2", "intervalo"],
            ),
            FlashcardPayload(
                front="O que acontece com repetition_count quando quality < 3?",
                back="Ele volta para 0 e o lapse_count aumenta.",
                tags=["sm2", "erro"],
            ),
            FlashcardPayload(
                front="Qual é o ease factor mínimo nesta implementação?",
                back="1.3.",
                tags=["sm2", "ease"],
            ),
        ]
        for payload in samples:
            create_flashcard(db, workspace.id, user.id, deck["id"], payload)
        print("Seed criado com sucesso.")
    except SQLAlchemyError as error:
        raise SystemExit(
            "Não foi possível acessar o banco. Rode 'make setup' para criar o SQLite local "
            "e aplicar as migrations."
        ) from error
    finally:
        db.close()


if __name__ == "__main__":
    run()
