"""Shared test fixtures for DevDiary."""

from __future__ import annotations

import asyncio
import os
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from devdiary.models import Base, Project, Diary
from devdiary.config import Config
from devdiary.scanner.git_scanner import CommitInfo, FileChange
from devdiary.generator.ai_provider import AIProvider, GenerationResult, ProviderRegistry


# ---- Database fixtures ----

@pytest_asyncio.fixture
async def db_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for testing."""
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def sample_project(db_session: AsyncSession) -> Project:
    """Create a sample project in the test database."""
    project = Project(
        name="test-project",
        repo_path="/tmp/test-repo",
        description="A test project",
        languages={"Python": 50, "JavaScript": 30},
        total_commits=100,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest_asyncio.fixture
async def sample_diary(db_session: AsyncSession, sample_project: Project) -> Diary:
    """Create a sample diary in the test database."""
    diary = Diary(
        project_id=sample_project.id,
        title="Test Diary - 2026-03-09",
        content="# Test Diary\n\nToday I worked on tests.",
        summary="Worked on tests",
        style="diary",
        date_from=datetime(2026, 3, 9, tzinfo=timezone.utc),
        date_to=datetime(2026, 3, 9, 23, 59, 59, tzinfo=timezone.utc),
        commit_count=5,
        insertions=200,
        deletions=50,
        tech_stack=["Python", "FastAPI"],
        ai_provider="mock",
        ai_model="mock-model",
        tokens_used=500,
    )
    db_session.add(diary)
    await db_session.commit()
    await db_session.refresh(diary)
    return diary


# ---- Config fixture ----

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def sample_config(temp_dir: Path) -> Config:
    """Create a sample configuration."""
    config = Config(
        config_dir=str(temp_dir / ".devdiary"),
    )
    config.ai.provider = "openai"
    config.ai.api_key = "test-key"
    config.ai.model = "gpt-4o-mini"
    config.output.dir = str(temp_dir / "diaries")
    return config


# ---- Git scanner fixtures ----

@pytest.fixture
def sample_commits() -> list[CommitInfo]:
    """Create sample commit data for testing."""
    now = datetime.now(tz=timezone.utc)
    return [
        CommitInfo(
            hash="abc123def456abc123def456abc123def4560001",
            author="Test Dev",
            email="dev@test.com",
            date=now - timedelta(hours=5),
            message="feat: add user authentication module",
            files=[
                FileChange(path="src/auth.py", insertions=150, deletions=0, change_type="add"),
                FileChange(path="tests/test_auth.py", insertions=80, deletions=0, change_type="add"),
            ],
            total_insertions=230,
            total_deletions=0,
        ),
        CommitInfo(
            hash="abc123def456abc123def456abc123def4560002",
            author="Test Dev",
            email="dev@test.com",
            date=now - timedelta(hours=3),
            message="fix: resolve login token expiration bug",
            files=[
                FileChange(path="src/auth.py", insertions=15, deletions=8, change_type="modify"),
            ],
            total_insertions=15,
            total_deletions=8,
        ),
        CommitInfo(
            hash="abc123def456abc123def456abc123def4560003",
            author="Test Dev",
            email="dev@test.com",
            date=now - timedelta(hours=1),
            message="refactor: extract token validation logic",
            files=[
                FileChange(path="src/auth.py", insertions=30, deletions=45, change_type="modify"),
                FileChange(path="src/token.py", insertions=50, deletions=0, change_type="add"),
            ],
            total_insertions=80,
            total_deletions=45,
        ),
    ]


# ---- AI Provider fixtures ----

class MockAIProvider(AIProvider):
    """Mock AI provider for testing."""

    @property
    def name(self) -> str:
        return "mock"

    @property
    def default_model(self) -> str:
        return "mock-model"

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> GenerationResult:
        return GenerationResult(
            content="# Mock Diary\n\nToday was a productive day. I worked on authentication.",
            tokens_used=100,
            model="mock-model",
            provider="mock",
        )


@pytest.fixture
def mock_provider() -> MockAIProvider:
    """Create a mock AI provider."""
    return MockAIProvider(api_key="test-key")


@pytest.fixture(autouse=True)
def register_mock_provider():
    """Register mock provider for all tests."""
    ProviderRegistry.register("mock", MockAIProvider)
    yield
