"""Git repository scanner for extracting commit history and diff statistics."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from git import Repo, InvalidGitRepositoryError, NoSuchPathError
from git.diff import Diff

logger = logging.getLogger(__name__)


@dataclass
class FileChange:
    """Represents a single file change in a commit."""

    path: str
    insertions: int = 0
    deletions: int = 0
    change_type: str = "modify"  # add / modify / delete / rename

    @property
    def total_changes(self) -> int:
        return self.insertions + self.deletions


@dataclass
class CommitInfo:
    """Structured information extracted from a Git commit."""

    hash: str
    author: str
    email: str
    date: datetime
    message: str
    files: list[FileChange] = field(default_factory=list)
    total_insertions: int = 0
    total_deletions: int = 0

    @property
    def files_changed(self) -> int:
        return len(self.files)

    @property
    def short_hash(self) -> str:
        return self.hash[:8]

    @property
    def first_line(self) -> str:
        """Get the first line of the commit message."""
        return self.message.split("\n")[0].strip()


class GitScanner:
    """Scans a Git repository and extracts commit information."""

    def __init__(self, repo_path: str | Path) -> None:
        self.repo_path = Path(repo_path).resolve()
        self._repo: Repo | None = None

    @property
    def repo(self) -> Repo:
        """Lazily initialize and return the Git repository."""
        if self._repo is None:
            try:
                self._repo = Repo(self.repo_path)
            except InvalidGitRepositoryError:
                raise ValueError(f"'{self.repo_path}' is not a valid Git repository.")
            except NoSuchPathError:
                raise ValueError(f"Path '{self.repo_path}' does not exist.")
        return self._repo

    @property
    def repo_name(self) -> str:
        """Get the repository name from its path."""
        return self.repo_path.name

    def validate(self) -> bool:
        """Check if the repository path is valid."""
        try:
            _ = self.repo
            return True
        except ValueError:
            return False

    def scan_commits(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        branch: str | None = None,
        max_count: int | None = None,
    ) -> list[CommitInfo]:
        """
        Scan commits within an optional date range.

        Args:
            date_from: Start date (inclusive). If None, no lower bound.
            date_to: End date (inclusive). If None, no upper bound.
            branch: Branch to scan. If None, uses current active branch.
            max_count: Maximum number of commits to return.

        Returns:
            List of CommitInfo objects, sorted by date descending.
        """
        commits: list[CommitInfo] = []

        kwargs: dict = {}
        if max_count:
            kwargs["max_count"] = max_count
        if date_from:
            kwargs["after"] = date_from.strftime("%Y-%m-%d")
        if date_to:
            kwargs["before"] = (date_to.strftime("%Y-%m-%d %H:%M:%S")
                                if date_to.hour or date_to.minute
                                else date_to.strftime("%Y-%m-%d 23:59:59"))

        try:
            rev = branch or self.repo.active_branch.name
        except TypeError:
            # Detached HEAD
            rev = "HEAD"

        try:
            for commit in self.repo.iter_commits(rev, **kwargs):
                commit_date = datetime.fromtimestamp(
                    commit.committed_date, tz=timezone.utc
                )

                # Apply date filtering (belt and suspenders)
                if date_from and commit_date < date_from.replace(tzinfo=timezone.utc):
                    continue
                if date_to and commit_date > date_to.replace(tzinfo=timezone.utc):
                    continue

                commit_info = self._extract_commit_info(commit, commit_date)
                commits.append(commit_info)

        except Exception as e:
            logger.warning(f"Error scanning commits: {e}")

        return commits

    def _extract_commit_info(self, commit: object, commit_date: datetime) -> CommitInfo:
        """Extract structured information from a single commit."""
        files: list[FileChange] = []
        total_insertions = 0
        total_deletions = 0

        try:
            # Get diff stats
            if commit.parents:  # type: ignore
                diffs = commit.parents[0].diff(commit, create_patch=False)  # type: ignore
            else:
                # Initial commit - diff against empty tree
                diffs = commit.diff(None, create_patch=False)  # type: ignore

            # Get stats
            stats = commit.stats  # type: ignore
            total_insertions = stats.total.get("insertions", 0)
            total_deletions = stats.total.get("deletions", 0)

            for file_path, file_stats in stats.files.items():
                change_type = "modify"
                # Try to determine change type from diff
                for diff in diffs:
                    diff_path = diff.b_path or diff.a_path
                    if diff_path == file_path:
                        if diff.new_file:
                            change_type = "add"
                        elif diff.deleted_file:
                            change_type = "delete"
                        elif diff.renamed_file:
                            change_type = "rename"
                        break

                files.append(
                    FileChange(
                        path=file_path,
                        insertions=file_stats.get("insertions", 0),
                        deletions=file_stats.get("deletions", 0),
                        change_type=change_type,
                    )
                )

        except Exception as e:
            logger.debug(f"Error extracting diff stats for {commit}: {e}")  # type: ignore

        return CommitInfo(
            hash=str(commit.hexsha),  # type: ignore
            author=str(commit.author),  # type: ignore
            email=str(commit.author.email) if hasattr(commit.author, "email") else "",  # type: ignore
            date=commit_date,
            message=str(commit.message).strip(),  # type: ignore
            files=files,
            total_insertions=total_insertions,
            total_deletions=total_deletions,
        )

    def get_branches(self) -> list[str]:
        """Get all local branch names."""
        return [b.name for b in self.repo.branches]  # type: ignore

    def get_current_branch(self) -> str:
        """Get the current active branch name."""
        try:
            return self.repo.active_branch.name
        except TypeError:
            return "HEAD (detached)"

    def get_file_extensions(self) -> dict[str, int]:
        """
        Get distribution of file extensions in the repository.

        Returns:
            Dict mapping extension (e.g. '.py') to file count.
        """
        extensions: dict[str, int] = {}
        try:
            for item in self.repo.tree().traverse():
                if item.type == "blob":  # type: ignore
                    ext = Path(item.path).suffix.lower()  # type: ignore
                    if ext:
                        extensions[ext] = extensions.get(ext, 0) + 1
        except Exception as e:
            logger.debug(f"Error scanning file extensions: {e}")
        return extensions
