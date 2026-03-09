"""Diary management API routes."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import Response
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from devdiary.database import get_db_session
from devdiary.models import Project, Commit, Diary
from devdiary.api.schemas import (
    DiaryResponse,
    DiaryListResponse,
    DiaryUpdate,
    BatchDeleteRequest,
    BatchDeleteResponse,
    GenerateRequest,
    GenerateResponse,
    StatsOverviewResponse,
    ExportResponse,
)

router = APIRouter(prefix="/api/diaries", tags=["diaries"])


async def _get_session():
    """Dependency to get database session."""
    async with get_db_session() as session:
        yield session


def _diary_to_response(diary: Diary) -> DiaryResponse:
    """Convert Diary model to response schema."""
    return DiaryResponse(
        id=diary.id,
        title=diary.title,
        content=diary.content,
        summary=diary.summary,
        style=diary.style,
        date_from=diary.date_from,
        date_to=diary.date_to,
        project_id=diary.project_id,
        project_name=diary.project.name if diary.project else "",
        commit_count=diary.commit_count,
        insertions=diary.insertions,
        deletions=diary.deletions,
        tech_stack=diary.tech_stack or [],
        ai_provider=diary.ai_provider,
        ai_model=diary.ai_model,
        tokens_used=diary.tokens_used,
        created_at=diary.created_at,
    )


@router.get("", response_model=DiaryListResponse)
async def list_diaries(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    style: Optional[str] = Query(None, description="Filter by style"),
    project_id: Optional[int] = Query(None, description="Filter by project"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Search keyword"),
    session: AsyncSession = Depends(_get_session),
):
    """Get paginated list of diaries with optional filters."""
    query = select(Diary).options(joinedload(Diary.project))
    count_query = select(func.count(Diary.id))

    # Apply filters
    filters = []
    if style:
        filters.append(Diary.style == style)
    if project_id:
        filters.append(Diary.project_id == project_id)
    if date_from:
        try:
            dt_from = datetime.strptime(date_from, "%Y-%m-%d")
            filters.append(Diary.date_from >= dt_from)
        except ValueError:
            pass
    if date_to:
        try:
            dt_to = datetime.strptime(date_to, "%Y-%m-%d")
            filters.append(Diary.date_to <= dt_to)
        except ValueError:
            pass
    if search:
        filters.append(Diary.title.ilike(f"%{search}%") | Diary.content.ilike(f"%{search}%"))

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    # Count total
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(Diary.created_at.desc()).offset(offset).limit(page_size)
    result = await session.execute(query)
    diaries = result.scalars().unique().all()

    return DiaryListResponse(
        items=[_diary_to_response(d) for d in diaries],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/overview", response_model=StatsOverviewResponse)
async def get_overview(session: AsyncSession = Depends(_get_session)):
    """Get dashboard overview statistics."""
    # Total counts
    diary_count = (await session.execute(select(func.count(Diary.id)))).scalar() or 0
    project_count = (await session.execute(select(func.count(Project.id)))).scalar() or 0
    commit_count = (await session.execute(select(func.count(Commit.id)))).scalar() or 0

    # Totals
    ins_result = await session.execute(select(func.sum(Diary.insertions)))
    total_insertions = ins_result.scalar() or 0
    del_result = await session.execute(select(func.sum(Diary.deletions)))
    total_deletions = del_result.scalar() or 0

    # This week stats
    now = datetime.now(tz=timezone.utc)
    week_start = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    week_diaries = (
        await session.execute(
            select(func.count(Diary.id)).where(Diary.created_at >= week_start)
        )
    ).scalar() or 0

    week_commits = (
        await session.execute(
            select(func.count(Commit.id)).where(Commit.date >= week_start)
        )
    ).scalar() or 0

    # Recent diaries
    recent_result = await session.execute(
        select(Diary)
        .options(joinedload(Diary.project))
        .order_by(Diary.created_at.desc())
        .limit(5)
    )
    recent = recent_result.scalars().unique().all()

    return StatsOverviewResponse(
        total_diaries=diary_count,
        total_commits=commit_count,
        total_projects=project_count,
        total_insertions=total_insertions,
        total_deletions=total_deletions,
        this_week_diaries=week_diaries,
        this_week_commits=week_commits,
        recent_diaries=[_diary_to_response(d) for d in recent],
    )


@router.post("/batch-delete", response_model=BatchDeleteResponse)
async def batch_delete_diaries(
    request: BatchDeleteRequest,
    session: AsyncSession = Depends(_get_session),
):
    """Batch delete diary entries by IDs."""
    result = await session.execute(
        select(Diary).where(Diary.id.in_(request.ids))
    )
    diaries = result.scalars().all()

    deleted_count = len(diaries)
    for diary in diaries:
        await session.delete(diary)

    return BatchDeleteResponse(deleted_count=deleted_count)


@router.get("/{diary_id}", response_model=DiaryResponse)
async def get_diary(diary_id: int, session: AsyncSession = Depends(_get_session)):
    """Get a single diary by ID."""
    result = await session.execute(
        select(Diary).options(joinedload(Diary.project)).where(Diary.id == diary_id)
    )
    diary = result.scalar_one_or_none()
    if not diary:
        raise HTTPException(status_code=404, detail="Diary not found")
    return _diary_to_response(diary)


@router.put("/{diary_id}", response_model=DiaryResponse)
async def update_diary(
    diary_id: int,
    data: DiaryUpdate,
    session: AsyncSession = Depends(_get_session),
):
    """Update a diary entry. Only non-None fields will be updated."""
    result = await session.execute(
        select(Diary).options(joinedload(Diary.project)).where(Diary.id == diary_id)
    )
    diary = result.scalar_one_or_none()
    if not diary:
        raise HTTPException(status_code=404, detail="日记不存在")

    # Only update fields that are explicitly provided (not None)
    update_data = data.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="未提供任何需要更新的字段")

    for field_name, value in update_data.items():
        setattr(diary, field_name, value)

    await session.flush()
    await session.refresh(diary)
    return _diary_to_response(diary)


@router.post("/generate", response_model=GenerateResponse)
async def generate_diary(
    request: GenerateRequest,
    session: AsyncSession = Depends(_get_session),
):
    """Generate a new diary for a project."""
    # Get project
    proj_result = await session.execute(
        select(Project).where(Project.id == request.project_id)
    )
    project = proj_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在，请先添加项目")

    # Parse dates
    now = datetime.now(tz=timezone.utc)
    if request.date_from:
        try:
            date_from = datetime.strptime(request.date_from, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            raise HTTPException(status_code=400, detail="起始日期格式错误，请使用 YYYY-MM-DD 格式")
    else:
        date_from = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if request.date_to:
        try:
            date_to = datetime.strptime(request.date_to, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, tzinfo=timezone.utc
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="结束日期格式错误，请使用 YYYY-MM-DD 格式")
    else:
        date_to = now

    # Scan commits
    from devdiary.scanner.git_scanner import GitScanner
    from devdiary.scanner.tech_detector import TechDetector
    from devdiary.analyzer.stats_analyzer import StatsAnalyzer
    from devdiary.config import Config

    try:
        scanner = GitScanner(project.repo_path)
        commits = scanner.scan_commits(date_from=date_from, date_to=date_to)
        file_exts = scanner.get_file_extensions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"扫描 Git 仓库失败: {e}")

    if not commits:
        raise HTTPException(
            status_code=422,
            detail=f"在 {date_from.strftime('%Y-%m-%d')} ~ {date_to.strftime('%Y-%m-%d')} 期间没有找到任何提交记录，请确认日期范围是否正确",
        )

    # Analyze
    detector = TechDetector(project.repo_path)
    tech_stack = detector.detect(file_exts)
    analyzer = StatsAnalyzer()
    report = analyzer.analyze(commits, tech_stack.languages)

    # Generate content
    config = Config.load()
    total_insertions = sum(c.total_insertions for c in commits)
    total_deletions = sum(c.total_deletions for c in commits)

    if config.ai.api_key:
        from devdiary.generator.content_generator import ContentGenerator
        generator = ContentGenerator.from_config(
            provider_name=config.ai.provider,
            api_key=config.ai.api_key,
            model=config.ai.model,
            base_url=config.ai.base_url,
        )
        result = await generator.generate(
            commits=commits,
            project_name=project.name,
            style=request.style,
            date_from=date_from,
            date_to=date_to,
            tech_stack=tech_stack.to_tags(),
            analysis=report,
        )
        content = result.content
        tokens_used = result.tokens_used
        ai_provider = result.provider
        ai_model = result.model
    else:
        # Fallback: basic summary
        content = _generate_basic_summary(commits, project.name, date_from, date_to, tech_stack.to_tags())
        tokens_used = 0
        ai_provider = "none"
        ai_model = "fallback"

    # Create title
    period_str = date_from.strftime("%Y-%m-%d")
    if date_from.date() != date_to.date():
        period_str += f" ~ {date_to.strftime('%Y-%m-%d')}"
    title = f"{project.name} - {request.style.capitalize()} ({period_str})"

    # Extract summary (first paragraph)
    summary_lines = []
    for line in content.split("\n"):
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("---"):
            summary_lines.append(line)
            if len(summary_lines) >= 2:
                break
    summary = " ".join(summary_lines)[:300]

    # Save to database
    diary = Diary(
        project_id=project.id,
        title=title,
        content=content,
        summary=summary,
        style=request.style,
        date_from=date_from,
        date_to=date_to,
        commit_count=len(commits),
        insertions=total_insertions,
        deletions=total_deletions,
        tech_stack=tech_stack.to_tags(),
        ai_provider=ai_provider,
        ai_model=ai_model,
        tokens_used=tokens_used,
    )
    session.add(diary)
    await session.flush()
    await session.refresh(diary)

    # Cache commits
    for c in commits:
        db_commit = Commit(
            project_id=project.id,
            hash=c.hash,
            author=c.author,
            email=c.email,
            message=c.message,
            date=c.date,
            insertions=c.total_insertions,
            deletions=c.total_deletions,
            files_changed=c.files_changed,
            file_list=[f.path for f in c.files],
        )
        session.add(db_commit)

    # Update project
    project.last_scanned = now
    project.total_commits = (project.total_commits or 0) + len(commits)
    project.languages = tech_stack.languages

    # Save files
    saved_files: list[str] = []
    if request.output_format in ("markdown", "both"):
        from devdiary.renderer.markdown_renderer import MarkdownRenderer
        md_renderer = MarkdownRenderer(config.output.dir)
        md_path = md_renderer.save(
            content=content, title=title, project_name=project.name,
            date=date_from, style=request.style, tech_stack=tech_stack.to_tags(),
        )
        saved_files.append(str(md_path))

    if request.output_format in ("html", "both"):
        from devdiary.renderer.html_renderer import HtmlRenderer
        html_renderer = HtmlRenderer(config.output.dir)
        html_path = html_renderer.save(
            content=content, title=title, project_name=project.name,
            date=date_from, style=request.style, tech_stack=tech_stack.to_tags(),
        )
        saved_files.append(str(html_path))

    # Build response with project name
    diary_response = _diary_to_response(diary)
    diary_response.project_name = project.name

    return GenerateResponse(
        diary=diary_response,
        files_saved=saved_files,
        tokens_used=tokens_used,
        message=f"Diary generated successfully with {len(commits)} commits analyzed",
    )


@router.get("/{diary_id}/export")
async def export_diary(
    diary_id: int,
    format: str = Query("markdown", description="Export format: markdown/html"),
    session: AsyncSession = Depends(_get_session),
):
    """Export a diary in specified format."""
    result = await session.execute(
        select(Diary).options(joinedload(Diary.project)).where(Diary.id == diary_id)
    )
    diary = result.scalar_one_or_none()
    if not diary:
        raise HTTPException(status_code=404, detail="Diary not found")

    project_name = diary.project.name if diary.project else "unknown"

    if format == "html":
        from devdiary.renderer.html_renderer import HtmlRenderer
        renderer = HtmlRenderer()
        content = renderer.render(
            content=diary.content,
            title=diary.title,
            project_name=project_name,
            date=diary.date_from,
            style=diary.style,
            tech_stack=diary.tech_stack or [],
        )
        return Response(
            content=content,
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="{diary.title}.html"'},
        )
    else:
        from devdiary.renderer.markdown_renderer import MarkdownRenderer
        renderer_md = MarkdownRenderer()
        content = renderer_md.render(
            content=diary.content,
            title=diary.title,
            project_name=project_name,
            date=diary.date_from,
            style=diary.style,
            tech_stack=diary.tech_stack or [],
        )
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{diary.title}.md"'},
        )


@router.delete("/{diary_id}", status_code=204)
async def delete_diary(diary_id: int, session: AsyncSession = Depends(_get_session)):
    """Delete a diary entry."""
    result = await session.execute(select(Diary).where(Diary.id == diary_id))
    diary = result.scalar_one_or_none()
    if not diary:
        raise HTTPException(status_code=404, detail="Diary not found")
    await session.delete(diary)


def _generate_basic_summary(
    commits: list,
    project_name: str,
    date_from: datetime,
    date_to: datetime,
    tech_tags: list[str],
) -> str:
    """Generate basic summary without AI."""
    lines = [
        f"# {project_name} Development Summary",
        f"",
        f"**Period**: {date_from.strftime('%Y-%m-%d')} ~ {date_to.strftime('%Y-%m-%d')}",
        f"**Tech Stack**: {', '.join(tech_tags) if tech_tags else 'N/A'}",
        f"",
        f"## Commits ({len(commits)})",
        f"",
    ]
    for c in commits[:30]:
        lines.append(f"- [{c.date.strftime('%m-%d %H:%M')}] {c.first_line}")
    if len(commits) > 30:
        lines.append(f"- ... and {len(commits) - 30} more")
    lines.extend([
        f"",
        f"## Stats",
        f"- Insertions: +{sum(c.total_insertions for c in commits)}",
        f"- Deletions: -{sum(c.total_deletions for c in commits)}",
        f"",
        f"> Configure an AI API key for AI-generated content.",
    ])
    return "\n".join(lines)
