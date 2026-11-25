from fastapi import APIRouter, Depends, Request
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import WorkspaceContext, get_workspace_context, require_workspace_writer
from app.routers.workspace.shared import comma_tags, urlencoded_form, validation_message
from app.schemas import CreateFlashcardDeckPayload, FlashcardPayload
from app.services import flashcards, study_reviews
from app.templates import templates

router = APIRouter()


def flashcards_context(
    db: Session,
    context: WorkspaceContext,
    deck_id: str | None = None,
    mode: str = "study",
    feedback: str = "",
    feedback_error: bool = False,
) -> dict:
    selected_deck = flashcards.load_deck(db, context.workspace_id, deck_id) if deck_id else None
    return {
        "decks": flashcards.list_decks(db, context.workspace_id),
        "selected_deck": selected_deck,
        "mode": mode,
        "feedback": feedback,
        "feedback_error": feedback_error,
        "can_write_content": context.can_write_content,
        "due_count": study_reviews.due_count(db, context.workspace_id),
    }


def flashcards_response(
    request: Request,
    db: Session,
    context: WorkspaceContext,
    deck_id: str | None = None,
    mode: str = "study",
    feedback: str = "",
    feedback_error: bool = False,
    status_code: int = 200,
):
    return templates.TemplateResponse(
        request,
        "partials/flashcards.html",
        flashcards_context(db, context, deck_id, mode, feedback, feedback_error),
        status_code=status_code,
    )


@router.get("/workspace/flashcards")
def workspace_flashcards(
    request: Request,
    deck_id: str | None = None,
    mode: str = "study",
    db: Session = Depends(get_db),
    context: WorkspaceContext = Depends(get_workspace_context),
):
    return flashcards_response(request, db, context, deck_id=deck_id, mode=mode)


@router.post("/workspace/flashcard-decks")
def workspace_create_flashcard_deck(
    request: Request,
    form: dict[str, str] = Depends(urlencoded_form),
    db: Session = Depends(get_db),
    context: WorkspaceContext = Depends(require_workspace_writer),
):
    try:
        deck = flashcards.create_deck(
            db,
            context.workspace_id,
            context.user_id,
            CreateFlashcardDeckPayload(
                title=form.get("title", ""),
                description=form.get("description", ""),
            ),
        )
    except ValidationError as error:
        return flashcards_response(
            request,
            db,
            context,
            mode="create_deck",
            feedback=validation_message(error, "Informe o nome do deck."),
            feedback_error=True,
        )
    return flashcards_response(request, db, context, deck_id=deck["id"], mode="create")


@router.post("/workspace/flashcard-decks/{deck_id}/flashcards")
def workspace_create_flashcard(
    request: Request,
    deck_id: str,
    form: dict[str, str] = Depends(urlencoded_form),
    db: Session = Depends(get_db),
    context: WorkspaceContext = Depends(require_workspace_writer),
):
    try:
        created = flashcards.create_flashcard(
            db,
            context.workspace_id,
            context.user_id,
            deck_id,
            FlashcardPayload(
                front=form.get("front", ""),
                back=form.get("back", ""),
                tags=comma_tags(form.get("tags", "")),
            ),
        )
    except ValidationError as error:
        return flashcards_response(
            request,
            db,
            context,
            deck_id=deck_id,
            mode="create",
            feedback=validation_message(error, "Preencha frente e verso."),
            feedback_error=True,
        )

    if created is None:
        return flashcards_response(
            request, db, context, feedback="Deck não encontrado.", feedback_error=True
        )
    return flashcards_response(
        request,
        db,
        context,
        deck_id=deck_id,
        mode="create",
        feedback="Flashcard criado e enviado para a fila SM2.",
    )
