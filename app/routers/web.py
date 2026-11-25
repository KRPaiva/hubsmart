from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import WorkspaceContext, get_workspace_context
from app.routers.workspace import flashcards, study_reviews
from app.services import study_reviews as study_review_service
from app.templates import templates

router = APIRouter()


@router.get("/")
def index():
    return RedirectResponse("/workspace", status_code=303)


@router.get("/workspace")
def workspace(
    request: Request,
    db: Session = Depends(get_db),
    context: WorkspaceContext = Depends(get_workspace_context),
):
    return templates.TemplateResponse(
        request,
        "workspace.html",
        {
            "workspace_context": context,
            "due_count": study_review_service.due_count(db, context.workspace_id),
        },
    )


router.include_router(flashcards.router)
router.include_router(study_reviews.router)
