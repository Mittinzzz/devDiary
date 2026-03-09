"""Git watcher service - monitors repositories and auto-generates diaries."""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
import os
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import yaml

from devdiary.config import Config

logger = logging.getLogger(__name__)

# Default watch config file
WATCH_CONFIG_FILE = "watch.yaml"

# Valid schedule modes
SCHEDULE_MODES = ("daily", "weekly", "on_push")


@dataclass
class WatchConfig:
    """Configuration for the watcher service."""

    enabled: bool = True
    schedule: str = "daily"        # daily / weekly / on_push
    time: str = "09:00"            # HH:MM for daily/weekly schedule
    weekday: str = "monday"        # for weekly schedule
    auto_scan: bool = True
    notify_desktop: bool = True
    notify_email: Optional[str] = None
    notify_webhook: Optional[str] = None

    @classmethod
    def load(cls, config_dir: str = ".devdiary") -> WatchConfig:
        """Load watch config from YAML file."""
        watch_path = Path(config_dir) / WATCH_CONFIG_FILE
        if not watch_path.exists():
            return cls()
        with open(watch_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(
            enabled=data.get("enabled", True),
            schedule=data.get("schedule", "daily"),
            time=data.get("time", "09:00"),
            weekday=data.get("weekday", "monday"),
            auto_scan=data.get("auto_scan", True),
            notify_desktop=data.get("notify", {}).get("desktop", True),
            notify_email=data.get("notify", {}).get("email"),
            notify_webhook=data.get("notify", {}).get("webhook"),
        )

    def save(self, config_dir: str = ".devdiary") -> None:
        """Save watch config to YAML file."""
        watch_path = Path(config_dir) / WATCH_CONFIG_FILE
        Path(config_dir).mkdir(parents=True, exist_ok=True)
        data = {
            "enabled": self.enabled,
            "schedule": self.schedule,
            "time": self.time,
            "weekday": self.weekday,
            "auto_scan": self.auto_scan,
            "notify": {
                "desktop": self.notify_desktop,
                "email": self.notify_email,
                "webhook": self.notify_webhook,
            },
        }
        with open(watch_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    def to_dict(self) -> dict:
        """Convert to serializable dict."""
        return {
            "enabled": self.enabled,
            "schedule": self.schedule,
            "time": self.time,
            "weekday": self.weekday,
            "auto_scan": self.auto_scan,
            "notify_desktop": self.notify_desktop,
            "notify_email": self.notify_email,
            "notify_webhook": self.notify_webhook,
        }


@dataclass
class WatcherState:
    """Runtime state of the watcher service."""

    running: bool = False
    last_check: Optional[str] = None
    last_generated: Optional[str] = None
    next_run: Optional[str] = None
    diaries_generated: int = 0
    errors: list[str] = field(default_factory=list)


# Global watcher state (in-memory)
_watcher_state = WatcherState()
_watcher_task: Optional[asyncio.Task] = None  # type: ignore[type-arg]


def get_watcher_state() -> WatcherState:
    """Get current watcher state."""
    return _watcher_state


def _compute_next_run(watch_config: WatchConfig) -> datetime:
    """Compute the next scheduled run time."""
    now = datetime.now(tz=timezone.utc)

    if watch_config.schedule == "on_push":
        # on_push doesn't have scheduled time, check every 5 minutes
        return now + timedelta(minutes=5)

    # Parse time
    try:
        hh, mm = map(int, watch_config.time.split(":"))
    except (ValueError, AttributeError):
        hh, mm = 9, 0

    if watch_config.schedule == "daily":
        next_run = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        return next_run

    elif watch_config.schedule == "weekly":
        weekdays = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6,
        }
        target_dow = weekdays.get(watch_config.weekday.lower(), 0)
        days_ahead = target_dow - now.weekday()
        if days_ahead < 0:
            days_ahead += 7
        next_run = now.replace(hour=hh, minute=mm, second=0, microsecond=0) + timedelta(days=days_ahead)
        if next_run <= now:
            next_run += timedelta(weeks=1)
        return next_run

    return now + timedelta(hours=24)


async def _check_and_generate(config: Config, watch_config: WatchConfig) -> None:
    """Check repositories for new commits and generate diaries if needed."""
    from devdiary.scanner.git_scanner import GitScanner
    from devdiary.database import init_db, get_db_session
    from devdiary.models import Project, Commit
    from sqlalchemy import select, func

    now = datetime.now(tz=timezone.utc)
    _watcher_state.last_check = now.isoformat()

    for repo_cfg in config.repos:
        try:
            scanner = GitScanner(repo_cfg.path)
            if not scanner.validate():
                logger.warning(f"Invalid repository: {repo_cfg.path}")
                continue

            # Determine date range based on schedule
            if watch_config.schedule == "daily":
                date_from = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                date_to = now
                style = config.output.style
            elif watch_config.schedule == "weekly":
                date_from = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
                date_to = now
                style = "report"
            else:  # on_push
                date_from = (now - timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
                date_to = now
                style = config.output.style

            commits = scanner.scan_commits(date_from=date_from, date_to=date_to)

            if not commits:
                logger.info(f"No new commits in {repo_cfg.name}")
                continue

            # Check if we already generated for this period
            async with get_db_session() as session:
                from devdiary.models import Diary
                existing = await session.execute(
                    select(func.count(Diary.id)).where(
                        Diary.date_from >= date_from,
                        Diary.date_to <= date_to,
                        Diary.project_id == (
                            select(Project.id).where(Project.repo_path == repo_cfg.path).scalar_subquery()
                        ),
                    )
                )
                if (existing.scalar() or 0) > 0:
                    logger.info(f"Diary already exists for {repo_cfg.name} in this period")
                    continue

            # Generate diary
            logger.info(f"Generating diary for {repo_cfg.name}: {len(commits)} commits")

            from devdiary.scanner.tech_detector import TechDetector
            from devdiary.analyzer.stats_analyzer import StatsAnalyzer

            file_exts = scanner.get_file_extensions()
            detector = TechDetector(repo_cfg.path)
            tech_stack = detector.detect(file_exts)
            analyzer = StatsAnalyzer()
            report = analyzer.analyze(commits, tech_stack.languages)

            # AI generation
            content = ""
            tokens_used = 0
            ai_provider_name = "none"
            ai_model_name = "fallback"

            if config.ai.api_key:
                try:
                    from devdiary.generator.content_generator import ContentGenerator
                    generator = ContentGenerator.from_config(
                        provider_name=config.ai.provider,
                        api_key=config.ai.api_key,
                        model=config.ai.model,
                        base_url=config.ai.base_url,
                    )
                    result = await generator.generate(
                        commits=commits,
                        project_name=repo_cfg.name,
                        style=style,
                        date_from=date_from,
                        date_to=date_to,
                        tech_stack=tech_stack.to_tags(),
                        analysis=report,
                    )
                    content = result.content
                    tokens_used = result.tokens_used
                    ai_provider_name = result.provider
                    ai_model_name = result.model
                except Exception as e:
                    logger.error(f"AI generation failed: {e}")
                    content = _basic_summary(commits, repo_cfg.name, date_from, date_to)
            else:
                content = _basic_summary(commits, repo_cfg.name, date_from, date_to)

            # Save to database
            async with get_db_session() as session:
                # Get or create project
                proj_result = await session.execute(
                    select(Project).where(Project.repo_path == repo_cfg.path)
                )
                project = proj_result.scalar_one_or_none()
                if not project:
                    project = Project(
                        name=repo_cfg.name,
                        repo_path=repo_cfg.path,
                    )
                    session.add(project)
                    await session.flush()

                period_str = f"{date_from.strftime('%Y-%m-%d')} ~ {date_to.strftime('%Y-%m-%d')}"
                title = f"{repo_cfg.name} - {style.capitalize()} ({period_str})"

                summary_lines = [l.strip() for l in content.split("\n")
                                 if l.strip() and not l.strip().startswith("#")][:2]
                summary = " ".join(summary_lines)[:300]

                from devdiary.models import Diary
                diary = Diary(
                    project_id=project.id,
                    title=title,
                    content=content,
                    summary=summary,
                    style=style,
                    date_from=date_from,
                    date_to=date_to,
                    commit_count=len(commits),
                    insertions=sum(c.total_insertions for c in commits),
                    deletions=sum(c.total_deletions for c in commits),
                    tech_stack=tech_stack.to_tags(),
                    ai_provider=ai_provider_name,
                    ai_model=ai_model_name,
                    tokens_used=tokens_used,
                )
                session.add(diary)

            _watcher_state.diaries_generated += 1
            _watcher_state.last_generated = now.isoformat()
            logger.info(f"✅ Auto-generated diary: {title}")

        except Exception as e:
            error_msg = f"Error processing {repo_cfg.name}: {e}"
            logger.error(error_msg)
            _watcher_state.errors.append(f"[{now.isoformat()}] {error_msg}")
            # Keep only last 20 errors
            if len(_watcher_state.errors) > 20:
                _watcher_state.errors = _watcher_state.errors[-20:]


def _basic_summary(commits: list, project_name: str, date_from: datetime, date_to: datetime) -> str:
    """Generate basic summary without AI."""
    lines = [
        f"# {project_name} - 自动日记",
        f"",
        f"**日期**: {date_from.strftime('%Y-%m-%d')} ~ {date_to.strftime('%Y-%m-%d')}",
        f"**提交数**: {len(commits)}",
        f"",
        "## 提交记录",
        "",
    ]
    for c in commits[:20]:
        lines.append(f"- [{c.date.strftime('%m-%d %H:%M')}] {c.first_line}")
    return "\n".join(lines)


async def run_watcher(config_dir: str = ".devdiary") -> None:
    """Main watcher loop."""
    global _watcher_state

    config = Config.load(config_dir)
    watch_config = WatchConfig.load(config_dir)

    if not watch_config.enabled:
        logger.info("Watcher is disabled in config")
        return

    # Initialize database
    from devdiary.database import init_db
    await init_db()

    _watcher_state.running = True
    logger.info(f"🔍 Watcher started (schedule={watch_config.schedule}, time={watch_config.time})")

    try:
        while _watcher_state.running:
            next_run = _compute_next_run(watch_config)
            _watcher_state.next_run = next_run.isoformat()

            now = datetime.now(tz=timezone.utc)
            wait_seconds = max(0, (next_run - now).total_seconds())

            if watch_config.schedule == "on_push":
                # For on_push, check frequently
                wait_seconds = min(wait_seconds, 300)  # Max 5 min

            logger.info(f"Next check in {wait_seconds:.0f}s ({next_run.strftime('%Y-%m-%d %H:%M')})")
            await asyncio.sleep(wait_seconds)

            # Reload config each cycle (in case user updated it)
            config = Config.load(config_dir)
            watch_config = WatchConfig.load(config_dir)

            if not watch_config.enabled:
                logger.info("Watcher disabled, stopping...")
                break

            await _check_and_generate(config, watch_config)

    except asyncio.CancelledError:
        logger.info("Watcher cancelled")
    finally:
        _watcher_state.running = False
        logger.info("Watcher stopped")


async def start_watcher_background(config_dir: str = ".devdiary") -> None:
    """Start watcher as a background task (for API integration)."""
    global _watcher_task
    if _watcher_task is not None and not _watcher_task.done():
        logger.warning("Watcher already running")
        return
    _watcher_task = asyncio.create_task(run_watcher(config_dir))


async def stop_watcher() -> None:
    """Stop the background watcher task."""
    global _watcher_task, _watcher_state
    _watcher_state.running = False
    if _watcher_task is not None and not _watcher_task.done():
        _watcher_task.cancel()
        try:
            await _watcher_task
        except asyncio.CancelledError:
            pass
    _watcher_task = None
