"""Annual/Periodic developer report API routes."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from devdiary.database import get_db_session
from devdiary.models import Project, Commit, Diary

router = APIRouter(prefix="/api/report", tags=["report"])

# Day names
_DAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
_MONTH_NAMES = [
    "1月", "2月", "3月", "4月", "5月", "6月",
    "7月", "8月", "9月", "10月", "11月", "12月",
]


async def _get_session():
    """Dependency to get database session."""
    async with get_db_session() as session:
        yield session


@router.get("")
async def get_annual_report(
    year: Optional[int] = Query(None, description="Year for the report (default: current year)"),
    session: AsyncSession = Depends(_get_session),
):
    """Generate a comprehensive annual developer report (like GitHub Wrapped / Spotify Wrapped)."""
    now = datetime.now(tz=timezone.utc)
    report_year = year or now.year

    year_start = datetime(report_year, 1, 1, tzinfo=timezone.utc)
    year_end = datetime(report_year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

    # ── Fetch all commits and diaries for the year ──
    commit_result = await session.execute(
        select(Commit).where(Commit.date >= year_start, Commit.date <= year_end)
    )
    commits = list(commit_result.scalars().all())

    diary_result = await session.execute(
        select(Diary).where(Diary.created_at >= year_start, Diary.created_at <= year_end)
    )
    diaries = list(diary_result.scalars().all())

    project_result = await session.execute(select(Project))
    projects = list(project_result.scalars().all())

    # ── Basic stats ──
    total_commits = len(commits)
    total_diaries = len(diaries)
    total_insertions = sum(c.insertions or 0 for c in commits)
    total_deletions = sum(c.deletions or 0 for c in commits)
    total_files_changed = sum(c.files_changed or 0 for c in commits)

    # ── Monthly commit trend ──
    monthly_commits: dict[int, int] = defaultdict(int)
    monthly_insertions: dict[int, int] = defaultdict(int)
    monthly_deletions: dict[int, int] = defaultdict(int)
    for c in commits:
        m = c.date.month
        monthly_commits[m] += 1
        monthly_insertions[m] += c.insertions or 0
        monthly_deletions[m] += c.deletions or 0

    monthly_trend = []
    for m in range(1, 13):
        monthly_trend.append({
            "month": _MONTH_NAMES[m - 1],
            "month_num": m,
            "commits": monthly_commits.get(m, 0),
            "insertions": monthly_insertions.get(m, 0),
            "deletions": monthly_deletions.get(m, 0),
        })

    # ── Most productive month ──
    best_month_num = max(monthly_commits, key=monthly_commits.get) if monthly_commits else 1
    best_month = _MONTH_NAMES[best_month_num - 1]
    best_month_commits = monthly_commits.get(best_month_num, 0)

    # ── Busiest day (single date with most commits) ──
    daily_counts: Counter[str] = Counter()
    for c in commits:
        daily_counts[c.date.strftime("%Y-%m-%d")] += 1
    busiest_date = daily_counts.most_common(1)[0] if daily_counts else ("N/A", 0)

    # ── Most active day of week ──
    dow_counts: Counter[int] = Counter()
    for c in commits:
        dow_counts[c.date.weekday()] += 1
    most_active_dow = _DAY_NAMES[dow_counts.most_common(1)[0][0]] if dow_counts else "N/A"

    # ── Peak hour ──
    hour_counts: Counter[int] = Counter()
    for c in commits:
        hour_counts[c.date.hour] += 1
    peak_hour = hour_counts.most_common(1)[0][0] if hour_counts else 0
    peak_hour_str = f"{peak_hour:02d}:00-{peak_hour + 1:02d}:00"

    # ── Longest streak ──
    date_set = set(c.date.strftime("%Y-%m-%d") for c in commits)
    longest_streak = 0
    current_streak = 0
    streak_start = ""
    best_streak_start = ""
    check_date = year_start
    while check_date <= year_end and check_date <= now:
        d_str = check_date.strftime("%Y-%m-%d")
        if d_str in date_set:
            if current_streak == 0:
                streak_start = d_str
            current_streak += 1
            if current_streak > longest_streak:
                longest_streak = current_streak
                best_streak_start = streak_start
        else:
            current_streak = 0
        check_date += timedelta(days=1)

    # ── Project ranking ──
    proj_commits: Counter[int] = Counter()
    for c in commits:
        proj_commits[c.project_id] += 1

    proj_map = {p.id: p.name for p in projects}
    project_ranking = [
        {"name": proj_map.get(pid, f"Project #{pid}"), "commits": cnt}
        for pid, cnt in proj_commits.most_common(10)
    ]

    # ── Language distribution (from all projects) ──
    all_langs: Counter[str] = Counter()
    for p in projects:
        if p.languages:
            for lang, count in p.languages.items():
                all_langs[lang] += count

    total_lang_files = sum(all_langs.values()) or 1
    language_ranking = [
        {"language": lang, "count": cnt, "percentage": round(cnt / total_lang_files * 100, 1)}
        for lang, cnt in all_langs.most_common(10)
    ]

    # ── Tech stack evolution (new languages introduced per month) ──
    monthly_langs: dict[int, set[str]] = defaultdict(set)
    for c in commits:
        if c.file_list:
            for fpath in c.file_list:
                ext = fpath.rsplit(".", 1)[-1].lower() if "." in fpath else ""
                if ext:
                    monthly_langs[c.date.month].add(ext)

    # ── Active days per month (for heatmap summary) ──
    monthly_active_days: dict[int, set[str]] = defaultdict(set)
    for c in commits:
        monthly_active_days[c.date.month].add(c.date.strftime("%Y-%m-%d"))

    active_days_trend = [
        {"month": _MONTH_NAMES[m - 1], "active_days": len(monthly_active_days.get(m, set()))}
        for m in range(1, 13)
    ]

    total_active_days = len(date_set)

    # ── Achievements / Milestones ──
    achievements = []
    if total_commits >= 1000:
        achievements.append({"icon": "🏆", "title": "千次提交", "desc": f"年度提交 {total_commits} 次"})
    elif total_commits >= 500:
        achievements.append({"icon": "🥇", "title": "五百强", "desc": f"年度提交 {total_commits} 次"})
    elif total_commits >= 100:
        achievements.append({"icon": "🥈", "title": "百提交达人", "desc": f"年度提交 {total_commits} 次"})

    if longest_streak >= 30:
        achievements.append({"icon": "🔥", "title": "月度坚持者", "desc": f"连续 {longest_streak} 天提交"})
    elif longest_streak >= 7:
        achievements.append({"icon": "⚡", "title": "周度活跃", "desc": f"连续 {longest_streak} 天提交"})

    if total_insertions >= 100000:
        achievements.append({"icon": "💻", "title": "十万行大佬", "desc": f"年度新增 {total_insertions:,} 行代码"})
    elif total_insertions >= 10000:
        achievements.append({"icon": "⌨️", "title": "万行选手", "desc": f"年度新增 {total_insertions:,} 行代码"})

    if total_diaries >= 50:
        achievements.append({"icon": "📝", "title": "日记达人", "desc": f"生成了 {total_diaries} 篇日记"})
    elif total_diaries >= 10:
        achievements.append({"icon": "📖", "title": "记录者", "desc": f"生成了 {total_diaries} 篇日记"})

    if len(all_langs) >= 5:
        achievements.append({"icon": "🌈", "title": "全栈工程师", "desc": f"使用了 {len(all_langs)} 种语言"})

    if 22 <= peak_hour or peak_hour <= 2:
        achievements.append({"icon": "🌙", "title": "夜猫子", "desc": f"最活跃时间 {peak_hour_str}"})
    elif 5 <= peak_hour <= 8:
        achievements.append({"icon": "🌅", "title": "早起鸟", "desc": f"最活跃时间 {peak_hour_str}"})

    if dow_counts and dow_counts.most_common(1)[0][0] >= 5:
        achievements.append({"icon": "🎮", "title": "周末战士", "desc": f"最爱在{most_active_dow}写代码"})

    # ── Build response ──
    return {
        "year": report_year,
        "generated_at": now.isoformat(),

        # Summary
        "summary": {
            "total_commits": total_commits,
            "total_diaries": total_diaries,
            "total_insertions": total_insertions,
            "total_deletions": total_deletions,
            "total_files_changed": total_files_changed,
            "total_active_days": total_active_days,
            "total_projects": len([p for p in proj_commits if proj_commits[p] > 0]),
        },

        # Highlights
        "highlights": {
            "best_month": best_month,
            "best_month_commits": best_month_commits,
            "busiest_date": busiest_date[0],
            "busiest_date_commits": busiest_date[1],
            "most_active_day": most_active_dow,
            "peak_hour": peak_hour_str,
            "longest_streak": longest_streak,
            "longest_streak_start": best_streak_start,
        },

        # Charts data
        "monthly_trend": monthly_trend,
        "active_days_trend": active_days_trend,
        "project_ranking": project_ranking,
        "language_ranking": language_ranking,

        # Achievements
        "achievements": achievements,
    }
