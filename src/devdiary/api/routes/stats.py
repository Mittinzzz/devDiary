"""Statistics aggregation API routes."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from devdiary.database import get_db_session
from devdiary.models import Project, Commit, Diary
from devdiary.api.schemas import (
    CommitTrendItem,
    CommitTrendResponse,
    HeatmapItem,
    HeatmapResponse,
    InsightsResponse,
)

router = APIRouter(prefix="/api/stats", tags=["stats"])

# Day-of-week names in Chinese (Monday=0 ... Sunday=6)
_DAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


async def _get_session():
    """Dependency to get database session."""
    async with get_db_session() as session:
        yield session


@router.get("/commit-trend", response_model=CommitTrendResponse)
async def get_commit_trend(
    days: int = Query(30, description="Number of days to look back (7/30/90)"),
    session: AsyncSession = Depends(_get_session),
):
    """Get daily commit trend for the specified number of days."""
    now = datetime.now(tz=timezone.utc)
    start_date = (now - timedelta(days=days)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # Query commits in the date range
    result = await session.execute(
        select(Commit).where(Commit.date >= start_date)
    )
    commits = result.scalars().all()

    # Aggregate by date
    daily: dict[str, dict] = {}
    for c in commits:
        date_str = c.date.strftime("%Y-%m-%d")
        if date_str not in daily:
            daily[date_str] = {"commit_count": 0, "insertions": 0, "deletions": 0}
        daily[date_str]["commit_count"] += 1
        daily[date_str]["insertions"] += c.insertions or 0
        daily[date_str]["deletions"] += c.deletions or 0

    # Fill in missing dates with zeros
    items: list[CommitTrendItem] = []
    current = start_date
    while current <= now:
        date_str = current.strftime("%Y-%m-%d")
        if date_str in daily:
            items.append(CommitTrendItem(
                date=date_str,
                commit_count=daily[date_str]["commit_count"],
                insertions=daily[date_str]["insertions"],
                deletions=daily[date_str]["deletions"],
            ))
        else:
            items.append(CommitTrendItem(
                date=date_str,
                commit_count=0,
                insertions=0,
                deletions=0,
            ))
        current += timedelta(days=1)

    return CommitTrendResponse(items=items)


@router.get("/heatmap", response_model=HeatmapResponse)
async def get_heatmap(
    days: int = Query(90, description="Number of days to look back"),
    session: AsyncSession = Depends(_get_session),
):
    """Get commit heatmap data grouped by (hour, day_of_week)."""
    now = datetime.now(tz=timezone.utc)
    start_date = (now - timedelta(days=days)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # Query commits in the date range
    result = await session.execute(
        select(Commit).where(Commit.date >= start_date)
    )
    commits = result.scalars().all()

    # Aggregate by (hour, day_of_week)
    # Python weekday(): Monday=0 ... Sunday=6
    grid: dict[tuple[int, int], int] = defaultdict(int)
    for c in commits:
        hour = c.date.hour
        dow = c.date.weekday()  # 0=Monday, 6=Sunday
        grid[(hour, dow)] += 1

    items: list[HeatmapItem] = [
        HeatmapItem(hour=hour, day_of_week=dow, count=count)
        for (hour, dow), count in sorted(grid.items())
    ]

    return HeatmapResponse(items=items)


@router.get("/insights", response_model=InsightsResponse)
async def get_insights(
    session: AsyncSession = Depends(_get_session),
):
    """Get developer insights based on commit and diary data."""

    # --- Most active hour ---
    result = await session.execute(select(Commit))
    all_commits = result.scalars().all()

    most_active_hour = ""
    most_active_day = ""
    most_active_project = ""
    current_streak = 0

    if all_commits:
        # Count commits by hour
        hour_counts: dict[int, int] = defaultdict(int)
        dow_counts: dict[int, int] = defaultdict(int)
        date_set: set[str] = set()

        for c in all_commits:
            hour_counts[c.date.hour] += 1
            dow_counts[c.date.weekday()] += 1
            date_set.add(c.date.strftime("%Y-%m-%d"))

        # Most active hour
        if hour_counts:
            peak_hour = max(hour_counts, key=hour_counts.get)  # type: ignore[arg-type]
            most_active_hour = f"{peak_hour:02d}:00-{peak_hour + 1:02d}:00"

        # Most active day of week
        if dow_counts:
            peak_dow = max(dow_counts, key=dow_counts.get)  # type: ignore[arg-type]
            most_active_day = _DAY_NAMES[peak_dow]

        # Current streak: count consecutive days with commits going backwards from today
        today = datetime.now(tz=timezone.utc).date()
        streak = 0
        check_date = today
        while True:
            if check_date.strftime("%Y-%m-%d") in date_set:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break
        current_streak = streak

    # --- Most active project ---
    proj_result = await session.execute(
        select(
            Project.name,
            func.count(Commit.id).label("cnt"),
        )
        .join(Commit, Commit.project_id == Project.id)
        .group_by(Project.id)
        .order_by(func.count(Commit.id).desc())
        .limit(1)
    )
    row = proj_result.first()
    if row:
        most_active_project = row[0]

    # --- Total diaries ---
    diary_count_result = await session.execute(select(func.count(Diary.id)))
    total_diaries = diary_count_result.scalar() or 0

    # --- This month commits ---
    now = datetime.now(tz=timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_commits_result = await session.execute(
        select(func.count(Commit.id)).where(Commit.date >= month_start)
    )
    this_month_commits = month_commits_result.scalar() or 0

    return InsightsResponse(
        most_active_hour=most_active_hour,
        most_active_day=most_active_day,
        most_active_project=most_active_project,
        current_streak=current_streak,
        total_diaries=total_diaries,
        this_month_commits=this_month_commits,
    )
