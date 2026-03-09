"""Content generation service orchestrating scanning, analysis, and AI generation."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Template

from devdiary.generator.ai_provider import AIProvider, GenerationResult, ProviderRegistry
from devdiary.scanner.git_scanner import CommitInfo
from devdiary.analyzer.stats_analyzer import AnalysisReport

logger = logging.getLogger(__name__)

# Prompt template directory
PROMPTS_DIR = Path(__file__).parent / "prompts"

# System prompt for all styles
SYSTEM_PROMPT = """你是 DevDiary，一个智能开发日记助手。你的任务是根据 Git 提交历史生成高质量的开发日记或报告。
你应该：
- 准确理解代码变更的意图和技术含义
- 使用自然流畅的中文表达
- 根据要求的文体风格调整语气和结构
- 输出格式严格使用 Markdown
- 不要编造不存在的信息，只基于提供的数据生成内容
"""

STYLE_MAP = {
    "diary": "diary.txt",
    "blog": "blog.txt",
    "report": "report.txt",
}


class ContentGenerator:
    """Orchestrates the content generation pipeline."""

    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    @classmethod
    def from_config(
        cls,
        provider_name: str,
        api_key: str,
        model: str = "",
        base_url: str | None = None,
        **kwargs: Any,
    ) -> ContentGenerator:
        """Create a ContentGenerator from configuration."""
        # Ensure providers are registered
        import devdiary.generator.providers  # noqa: F401

        provider = ProviderRegistry.get(
            provider_name,
            api_key=api_key,
            model=model,
            base_url=base_url,
            **kwargs,
        )
        return cls(provider)

    async def generate(
        self,
        commits: list[CommitInfo],
        project_name: str = "Unknown Project",
        style: str = "diary",
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        tech_stack: list[str] | None = None,
        analysis: AnalysisReport | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> GenerationResult:
        """
        Generate content from commit data.

        Args:
            commits: List of CommitInfo objects to generate content from.
            project_name: Name of the project.
            style: Writing style ('diary', 'blog', 'report').
            date_from: Start date for the report.
            date_to: End date for the report.
            tech_stack: Detected technology stack tags.
            analysis: Optional pre-computed analysis report.
            temperature: AI generation temperature.
            max_tokens: Max tokens for AI response.

        Returns:
            GenerationResult with the generated content.
        """
        if not commits:
            return GenerationResult(
                content="没有找到指定时间范围内的提交记录。",
                provider=self.provider.name,
                model=self.provider.get_model(),
            )

        # Build the prompt
        prompt = self._build_prompt(
            commits=commits,
            project_name=project_name,
            style=style,
            date_from=date_from,
            date_to=date_to,
            tech_stack=tech_stack,
            analysis=analysis,
        )

        logger.info(f"Generating {style} content for {project_name} with {self.provider.name}...")

        # Call AI
        result = await self.provider.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        logger.info(
            f"Generated {len(result.content)} chars using {result.tokens_used} tokens "
            f"({result.provider}/{result.model})"
        )

        return result

    def _build_prompt(
        self,
        commits: list[CommitInfo],
        project_name: str,
        style: str,
        date_from: datetime | None,
        date_to: datetime | None,
        tech_stack: list[str] | None,
        analysis: AnalysisReport | None,
    ) -> str:
        """Build the full prompt from template and data."""
        # Load template
        template_file = STYLE_MAP.get(style, "diary.txt")
        template_path = PROMPTS_DIR / template_file

        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                template_text = f.read()
        else:
            logger.warning(f"Prompt template not found: {template_path}. Using default.")
            template_text = self._default_template()

        # Prepare template variables
        commits_summary = self._format_commits_summary(commits)

        if date_from is None:
            date_from = min(c.date for c in commits)
        if date_to is None:
            date_to = max(c.date for c in commits)

        total_insertions = sum(c.total_insertions for c in commits)
        total_deletions = sum(c.total_deletions for c in commits)
        files_changed = len(set(f.path for c in commits for f in c.files))

        analysis_summary = ""
        if analysis:
            analysis_summary = analysis.to_summary_text()

        template = Template(template_text)
        return template.render(
            project_name=project_name,
            date_from=date_from.strftime("%Y-%m-%d"),
            date_to=date_to.strftime("%Y-%m-%d"),
            tech_stack=", ".join(tech_stack) if tech_stack else "未检测到",
            commits_summary=commits_summary,
            total_commits=len(commits),
            total_insertions=total_insertions,
            total_deletions=total_deletions,
            files_changed=files_changed,
            analysis_summary=analysis_summary,
        )

    def _format_commits_summary(self, commits: list[CommitInfo], max_commits: int = 50) -> str:
        """Format commit list into a readable summary for the prompt."""
        lines: list[str] = []

        display_commits = commits[:max_commits]
        for c in display_commits:
            date_str = c.date.strftime("%Y-%m-%d %H:%M")
            files_str = f"({c.files_changed} files, +{c.total_insertions}/-{c.total_deletions})"
            lines.append(f"- [{date_str}] {c.first_line} {files_str}")

            # Add notable files
            notable_files = [f for f in c.files if f.total_changes > 20][:3]
            for f in notable_files:
                lines.append(f"  - {f.path}: +{f.insertions}/-{f.deletions} ({f.change_type})")

        if len(commits) > max_commits:
            lines.append(f"\n... 以及另外 {len(commits) - max_commits} 个提交")

        return "\n".join(lines)

    @staticmethod
    def _default_template() -> str:
        """Default prompt template when file templates are unavailable."""
        return """请根据以下 Git 提交记录生成一篇开发日记。

## 项目信息
- 项目名称：{{ project_name }}
- 日期范围：{{ date_from }} ~ {{ date_to }}

## 提交记录
{{ commits_summary }}

## 统计
- 提交数：{{ total_commits }}
- 新增：{{ total_insertions }} 行
- 删除：{{ total_deletions }} 行
- 文件数：{{ files_changed }}

请生成一篇有趣的开发日记：
"""
