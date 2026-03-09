"""Initial database schema.

Revision ID: 001_initial
Revises:
Create Date: 2026-03-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Projects table
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("repo_path", sa.String(1024), nullable=False),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("last_scanned", sa.DateTime(), nullable=True),
        sa.Column("total_commits", sa.Integer(), server_default="0"),
        sa.Column("languages", sa.JSON(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repo_path"),
    )

    # Commits table
    op.create_table(
        "commits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("hash", sa.String(40), nullable=False),
        sa.Column("author", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), server_default=""),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("insertions", sa.Integer(), server_default="0"),
        sa.Column("deletions", sa.Integer(), server_default="0"),
        sa.Column("files_changed", sa.Integer(), server_default="0"),
        sa.Column("file_list", sa.JSON(), server_default="[]"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_commits_project_date", "commits", ["project_id", "date"])
    op.create_index("ix_commits_hash", "commits", ["hash"])

    # Diaries table
    op.create_table(
        "diaries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), server_default=""),
        sa.Column("style", sa.String(50), server_default="diary"),
        sa.Column("date_from", sa.DateTime(), nullable=False),
        sa.Column("date_to", sa.DateTime(), nullable=False),
        sa.Column("commit_count", sa.Integer(), server_default="0"),
        sa.Column("insertions", sa.Integer(), server_default="0"),
        sa.Column("deletions", sa.Integer(), server_default="0"),
        sa.Column("tech_stack", sa.JSON(), server_default="[]"),
        sa.Column("ai_provider", sa.String(100), server_default=""),
        sa.Column("ai_model", sa.String(100), server_default=""),
        sa.Column("tokens_used", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_diaries_project_date", "diaries", ["project_id", "date_from", "date_to"])
    op.create_index("ix_diaries_style", "diaries", ["style"])


def downgrade() -> None:
    op.drop_table("diaries")
    op.drop_table("commits")
    op.drop_table("projects")
