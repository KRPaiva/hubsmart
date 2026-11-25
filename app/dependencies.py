from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.bootstrap import ensure_dev_context


@dataclass(frozen=True)
class WorkspaceContext:
    user_id: UUID
    workspace_id: UUID
    workspace_name: str
    can_write_content: bool = True


def get_workspace_context(db: Session = Depends(get_db)) -> WorkspaceContext:
    user, workspace = ensure_dev_context(db)
    return WorkspaceContext(
        user_id=user.id,
        workspace_id=workspace.id,
        workspace_name=workspace.name,
        can_write_content=True,
    )


def require_workspace_writer(
    context: WorkspaceContext = Depends(get_workspace_context),
) -> WorkspaceContext:
    return context
