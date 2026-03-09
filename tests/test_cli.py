"""Tests for the CLI module."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from devdiary.cli.main import cli


@pytest.fixture
def runner():
    return CliRunner()


class TestCLI:
    """Tests for CLI commands."""

    def test_version(self, runner):
        """Test --version flag."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "DevDiary" in result.output

    def test_help(self, runner):
        """Test --help flag."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "DevDiary" in result.output
        assert "init" in result.output
        assert "today" in result.output
        assert "week" in result.output
        assert "month" in result.output

    def test_init_help(self, runner):
        """Test init --help."""
        result = runner.invoke(cli, ["init", "--help"])
        assert result.exit_code == 0
        assert "Initialize" in result.output

    def test_today_no_config(self, runner):
        """Test today command without config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(cli, ["today", "--config-dir", f"{tmpdir}/.devdiary"])
            # Should fail gracefully - config not found
            assert result.exit_code != 0 or "not initialized" in result.output.lower() or "❌" in result.output

    def test_week_help(self, runner):
        """Test week --help."""
        result = runner.invoke(cli, ["week", "--help"])
        assert result.exit_code == 0

    def test_month_help(self, runner):
        """Test month --help."""
        result = runner.invoke(cli, ["month", "--help"])
        assert result.exit_code == 0
