"""Statistical analysis service for commit data."""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from devdiary.scanner.git_scanner import CommitInfo

logger = logging.getLogger(__name__)


@dataclass
class DailyStats:
    """Statistics for a single day."""

    date: str
    commit_count: int = 0
    insertions: int = 0
    deletions: int = 0
    files_changed: int = 0


@dataclass
class HourlyActivity:
    """Commit activity by hour and day of week."""

    hour: int
    day_of_week: int  # 0=Monday, 6=Sunday
    count: int = 0


@dataclass
class FileHotspot:
    """Most frequently changed files."""

    path: str
    change_count: int = 0
    total_insertions: int = 0
    total_deletions: int = 0


@dataclass
class AnalysisReport:
    """Comprehensive analysis report from commit data."""

    # Summary
    total_commits: int = 0
    total_insertions: int = 0
    total_deletions: int = 0
    total_files_changed: int = 0
    date_from: str = ""
    date_to: str = ""
    active_days: int = 0

    # Distributions
    language_distribution: dict[str, int] = field(default_factory=dict)
    daily_stats: list[DailyStats] = field(default_factory=list)
    hourly_activity: list[HourlyActivity] = field(default_factory=list)
    file_hotspots: list[FileHotspot] = field(default_factory=list)
    author_distribution: dict[str, int] = field(default_factory=dict)

    # Commit message analysis
    commit_types: dict[str, int] = field(default_factory=dict)  # feat/fix/refactor/etc.

    def to_summary_text(self) -> str:
        """Generate a human-readable summary."""
        lines = [
            f"📊 Analysis Report ({self.date_from} ~ {self.date_to})",
            f"",
            f"Total Commits: {self.total_commits}",
            f"Active Days: {self.active_days}",
            f"Code Changes: +{self.total_insertions} / -{self.total_deletions}",
            f"Files Changed: {self.total_files_changed}",
        ]

        if self.language_distribution:
            lines.append("")
            lines.append("Languages:")
            total = sum(self.language_distribution.values())
            for lang, count in sorted(
                self.language_distribution.items(), key=lambda x: x[1], reverse=True
            )[:5]:
                pct = (count / total) * 100
                lines.append(f"  {lang}: {pct:.1f}%")

        if self.commit_types:
            lines.append("")
            lines.append("Commit Types:")
            for ctype, count in sorted(
                self.commit_types.items(), key=lambda x: x[1], reverse=True
            ):
                lines.append(f"  {ctype}: {count}")

        return "\n".join(lines)


class StatsAnalyzer:
    """Analyzes commit data and generates statistical reports."""

    # Common commit type prefixes
    COMMIT_TYPE_PATTERNS: dict[str, list[str]] = {
        "feat": ["feat", "feature", "add", "new"],
        "fix": ["fix", "bugfix", "hotfix", "patch"],
        "refactor": ["refactor", "restructure", "reorganize"],
        "docs": ["docs", "doc", "documentation", "readme"],
        "style": ["style", "format", "formatting", "lint"],
        "test": ["test", "tests", "testing", "spec"],
        "chore": ["chore", "build", "ci", "config", "deps", "dependency"],
        "perf": ["perf", "performance", "optimize", "speed"],
    }

    def analyze(
        self,
        commits: list[CommitInfo],
        language_distribution: dict[str, int] | None = None,
    ) -> AnalysisReport:
        """
        Analyze a list of commits and generate a comprehensive report.

        Args:
            commits: List of CommitInfo objects to analyze.
            language_distribution: Optional pre-computed language distribution.

        Returns:
            AnalysisReport with all computed statistics.
        """
        if not commits:
            return AnalysisReport()

        report = AnalysisReport()

        # Basic stats
        report.total_commits = len(commits)
        report.total_insertions = sum(c.total_insertions for c in commits)
        report.total_deletions = sum(c.total_deletions for c in commits)

        dates = [c.date for c in commits]
        report.date_from = min(dates).strftime("%Y-%m-%d")
        report.date_to = max(dates).strftime("%Y-%m-%d")

        # Count unique files
        all_files: set[str] = set()
        for c in commits:
            for f in c.files:
                all_files.add(f.path)
        report.total_files_changed = len(all_files)

        # Language distribution
        if language_distribution:
            report.language_distribution = language_distribution
        else:
            report.language_distribution = self._compute_language_from_files(commits)

        # Daily stats
        report.daily_stats = self._compute_daily_stats(commits)
        report.active_days = len(report.daily_stats)

        # Hourly activity
        report.hourly_activity = self._compute_hourly_activity(commits)

        # File hotspots
        report.file_hotspots = self._compute_file_hotspots(commits)

        # Author distribution
        report.author_distribution = self._compute_author_distribution(commits)

        # Commit type analysis
        report.commit_types = self._classify_commits(commits)

        return report

    def _compute_daily_stats(self, commits: list[CommitInfo]) -> list[DailyStats]:
        """Compute per-day statistics."""
        daily: dict[str, DailyStats] = {}

        for c in commits:
            date_str = c.date.strftime("%Y-%m-%d")
            if date_str not in daily:
                daily[date_str] = DailyStats(date=date_str)

            day = daily[date_str]
            day.commit_count += 1
            day.insertions += c.total_insertions
            day.deletions += c.total_deletions
            day.files_changed += c.files_changed

        return sorted(daily.values(), key=lambda d: d.date)

    def _compute_hourly_activity(self, commits: list[CommitInfo]) -> list[HourlyActivity]:
        """Compute commit activity by hour and day of week."""
        activity: dict[tuple[int, int], int] = defaultdict(int)

        for c in commits:
            hour = c.date.hour
            dow = c.date.weekday()  # 0=Monday
            activity[(hour, dow)] += 1

        return [
            HourlyActivity(hour=h, day_of_week=d, count=count)
            for (h, d), count in sorted(activity.items())
        ]

    def _compute_file_hotspots(
        self, commits: list[CommitInfo], top_n: int = 10
    ) -> list[FileHotspot]:
        """Find the most frequently changed files."""
        file_stats: dict[str, FileHotspot] = {}

        for c in commits:
            for f in c.files:
                if f.path not in file_stats:
                    file_stats[f.path] = FileHotspot(path=f.path)
                hotspot = file_stats[f.path]
                hotspot.change_count += 1
                hotspot.total_insertions += f.insertions
                hotspot.total_deletions += f.deletions

        sorted_files = sorted(
            file_stats.values(), key=lambda x: x.change_count, reverse=True
        )
        return sorted_files[:top_n]

    def _compute_author_distribution(self, commits: list[CommitInfo]) -> dict[str, int]:
        """Count commits per author."""
        authors: Counter[str] = Counter()
        for c in commits:
            authors[c.author] += 1
        return dict(authors.most_common())

    def _classify_commits(self, commits: list[CommitInfo]) -> dict[str, int]:
        """Classify commits by type based on their message."""
        types: Counter[str] = Counter()

        for c in commits:
            msg_lower = c.first_line.lower()
            classified = False

            for ctype, patterns in self.COMMIT_TYPE_PATTERNS.items():
                for pattern in patterns:
                    if msg_lower.startswith(f"{pattern}:") or msg_lower.startswith(f"{pattern}("):
                        types[ctype] += 1
                        classified = True
                        break
                if classified:
                    break

            if not classified:
                # Try keyword matching
                for ctype, patterns in self.COMMIT_TYPE_PATTERNS.items():
                    if any(pattern in msg_lower for pattern in patterns):
                        types[ctype] += 1
                        classified = True
                        break

            if not classified:
                types["other"] += 1

        return dict(types.most_common())

    def _compute_language_from_files(self, commits: list[CommitInfo]) -> dict[str, int]:
        """Infer language distribution from changed file extensions."""
        from devdiary.scanner.tech_detector import EXTENSION_LANGUAGE_MAP

        languages: Counter[str] = Counter()
        for c in commits:
            for f in c.files:
                ext = "." + f.path.rsplit(".", 1)[-1].lower() if "." in f.path else ""
                lang = EXTENSION_LANGUAGE_MAP.get(ext)
                if lang and lang not in ("Markdown", "JSON", "YAML", "TOML", "XML"):
                    languages[lang] += 1

        return dict(languages.most_common())
