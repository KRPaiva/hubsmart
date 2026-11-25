"""initial brainstorm schema

Revision ID: 202609160001
Revises:
Create Date: 2026-09-16
"""

import sqlalchemy as sa
from alembic import op

revision = "202609160001"
down_revision = None
branch_labels = None
depends_on = None


def uuid_type() -> sa.Uuid:
    return sa.Uuid(as_uuid=True)


def id_column() -> sa.Column:
    return sa.Column("id", uuid_type(), nullable=False, primary_key=True)


def timestamp_column(name: str, nullable: bool = False) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), nullable=nullable)


def json_dict_default() -> sa.TextClause:
    return sa.text("'{}'")


def json_list_default() -> sa.TextClause:
    return sa.text("'[]'")


def upgrade() -> None:
    op.create_table(
        "users",
        id_column(),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        timestamp_column("deleted_at", nullable=True),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_status", "users", ["status"])
    op.create_index("ix_users_deleted_at", "users", ["deleted_at"])

    op.create_table(
        "workspaces",
        id_column(),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("owner_user_id", uuid_type(), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False, server_default=json_dict_default()),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        timestamp_column("deleted_at", nullable=True),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], name="fk_workspaces_owner_user_id"),
        sa.UniqueConstraint("slug", name="uq_workspaces_slug"),
    )
    op.create_index("ix_workspaces_owner_user_id", "workspaces", ["owner_user_id"])
    op.create_index("ix_workspaces_slug", "workspaces", ["slug"])
    op.create_index("ix_workspaces_deleted_at", "workspaces", ["deleted_at"])

    op.create_table(
        "pages",
        id_column(),
        sa.Column("workspace_id", uuid_type(), nullable=False),
        sa.Column("created_by_user_id", uuid_type(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False, server_default=json_dict_default()),
        sa.Column("attributes", sa.JSON(), nullable=False, server_default=json_dict_default()),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        timestamp_column("deleted_at", nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name="fk_pages_created_by_user_id"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name="fk_pages_workspace_id"),
    )
    op.create_index("ix_pages_workspace_id", "pages", ["workspace_id"])
    op.create_index("ix_pages_created_by_user_id", "pages", ["created_by_user_id"])
    op.create_index("ix_pages_deleted_at", "pages", ["deleted_at"])

    op.create_table(
        "flashcard_decks",
        id_column(),
        sa.Column("workspace_id", uuid_type(), nullable=False),
        sa.Column("page_id", uuid_type(), nullable=True),
        sa.Column("created_by_user_id", uuid_type(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("attributes", sa.JSON(), nullable=False, server_default=json_dict_default()),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        timestamp_column("deleted_at", nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name="fk_flashcard_decks_created_by_user_id"),
        sa.ForeignKeyConstraint(["page_id"], ["pages.id"], name="fk_flashcard_decks_page_id"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name="fk_flashcard_decks_workspace_id"),
    )
    op.create_index("ix_flashcard_decks_workspace_id", "flashcard_decks", ["workspace_id"])
    op.create_index("ix_flashcard_decks_page_id", "flashcard_decks", ["page_id"])
    op.create_index("ix_flashcard_decks_created_by_user_id", "flashcard_decks", ["created_by_user_id"])
    op.create_index("ix_flashcard_decks_deleted_at", "flashcard_decks", ["deleted_at"])

    op.create_table(
        "flashcards",
        id_column(),
        sa.Column("deck_id", uuid_type(), nullable=False),
        sa.Column("workspace_id", uuid_type(), nullable=False),
        sa.Column("created_by_user_id", uuid_type(), nullable=False),
        sa.Column("front", sa.Text(), nullable=False),
        sa.Column("back", sa.Text(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False, server_default=json_list_default()),
        sa.Column("position", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("attributes", sa.JSON(), nullable=False, server_default=json_dict_default()),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        timestamp_column("deleted_at", nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name="fk_flashcards_created_by_user_id"),
        sa.ForeignKeyConstraint(["deck_id"], ["flashcard_decks.id"], name="fk_flashcards_deck_id"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name="fk_flashcards_workspace_id"),
    )
    op.create_index("ix_flashcards_deck_id", "flashcards", ["deck_id"])
    op.create_index("ix_flashcards_workspace_id", "flashcards", ["workspace_id"])
    op.create_index("ix_flashcards_created_by_user_id", "flashcards", ["created_by_user_id"])
    op.create_index("ix_flashcards_deleted_at", "flashcards", ["deleted_at"])

    op.create_table(
        "flashcard_reviews",
        id_column(),
        sa.Column("flashcard_id", uuid_type(), nullable=False),
        sa.Column("workspace_id", uuid_type(), nullable=False),
        sa.Column("user_id", uuid_type(), nullable=False),
        sa.Column("result", sa.Text(), nullable=False),
        timestamp_column("reviewed_at"),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=json_dict_default()),
        sa.ForeignKeyConstraint(["flashcard_id"], ["flashcards.id"], name="fk_flashcard_reviews_flashcard_id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_flashcard_reviews_user_id"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name="fk_flashcard_reviews_workspace_id"),
    )
    op.create_index("ix_flashcard_reviews_flashcard_id", "flashcard_reviews", ["flashcard_id"])
    op.create_index("ix_flashcard_reviews_workspace_id", "flashcard_reviews", ["workspace_id"])
    op.create_index("ix_flashcard_reviews_user_id", "flashcard_reviews", ["user_id"])
    op.create_index("ix_flashcard_reviews_reviewed_at", "flashcard_reviews", ["reviewed_at"])

    op.create_table(
        "study_flows",
        id_column(),
        sa.Column("workspace_id", uuid_type(), nullable=False),
        sa.Column("page_id", uuid_type(), nullable=True),
        sa.Column("created_by_user_id", uuid_type(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("source_excerpt", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.Text(), nullable=False, server_default="ready"),
        sa.Column("attributes", sa.JSON(), nullable=False, server_default=json_dict_default()),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        timestamp_column("deleted_at", nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name="fk_study_flows_created_by_user_id"),
        sa.ForeignKeyConstraint(["page_id"], ["pages.id"], name="fk_study_flows_page_id"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name="fk_study_flows_workspace_id"),
    )
    op.create_index("ix_study_flows_workspace_id", "study_flows", ["workspace_id"])
    op.create_index("ix_study_flows_page_id", "study_flows", ["page_id"])
    op.create_index("ix_study_flows_created_by_user_id", "study_flows", ["created_by_user_id"])
    op.create_index("ix_study_flows_deleted_at", "study_flows", ["deleted_at"])

    op.create_table(
        "study_tool_links",
        id_column(),
        sa.Column("workspace_id", uuid_type(), nullable=False),
        sa.Column("study_flow_id", uuid_type(), nullable=False),
        sa.Column("page_id", uuid_type(), nullable=True),
        sa.Column("created_by_user_id", uuid_type(), nullable=False),
        sa.Column("tool_type", sa.Text(), nullable=False),
        sa.Column("tool_id", uuid_type(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False, server_default="manual_flashcard"),
        sa.Column("review_mode", sa.Text(), nullable=False, server_default="static_flashcard"),
        timestamp_column("due_at"),
        timestamp_column("last_reviewed_at", nullable=True),
        sa.Column("interval_days", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("repetition_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("ease_factor", sa.Float(), nullable=False, server_default=sa.text("2.5")),
        sa.Column("lapse_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("review_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("tags", sa.JSON(), nullable=False, server_default=json_list_default()),
        sa.Column("attributes", sa.JSON(), nullable=False, server_default=json_dict_default()),
        timestamp_column("created_at"),
        timestamp_column("updated_at"),
        timestamp_column("deleted_at", nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name="fk_study_tool_links_created_by_user_id"),
        sa.ForeignKeyConstraint(["page_id"], ["pages.id"], name="fk_study_tool_links_page_id"),
        sa.ForeignKeyConstraint(["study_flow_id"], ["study_flows.id"], name="fk_study_tool_links_study_flow_id"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name="fk_study_tool_links_workspace_id"),
    )
    op.create_index("ix_study_tool_links_workspace_id", "study_tool_links", ["workspace_id"])
    op.create_index("ix_study_tool_links_study_flow_id", "study_tool_links", ["study_flow_id"])
    op.create_index("ix_study_tool_links_tool", "study_tool_links", ["tool_type", "tool_id"])
    op.create_index("ix_study_tool_links_workspace_due_at", "study_tool_links", ["workspace_id", "due_at"])
    op.create_index("ix_study_tool_links_deleted_at", "study_tool_links", ["deleted_at"])

    op.create_table(
        "study_review_logs",
        id_column(),
        sa.Column("workspace_id", uuid_type(), nullable=False),
        sa.Column("user_id", uuid_type(), nullable=False),
        sa.Column("study_tool_link_id", uuid_type(), nullable=False),
        sa.Column("tool_type", sa.Text(), nullable=False),
        sa.Column("tool_id", uuid_type(), nullable=False),
        sa.Column("quality", sa.Integer(), nullable=False),
        sa.Column("result", sa.Text(), nullable=False),
        sa.Column("previous_state", sa.JSON(), nullable=False, server_default=json_dict_default()),
        sa.Column("next_state", sa.JSON(), nullable=False, server_default=json_dict_default()),
        sa.Column("answers", sa.JSON(), nullable=False, server_default=json_dict_default()),
        sa.Column("errors", sa.JSON(), nullable=False, server_default=json_list_default()),
        timestamp_column("reviewed_at"),
        sa.ForeignKeyConstraint(["study_tool_link_id"], ["study_tool_links.id"], name="fk_study_review_logs_study_tool_link_id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_study_review_logs_user_id"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name="fk_study_review_logs_workspace_id"),
    )
    op.create_index("ix_study_review_logs_workspace_id", "study_review_logs", ["workspace_id"])
    op.create_index("ix_study_review_logs_user_id", "study_review_logs", ["user_id"])
    op.create_index("ix_study_review_logs_study_tool_link_id", "study_review_logs", ["study_tool_link_id"])
    op.create_index("ix_study_review_logs_reviewed_at", "study_review_logs", ["reviewed_at"])


def downgrade() -> None:
    op.drop_table("study_review_logs")
    op.drop_table("study_tool_links")
    op.drop_table("study_flows")
    op.drop_table("flashcard_reviews")
    op.drop_table("flashcards")
    op.drop_table("flashcard_decks")
    op.drop_table("pages")
    op.drop_table("workspaces")
    op.drop_table("users")
