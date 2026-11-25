from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID


def parse_uuid(value: str | UUID | None) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if not value:
        return None
    try:
        return UUID(str(value))
    except ValueError:
        return None


def id_for(entity: object) -> str:
    return str(entity.id)


def utc_now() -> datetime:
    return datetime.now(UTC)


def isoformat(value: datetime | date | None) -> str:
    return value.isoformat() if value else ""


def state_for_log(state: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value.isoformat() if isinstance(value, datetime) else value
        for key, value in state.items()
    }
