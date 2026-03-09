"""Tests for the FastAPI API endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from devdiary.api.app import create_app
from devdiary.models import Base, Project, Diary
from devdiary import database as db_module


@pytest_asyncio.fixture
async def app(db_engine):
    """Create test app with test database."""
    app = create_app()

    # Override database to use test engine
    db_module._engine = db_engine
    db_module._session_factory = None
    db_module.get_session_factory(db_engine)

    yield app

    db_module.reset_engine()


@pytest_asyncio.fixture
async def client(app) -> AsyncClient:
    """Create test HTTP client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestProjectsAPI:
    """Tests for project API endpoints."""

    @pytest.mark.asyncio
    async def test_list_projects_empty(self, client: AsyncClient):
        response = await client.get("/api/projects")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_create_project_invalid_repo(self, client: AsyncClient):
        response = await client.post("/api/projects", json={
            "name": "test",
            "repo_path": "/nonexistent/path",
        })
        assert response.status_code == 400


class TestDiariesAPI:
    """Tests for diary API endpoints."""

    @pytest.mark.asyncio
    async def test_list_diaries_empty(self, client: AsyncClient):
        response = await client.get("/api/diaries")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_diary_not_found(self, client: AsyncClient):
        response = await client.get("/api/diaries/999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_overview(self, client: AsyncClient):
        response = await client.get("/api/diaries/overview")
        assert response.status_code == 200
        data = response.json()
        assert "total_diaries" in data
        assert "total_projects" in data

    @pytest.mark.asyncio
    async def test_generate_project_not_found(self, client: AsyncClient):
        response = await client.post("/api/diaries/generate", json={
            "project_id": 999,
        })
        assert response.status_code == 404
