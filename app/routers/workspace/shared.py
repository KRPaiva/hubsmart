from typing import Any
from urllib.parse import parse_qs

from fastapi import HTTPException, Request
from pydantic import ValidationError

from app.config import settings


def is_htmx_request(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"


def validation_message(error: Exception, fallback: str) -> str:
    if not isinstance(error, ValidationError) or not error.errors():
        return fallback
    return str(error.errors()[0].get("msg") or fallback)


def comma_tags(value: str) -> list[str]:
    return [tag.strip() for tag in value.split(",") if tag.strip()]


async def urlencoded_form(request: Request) -> dict[str, str]:
    body = await request.body()
    if len(body) > settings.workspace_form_max_bytes:
        raise HTTPException(status_code=413, detail="Formulario muito grande.")
    try:
        decoded_body = body.decode("utf-8")
    except UnicodeDecodeError as error:
        raise HTTPException(status_code=400, detail="Formulário inválido.") from error
    try:
        parsed = parse_qs(
            decoded_body,
            keep_blank_values=True,
            max_num_fields=settings.workspace_form_max_fields,
        )
    except ValueError as error:
        raise HTTPException(status_code=413, detail="Formulario com campos demais.") from error
    return {key: values[-1] if values else "" for key, values in parsed.items()}


def int_from_form(value: str | None, default: int = 0) -> int:
    try:
        return int(value or "")
    except (TypeError, ValueError):
        return default


def context_with_feedback(
    data: dict[str, Any], feedback: str = "", feedback_error: bool = False
) -> dict[str, Any]:
    return {**data, "feedback": feedback, "feedback_error": feedback_error}
