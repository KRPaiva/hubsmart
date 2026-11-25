from fastapi import APIRouter, Depends, Request
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import WorkspaceContext, get_workspace_context
from app.routers.workspace.shared import int_from_form, urlencoded_form, validation_message
from app.schemas import ReviewGradePayload
from app.services import study_reviews
from app.templates import templates

router = APIRouter()


def review_response(request: Request, context: dict, status_code: int = 200):
    return templates.TemplateResponse(
        request, "partials/study_review.html", context, status_code=status_code
    )


@router.get("/workspace/reviews")
def workspace_reviews(
    request: Request,
    item_id: str | None = None,
    db: Session = Depends(get_db),
    context: WorkspaceContext = Depends(get_workspace_context),
):
    return review_response(
        request, study_reviews.review_context(db, context.workspace_id, item_id=item_id)
    )


@router.post("/workspace/reviews/{item_id}/grade")
def grade_review_item(
    request: Request,
    item_id: str,
    form: dict[str, str] = Depends(urlencoded_form),
    db: Session = Depends(get_db),
    context: WorkspaceContext = Depends(get_workspace_context),
):
    try:
        raw_quality = form.get("quality")
        quality_value = int_from_form(raw_quality) if raw_quality not in {None, ""} else None
        payload = ReviewGradePayload(
            result=form.get("result") or None,
            quality=quality_value,
            context=form.get("context") or None,
        )
        quality = payload.quality
    except ValidationError as error:
        return review_response(
            request,
            study_reviews.review_context(
                db,
                context.workspace_id,
                feedback={"message": validation_message(error, "Nota inválida."), "error": True},
            ),
            status_code=400,
        )

    try:
        result = study_reviews.grade_flashcard_review(
            db,
            context.workspace_id,
            context.user_id,
            item_id,
            result=payload.result,
            quality=quality,
            context=payload.context,
        )
    except study_reviews.StudyReviewError as error:
        return review_response(
            request,
            study_reviews.review_context(
                db, context.workspace_id, feedback={"message": str(error), "error": True}
            ),
            status_code=400,
        )

    feedback = {
        "message": f"Revisão salva. Próxima em {result['next_due_at_br']}.",
        "error": False,
        "result": result,
    }
    return review_response(
        request, study_reviews.review_context(db, context.workspace_id, feedback=feedback)
    )
