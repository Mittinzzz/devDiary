"""Tests for the AI content generator module."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from devdiary.generator.ai_provider import AIProvider, GenerationResult, ProviderRegistry
from devdiary.generator.content_generator import ContentGenerator
from devdiary.scanner.git_scanner import CommitInfo, FileChange


class TestProviderRegistry:
    """Tests for ProviderRegistry."""

    def test_register_and_get(self, mock_provider):
        """Test provider registration and retrieval."""
        assert ProviderRegistry.is_registered("mock")
        provider = ProviderRegistry.get("mock", api_key="test")
        assert provider.name == "mock"

    def test_list_providers(self):
        providers = ProviderRegistry.list_providers()
        assert "mock" in providers

    def test_unknown_provider(self):
        with pytest.raises(ValueError, match="Unknown AI provider"):
            ProviderRegistry.get("nonexistent", api_key="test")


class TestGenerationResult:
    """Tests for GenerationResult."""

    def test_is_empty(self):
        result = GenerationResult(content="")
        assert result.is_empty is True

    def test_not_empty(self):
        result = GenerationResult(content="Hello world")
        assert result.is_empty is False


class TestContentGenerator:
    """Tests for ContentGenerator."""

    @pytest.mark.asyncio
    async def test_generate_with_commits(self, mock_provider, sample_commits):
        """Test content generation with commit data."""
        generator = ContentGenerator(mock_provider)
        result = await generator.generate(
            commits=sample_commits,
            project_name="test-project",
            style="diary",
        )
        assert not result.is_empty
        assert result.provider == "mock"
        assert result.model == "mock-model"

    @pytest.mark.asyncio
    async def test_generate_empty_commits(self, mock_provider):
        """Test generation with no commits returns appropriate message."""
        generator = ContentGenerator(mock_provider)
        result = await generator.generate(
            commits=[],
            project_name="test-project",
        )
        assert "没有找到" in result.content

    @pytest.mark.asyncio
    async def test_generate_from_config(self, sample_commits):
        """Test ContentGenerator.from_config factory."""
        generator = ContentGenerator.from_config(
            provider_name="mock",
            api_key="test-key",
        )
        result = await generator.generate(
            commits=sample_commits,
            project_name="test",
        )
        assert not result.is_empty

    def test_format_commits_summary(self, mock_provider, sample_commits):
        """Test commit summary formatting."""
        generator = ContentGenerator(mock_provider)
        summary = generator._format_commits_summary(sample_commits)
        assert "add user authentication" in summary
        assert "login token expiration" in summary
