from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.identity import User, Workspace


def ensure_dev_context(db: Session) -> tuple[User, Workspace]:
    user = db.scalar(select(User).where(User.email == settings.dev_user_email))
    if not user:
        user = User(email=settings.dev_user_email, name=settings.dev_user_name)
        db.add(user)
        db.flush()

    workspace = db.scalar(
        select(Workspace).where(Workspace.slug == settings.default_workspace_slug)
    )
    if not workspace:
        workspace = Workspace(
            name="Workspace Brainstorm",
            slug=settings.default_workspace_slug,
            owner_user_id=user.id,
            attributes={"kind": "brainstorm"},
        )
        db.add(workspace)
        db.flush()

    db.commit()
    return user, workspace
