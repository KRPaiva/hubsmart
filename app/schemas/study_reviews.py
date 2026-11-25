from pydantic import BaseModel, field_validator, model_validator


class ReviewGradePayload(BaseModel):
    quality: int | None = None
    result: str | None = None
    context: str | None = None

    @field_validator("quality")
    @classmethod
    def validate_quality(cls, value: int | None) -> int | None:
        if value is None:
            return None
        return min(max(int(value), 0), 5)

    @field_validator("result")
    @classmethod
    def validate_result(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in {"correct", "wrong", "partial", "acertei", "errei"}:
            raise ValueError("result inválido")
        return normalized

    @field_validator("context")
    @classmethod
    def validate_context(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        normalized = value.strip().lower()
        if normalized != "review_earlier":
            raise ValueError("contexto inválido")
        return normalized

    @model_validator(mode="after")
    def require_quality_or_result(self) -> "ReviewGradePayload":
        if self.quality is None and self.result is None:
            raise ValueError("quality ou result é obrigatório")
        return self
