from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, empty_dict, empty_list


class Page(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "pages"

    workspace_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("workspaces.id"), nullable=False
    )
    created_by_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[dict] = mapped_column(JSON, default=lambda: {"blocks": []}, nullable=False)
    attributes: Mapped[dict] = mapped_column(JSON, default=empty_dict, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_pages_workspace_id", "workspace_id"),
        Index("ix_pages_created_by_user_id", "created_by_user_id"),
        Index("ix_pages_deleted_at", "deleted_at"),
    )


class FlashcardDeck(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "flashcard_decks"

    workspace_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("workspaces.id"), nullable=False
    )
    page_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("pages.id"))
    created_by_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    attributes: Mapped[dict] = mapped_column(JSON, default=empty_dict, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_flashcard_decks_workspace_id", "workspace_id"),
        Index("ix_flashcard_decks_page_id", "page_id"),
        Index("ix_flashcard_decks_created_by_user_id", "created_by_user_id"),
        Index("ix_flashcard_decks_deleted_at", "deleted_at"),
    )


class Flashcard(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "flashcards"

    deck_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("flashcard_decks.id"), nullable=False
    )
    workspace_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("workspaces.id"), nullable=False
    )
    created_by_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    front: Mapped[str] = mapped_column(Text, nullable=False)
    back: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=empty_list, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    attributes: Mapped[dict] = mapped_column(JSON, default=empty_dict, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_flashcards_deck_id", "deck_id"),
        Index("ix_flashcards_workspace_id", "workspace_id"),
        Index("ix_flashcards_created_by_user_id", "created_by_user_id"),
        Index("ix_flashcards_deleted_at", "deleted_at"),
    )


class FlashcardReview(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "flashcard_reviews"

    flashcard_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("flashcards.id"), nullable=False
    )
    workspace_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("workspaces.id"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    result: Mapped[str] = mapped_column(Text, nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=empty_dict, nullable=False)

    __table_args__ = (
        Index("ix_flashcard_reviews_flashcard_id", "flashcard_id"),
        Index("ix_flashcard_reviews_workspace_id", "workspace_id"),
        Index("ix_flashcard_reviews_user_id", "user_id"),
        Index("ix_flashcard_reviews_reviewed_at", "reviewed_at"),
    )


class StudyFlow(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "study_flows"

    workspace_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("workspaces.id"), nullable=False
    )
    page_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("pages.id"))
    created_by_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    source_excerpt: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(Text, default="ready", nullable=False)
    attributes: Mapped[dict] = mapped_column(JSON, default=empty_dict, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_study_flows_workspace_id", "workspace_id"),
        Index("ix_study_flows_page_id", "page_id"),
        Index("ix_study_flows_created_by_user_id", "created_by_user_id"),
        Index("ix_study_flows_deleted_at", "deleted_at"),
    )


class StudyToolLink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "study_tool_links"

    workspace_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("workspaces.id"), nullable=False
    )
    study_flow_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("study_flows.id"), nullable=False
    )
    page_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("pages.id"))
    created_by_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    tool_type: Mapped[str] = mapped_column(Text, nullable=False)
    tool_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    source_type: Mapped[str] = mapped_column(Text, default="manual_flashcard", nullable=False)
    review_mode: Mapped[str] = mapped_column(Text, default="static_flashcard", nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    interval_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    repetition_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5, nullable=False)
    lapse_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=empty_list, nullable=False)
    attributes: Mapped[dict] = mapped_column(JSON, default=empty_dict, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_study_tool_links_workspace_id", "workspace_id"),
        Index("ix_study_tool_links_study_flow_id", "study_flow_id"),
        Index("ix_study_tool_links_tool", "tool_type", "tool_id"),
        Index("ix_study_tool_links_workspace_due_at", "workspace_id", "due_at"),
        Index("ix_study_tool_links_deleted_at", "deleted_at"),
    )


class StudyReviewLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "study_review_logs"

    workspace_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("workspaces.id"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    study_tool_link_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("study_tool_links.id"), nullable=False
    )
    tool_type: Mapped[str] = mapped_column(Text, nullable=False)
    tool_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    quality: Mapped[int] = mapped_column(Integer, nullable=False)
    result: Mapped[str] = mapped_column(Text, nullable=False)
    previous_state: Mapped[dict] = mapped_column(JSON, default=empty_dict, nullable=False)
    next_state: Mapped[dict] = mapped_column(JSON, default=empty_dict, nullable=False)
    answers: Mapped[dict] = mapped_column(JSON, default=empty_dict, nullable=False)
    errors: Mapped[list] = mapped_column(JSON, default=empty_list, nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_study_review_logs_workspace_id", "workspace_id"),
        Index("ix_study_review_logs_user_id", "user_id"),
        Index("ix_study_review_logs_study_tool_link_id", "study_tool_link_id"),
        Index("ix_study_review_logs_reviewed_at", "reviewed_at"),
    )
