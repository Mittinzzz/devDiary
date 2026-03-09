"""Tests for the Git scanner module."""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from devdiary.scanner.git_scanner import GitScanner, CommitInfo, FileChange
from devdiary.scanner.tech_detector import TechDetector, TechStack


class TestFileChange:
    """Tests for FileChange dataclass."""

    def test_total_changes(self):
        fc = FileChange(path="test.py", insertions=10, deletions=5)
        assert fc.total_changes == 15

    def test_default_change_type(self):
        fc = FileChange(path="test.py")
        assert fc.change_type == "modify"


class TestCommitInfo:
    """Tests for CommitInfo dataclass."""

    def test_files_changed(self):
        commit = CommitInfo(
            hash="abc123",
            author="dev",
            email="dev@test.com",
            date=datetime.now(tz=timezone.utc),
            message="test commit",
            files=[
                FileChange(path="a.py"),
                FileChange(path="b.py"),
            ],
        )
        assert commit.files_changed == 2

    def test_short_hash(self):
        commit = CommitInfo(
            hash="abc123def456789",
            author="dev",
            email="",
            date=datetime.now(tz=timezone.utc),
            message="test",
        )
        assert commit.short_hash == "abc123de"

    def test_first_line(self):
        commit = CommitInfo(
            hash="abc",
            author="dev",
            email="",
            date=datetime.now(tz=timezone.utc),
            message="feat: add feature\n\nDetailed description here",
        )
        assert commit.first_line == "feat: add feature"


class TestGitScanner:
    """Tests for GitScanner."""

    def test_invalid_repo_path(self):
        scanner = GitScanner("/nonexistent/path")
        assert scanner.validate() is False

    def test_scan_empty_commits(self):
        """Test scanning with no commits in range returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize a bare git repo
            from git import Repo
            repo = Repo.init(tmpdir)

            scanner = GitScanner(tmpdir)
            # Scan future dates (should be empty)
            future = datetime(2099, 1, 1, tzinfo=timezone.utc)
            commits = scanner.scan_commits(date_from=future)
            assert commits == []


class TestTechDetector:
    """Tests for TechDetector."""

    def test_detect_from_extensions(self):
        detector = TechDetector("/tmp")
        extensions = {".py": 50, ".js": 30, ".ts": 20}
        tech = detector.detect(file_extensions=extensions)

        assert "Python" in tech.languages
        assert tech.languages["Python"] == 50
        assert "JavaScript" in tech.languages

    def test_primary_language(self):
        tech = TechStack(languages={"Python": 100, "JavaScript": 50})
        assert tech.primary_language == "Python"

    def test_empty_languages(self):
        tech = TechStack()
        assert tech.primary_language is None

    def test_language_percentages(self):
        tech = TechStack(languages={"Python": 75, "JavaScript": 25})
        pcts = tech.language_percentages
        assert pcts["Python"] == 75.0
        assert pcts["JavaScript"] == 25.0

    def test_to_tags(self):
        tech = TechStack(
            languages={"Python": 100, "JavaScript": 50},
            frameworks=["FastAPI", "Vue.js"],
        )
        tags = tech.to_tags()
        assert "Python" in tags
        assert "FastAPI" in tags
