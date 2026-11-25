from pydantic import BaseModel, Field, field_validator

MAX_FLASHCARD_TEXT_CHARS = 5_000
MAX_FLASHCARD_TAGS = 20
MAX_FLASHCARD_TAG_CHARS = 64
MAX_FLASHCARD_DECK_TITLE_CHARS = 200
MAX_FLASHCARD_DECK_DESCRIPTION_CHARS = 1_000


class FlashcardPayload(BaseModel):
    front: str = Field(max_length=MAX_FLASHCARD_TEXT_CHARS)
    back: str = Field(max_length=MAX_FLASHCARD_TEXT_CHARS)
    tags: list[str] = Field(default_factory=list, max_length=MAX_FLASHCARD_TAGS)

    @field_validator("front", "back")
    @classmethod
    def required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("front e back são obrigatórios")
        return value

    @field_validator("tags", mode="before")
    @classmethod
    def default_tags(cls, value: list[str] | None) -> list[str]:
        return value or []

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, value: list[str]) -> list[str]:
        tags = [str(tag).strip() for tag in value if str(tag).strip()]
        if any(len(tag) > MAX_FLASHCARD_TAG_CHARS for tag in tags):
            raise ValueError("tags excedem o tamanho máximo")
        return tags


class CreateFlashcardDeckPayload(BaseModel):
    title: str = Field(max_length=MAX_FLASHCARD_DECK_TITLE_CHARS)
    description: str = Field(default="", max_length=MAX_FLASHCARD_DECK_DESCRIPTION_CHARS)

    @field_validator("title")
    @classmethod
    def required_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title é obrigatório")
        return value

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: str) -> str:
        return value.strip()
