"""Project management API routes."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from devdiary.database import get_db_session
from devdiary.models import Project, Commit, Diary
from devdiary.api.schemas import ProjectCreate, ProjectResponse, ProjectStatsResponse

router = APIRouter(prefix="/api/projects", tags=["projects"])


async def _get_session():
    """Dependency to get database session."""
    async with get_db_session() as session:
        yield session


@router.get("", response_model=list[ProjectResponse])
async def list_projects(session: AsyncSession = Depends(_get_session)):
    """Get all projects."""
    result = await session.execute(
        select(Project).order_by(Project.updated_at.desc())
    )
    projects = result.scalars().all()
    return [ProjectResponse.model_validate(p) for p in projects]


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    session: AsyncSession = Depends(_get_session),
):
    """Add a new project/repository."""
    # Validate the repository path
    repo_path = str(Path(data.repo_path).resolve())

    try:
        from devdiary.scanner.git_scanner import GitScanner
        scanner = GitScanner(repo_path)
        if not scanner.validate():
            raise HTTPException(status_code=400, detail="Invalid Git repository path")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Check if already exists
    existing = await session.execute(
        select(Project).where(Project.repo_path == repo_path)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Repository already registered")

    # Detect tech stack
    from devdiary.scanner.tech_detector import TechDetector
    detector = TechDetector(repo_path)
    tech_stack = detector.detect(scanner.get_file_extensions())

    project = Project(
        name=data.name,
        repo_path=repo_path,
        description=data.description,
        languages=tech_stack.languages,
    )
    session.add(project)
    await session.flush()
    await session.refresh(project)

    return ProjectResponse.model_validate(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, session: AsyncSession = Depends(_get_session)):
    """Get a project by ID."""
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: int, session: AsyncSession = Depends(_get_session)):
    """Delete a project."""
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await session.delete(project)


@router.get("/{project_id}/stats", response_model=ProjectStatsResponse)
async def get_project_stats(project_id: int, session: AsyncSession = Depends(_get_session)):
    """Get statistics for a project."""
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Language distribution
    lang_dist = [
        {"language": lang, "count": count, "percentage": 0}
        for lang, count in (project.languages or {}).items()
    ]
    total_files = sum(d["count"] for d in lang_dist) or 1
    for d in lang_dist:
        d["percentage"] = round(d["count"] / total_files * 100, 1)
    lang_dist.sort(key=lambda x: x["count"], reverse=True)

    # Recent commits from DB
    commit_result = await session.execute(
        select(Commit)
        .where(Commit.project_id == project_id)
        .order_by(Commit.date.desc())
        .limit(20)
    )
    recent_commits = [
        {
            "hash": c.hash,
            "author": c.author,
            "date": c.date.isoformat(),
            "message": c.message,
            "insertions": c.insertions,
            "deletions": c.deletions,
            "files_changed": c.files_changed,
        }
        for c in commit_result.scalars().all()
    ]

    return ProjectStatsResponse(
        project=ProjectResponse.model_validate(project),
        language_distribution=lang_dist,
        recent_commits=recent_commits,
    )
