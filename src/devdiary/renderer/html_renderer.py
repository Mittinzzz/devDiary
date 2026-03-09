"""HTML renderer for diary output."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pygments.formatters import HtmlFormatter

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"


class HtmlRenderer:
    """Renders diary content to standalone HTML pages."""

    def __init__(self, output_dir: str | Path = "diaries") -> None:
        self.output_dir = Path(output_dir)
        self._env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(["html"]),
        )

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
        Render Markdown content to a standalone HTML page.

        Args:
            content: The main content text in Markdown.
            title: Document title.
            project_name: Project name.
            date: Date for the diary entry.
            style: Writing style used.
            tech_stack: Technology stack tags.
            metadata: Additional metadata.

        Returns:
            Complete HTML string.
        """
        if date is None:
            date = datetime.now()

        # Convert Markdown to HTML
        md = markdown.Markdown(
            extensions=["fenced_code", "tables", "codehilite", "toc", "nl2br"],
            extension_configs={
                "codehilite": {
                    "css_class": "highlight",
                    "guess_lang": True,
                    "linenums": False,
                },
            },
        )
        html_content = md.convert(content)

        # Get Pygments CSS for code highlighting
        pygments_css = HtmlFormatter(style="monokai").get_style_defs(".highlight")

        # Render template
        try:
            template = self._env.get_template("diary.html")
        except Exception:
            logger.warning("diary.html template not found, using inline template")
            template = Environment(autoescape=True).from_string(self._inline_template())

        return template.render(
            title=title,
            project_name=project_name,
            date=date.strftime("%Y-%m-%d"),
            style=style,
            tech_stack=tech_stack or [],
            content=html_content,
            pygments_css=pygments_css,
            metadata=metadata or {},
            year=date.year,
        )

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
        Render and save content to an HTML file.

        Returns:
            Path to the saved file.
        """
        if date is None:
            date = datetime.now()

        html = self.render(
            content=content,
            title=title,
            project_name=project_name,
            date=date,
            style=style,
            tech_stack=tech_stack,
            metadata=metadata,
        )

        # Organize by date
        date_dir = self.output_dir / date.strftime("%Y") / date.strftime("%m")
        date_dir.mkdir(parents=True, exist_ok=True)

        safe_style = style.replace(" ", "-")
        filename = f"{date.strftime('%Y-%m-%d')}-{safe_style}.html"
        filepath = date_dir / filename

        counter = 1
        while filepath.exists():
            filename = f"{date.strftime('%Y-%m-%d')}-{safe_style}-{counter}.html"
            filepath = date_dir / filename
            counter += 1

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(f"Saved HTML diary to: {filepath}")
        return filepath

    @staticmethod
    def _inline_template() -> str:
        """Fallback inline HTML template."""
        return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - DevDiary</title>
    <style>
        {{ pygments_css }}
        body { font-family: system-ui; max-width: 800px; margin: 0 auto; padding: 2rem; background: #0f172a; color: #f8fafc; }
        h1, h2, h3 { color: #a78bfa; }
        a { color: #6366f1; }
        code { background: #1e293b; padding: 0.2em 0.4em; border-radius: 3px; }
        pre { background: #1e293b; padding: 1rem; border-radius: 8px; overflow-x: auto; }
        .tag { display: inline-block; padding: 2px 8px; margin: 2px; background: rgba(99,102,241,0.15); color: #a78bfa; border-radius: 12px; font-size: 0.8em; }
    </style>
</head>
<body>
    <header>
        <h1>{{ title }}</h1>
        <p>{{ project_name }} | {{ date }} | {{ style }}</p>
        <div>{% for tag in tech_stack %}<span class="tag">{{ tag }}</span>{% endfor %}</div>
    </header>
    <main>{{ content }}</main>
    <footer><p>Generated by DevDiary &copy; {{ year }}</p></footer>
</body>
</html>"""
