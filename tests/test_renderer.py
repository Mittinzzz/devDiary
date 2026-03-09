"""Tests for the renderer module."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from devdiary.renderer.markdown_renderer import MarkdownRenderer
from devdiary.renderer.html_renderer import HtmlRenderer


class TestMarkdownRenderer:
    """Tests for MarkdownRenderer."""

    def test_render_basic(self):
        renderer = MarkdownRenderer()
        result = renderer.render(
            content="# Hello\n\nWorld",
            title="Test Diary",
            project_name="test-project",
            date=datetime(2026, 3, 9),
        )
        assert "---" in result
        assert "title: \"Test Diary\"" in result
        assert "project: test-project" in result
        assert "# Hello" in result

    def test_render_with_tech_stack(self):
        renderer = MarkdownRenderer()
        result = renderer.render(
            content="Content",
            title="Test",
            tech_stack=["Python", "FastAPI"],
        )
        assert "Python" in result
        assert "FastAPI" in result

    def test_save_creates_file(self, temp_dir):
        renderer = MarkdownRenderer(output_dir=str(temp_dir))
        filepath = renderer.save(
            content="# Test Diary",
            title="Test",
            project_name="test",
            date=datetime(2026, 3, 9),
        )
        assert filepath.exists()
        assert filepath.suffix == ".md"
        content = filepath.read_text(encoding="utf-8")
        assert "# Test Diary" in content

    def test_save_organizes_by_date(self, temp_dir):
        renderer = MarkdownRenderer(output_dir=str(temp_dir))
        filepath = renderer.save(
            content="Test",
            title="Test",
            date=datetime(2026, 3, 9),
        )
        # Should be in YYYY/MM subdirectory
        assert "2026" in str(filepath)
        assert "03" in str(filepath)

    def test_save_handles_duplicate(self, temp_dir):
        renderer = MarkdownRenderer(output_dir=str(temp_dir))
        path1 = renderer.save(content="V1", title="T", date=datetime(2026, 3, 9))
        path2 = renderer.save(content="V2", title="T", date=datetime(2026, 3, 9))
        assert path1 != path2
        assert path1.exists()
        assert path2.exists()


class TestHtmlRenderer:
    """Tests for HtmlRenderer."""

    def test_render_basic(self):
        renderer = HtmlRenderer()
        html = renderer.render(
            content="# Hello\n\nWorld",
            title="Test Diary",
            project_name="test",
            date=datetime(2026, 3, 9),
        )
        assert "<html" in html
        assert "Test Diary" in html
        assert "DevDiary" in html

    def test_render_with_code(self):
        renderer = HtmlRenderer()
        html = renderer.render(
            content="```python\nprint('hello')\n```",
            title="Code Test",
        )
        assert "<html" in html
        assert "print" in html

    def test_save_creates_file(self, temp_dir):
        renderer = HtmlRenderer(output_dir=str(temp_dir))
        filepath = renderer.save(
            content="# Test",
            title="Test",
            date=datetime(2026, 3, 9),
        )
        assert filepath.exists()
        assert filepath.suffix == ".html"
