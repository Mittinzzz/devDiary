"""Markdown renderer for diary output."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class MarkdownRenderer:
    """Renders diary content to Markdown files."""

    def __init__(self, output_dir: str | Path = "diaries") -> None:
        self.output_dir = Path(output_dir)

    def render(
        self,
        content: str,
        title: str,
        project_name: str = "",
        date: datetime | None = None,
        style: str = "diary",
        tech_stack: list[str] | None = None,
        metadata: dict | None = None,
    ) -> str:
        """
        Render content to a Markdown string with frontmatter.

        Args:
            content: The main content text (already in Markdown).
            title: Document title.
            project_name: Project name for metadata.
            date: Date for the diary entry.
            style: Writing style used.
            tech_stack: Technology stack tags.
            metadata: Additional metadata.

        Returns:
            Complete Markdown string with frontmatter.
        """
        if date is None:
            date = datetime.now()

        tags = tech_stack or []

        # Build YAML frontmatter
        frontmatter_lines = [
            "---",
            f"title: \"{title}\"",
            f"date: {date.strftime('%Y-%m-%d')}",
            f"project: {project_name}",
            f"style: {style}",
            f"tags: [{', '.join(tags)}]",
        ]

        if metadata:
            for key, value in metadata.items():
                frontmatter_lines.append(f"{key}: {value}")

        frontmatter_lines.append(f"generated_by: DevDiary")
        frontmatter_lines.append("---")
        frontmatter_lines.append("")

        frontmatter = "\n".join(frontmatter_lines)

        return f"{frontmatter}{content}\n"

    def save(
        self,
        content: str,
        title: str,
        project_name: str = "",
        date: datetime | None = None,
        style: str = "diary",
        tech_stack: list[str] | None = None,
        metadata: dict | None = None,
    ) -> Path:
        """
        Render and save content to a Markdown file.

        Returns:
            Path to the saved file.
        """
        if date is None:
            date = datetime.now()

        markdown = self.render(
            content=content,
            title=title,
            project_name=project_name,
            date=date,
            style=style,
            tech_stack=tech_stack,
            metadata=metadata,
        )

        # Organize by date: diaries/2026/03/2026-03-09-diary.md
        date_dir = self.output_dir / date.strftime("%Y") / date.strftime("%m")
        date_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        safe_style = style.replace(" ", "-")
        filename = f"{date.strftime('%Y-%m-%d')}-{safe_style}.md"
        filepath = date_dir / filename

        # Handle duplicate filenames
        counter = 1
        while filepath.exists():
            filename = f"{date.strftime('%Y-%m-%d')}-{safe_style}-{counter}.md"
            filepath = date_dir / filename
            counter += 1

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown)

        logger.info(f"Saved Markdown diary to: {filepath}")
        return filepath
