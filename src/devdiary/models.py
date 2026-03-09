"""SQLAlchemy ORM models for DevDiary."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Index,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class Project(Base):
    """Project / repository model."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    repo_path: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    last_scanned: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    total_commits: Mapped[int] = mapped_column(Integer, default=0)
    languages: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    commits: Mapped[list[Commit]] = relationship("Commit", back_populates="project", cascade="all, delete-orphan")
    diaries: Mapped[list[Diary]] = relationship("Diary", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}')>"


class Commit(Base):
    """Cached commit information."""

    __tablename__ = "commits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    hash: Mapped[str] = mapped_column(String(40), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), default="")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    insertions: Mapped[int] = mapped_column(Integer, default=0)
    deletions: Mapped[int] = mapped_column(Integer, default=0)
    files_changed: Mapped[int] = mapped_column(Integer, default=0)
    file_list: Mapped[dict] = mapped_column(JSON, default=list)  # List of changed file paths

    # Relationships
    project: Mapped[Project] = relationship("Project", back_populates="commits")

    __table_args__ = (
        Index("ix_commits_project_date", "project_id", "date"),
        Index("ix_commits_hash", "hash"),
    )

    def __repr__(self) -> str:
        return f"<Commit(hash='{self.hash[:8]}', message='{self.message[:50]}')>"


class Diary(Base):
    """Generated diary / report."""

    __tablename__ = "diaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="")
    style: Mapped[str] = mapped_column(String(50), default="diary")  # diary / blog / report
    date_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    date_to: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    commit_count: Mapped[int] = mapped_column(Integer, default=0)
    insertions: Mapped[int] = mapped_column(Integer, default=0)
    deletions: Mapped[int] = mapped_column(Integer, default=0)
    tech_stack: Mapped[dict] = mapped_column(JSON, default=list)  # List of detected tech
    ai_provider: Mapped[str] = mapped_column(String(100), default="")
    ai_model: Mapped[str] = mapped_column(String(100), default="")
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    project: Mapped[Project] = relationship("Project", back_populates="diaries")

    __table_args__ = (
        Index("ix_diaries_project_date", "project_id", "date_from", "date_to"),
        Index("ix_diaries_style", "style"),
    )

    def __repr__(self) -> str:
        return f"<Diary(id={self.id}, title='{self.title[:50]}')>"
