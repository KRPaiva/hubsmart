from sqlalchemy import text
from sqlalchemy.orm import Session


def database_ready(db: Session) -> bool:
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        return False
    return True
