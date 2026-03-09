"""DevDiary CLI - Command line interface for generating dev diaries."""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text
from rich import print as rprint

from devdiary import __version__
from devdiary.config import Config, RepoConfig, AIConfig

# Fix Windows terminal encoding for emoji/unicode support
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore
    except (AttributeError, OSError):
        pass

console = Console(force_terminal=True)


def _banner() -> None:
    """Print the DevDiary banner."""
    banner = Text()
    banner.append("╔═══════════════════════════════════════╗\n", style="bold blue")
    banner.append("║  ", style="bold blue")
    banner.append("📝 DevDiary", style="bold magenta")
    banner.append("  v" + __version__, style="dim")
    banner.append("              ║\n", style="bold blue")
    banner.append("║  ", style="bold blue")
    banner.append("Your Second Brain for Development", style="italic cyan")
    banner.append("  ║\n", style="bold blue")
    banner.append("╚═══════════════════════════════════════╝", style="bold blue")
    console.print(banner)
    console.print()


def _run_async(coro):  # type: ignore
    """Run an async coroutine synchronously."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@click.group()
@click.version_option(version=__version__, prog_name="DevDiary")
def cli() -> None:
    """📝 DevDiary - Automatically generate dev diaries from Git history with AI."""
    pass


@cli.command()
@click.option("--config-dir", default=".devdiary", help="Configuration directory path")
@click.option("--yes", "-y", is_flag=True, default=False, help="Skip interactive prompts, use existing config as-is")
def init(config_dir: str, yes: bool) -> None:
    """🚀 Initialize DevDiary configuration for your project."""
    _banner()

    # Load existing config if present, otherwise create new
    existing = Config.load(config_dir)
    has_existing = existing.config_path.exists()

    if has_existing and yes:
        # Non-interactive mode: just validate and exit
        console.print(f"[green]✅ Configuration already exists at [bold]{existing.config_path}[/bold][/green]\n")
        _display_config_summary(existing)
        console.print(
            Panel(
                f"Try generating your diary:\n"
                f"  [cyan]devdiary today[/cyan]\n\n"
                f"To reconfigure interactively, run:\n"
                f"  [cyan]devdiary init[/cyan]  (without --yes)",
                title="Configuration OK",
                border_style="green",
            )
        )
        return

    if has_existing:
        console.print(f"[yellow]Found existing config at [bold]{existing.config_path}[/bold][/yellow]")
        console.print("[dim]Existing values shown as defaults — press Enter to keep them.[/dim]\n")
        config = existing
    else:
        console.print("[bold green]Initializing DevDiary...[/bold green]\n")
        config = Config(config_dir=config_dir)

    # AI Provider selection
    console.print("[bold]Step 1: Configure AI Provider[/bold]")
    provider = Prompt.ask(
        "  Select AI provider",
        choices=["openai", "deepseek", "zhipu", "gongfeng"],
        default=config.ai.provider or "openai",
    )
    config.ai.provider = provider

    # Show masked existing key as hint
    existing_key_hint = ""
    if config.ai.api_key:
        key = config.ai.api_key
        existing_key_hint = f" [dim](current: {key[:6]}...{key[-4:]})[/dim]"
    console.print(f"  Enter {provider} API key{existing_key_hint}")
    new_key = Prompt.ask("  API key", password=True, default="")
    if new_key:
        config.ai.api_key = new_key
    # If user pressed Enter with empty input, keep existing key

    model_defaults = {
        "openai": "gpt-4o-mini",
        "deepseek": "deepseek-chat",
        "zhipu": "glm-4-flash",
        "gongfeng": "gongfeng-chat",
    }
    current_model = config.ai.model or model_defaults.get(provider, "")
    model = Prompt.ask("  Model name", default=current_model)
    config.ai.model = model

    current_base_url = config.ai.base_url or ""
    base_url = Prompt.ask("  Custom API base URL (leave empty for default)", default=current_base_url)
    config.ai.base_url = base_url or None

    console.print()

    # Repository configuration
    console.print("[bold]Step 2: Add Git Repository[/bold]")
    current_repo_path = config.repos[0].path if config.repos else str(Path.cwd())
    repo_path = Prompt.ask("  Repository path", default=current_repo_path)
    repo_path = str(Path(repo_path).resolve())

    # Clear old repos and re-add
    config.repos.clear()

    # Validate the repo
    try:
        from devdiary.scanner.git_scanner import GitScanner
        scanner = GitScanner(repo_path)
        default_repo_name = scanner.repo_name if scanner.validate() else Path(repo_path).name
        if has_existing and existing.repos:
            default_repo_name = existing.repos[0].name or default_repo_name

        if scanner.validate():
            repo_name = Prompt.ask("  Project name", default=default_repo_name)
            config.repos.append(RepoConfig(path=repo_path, name=repo_name))
            console.print(f"  [green]✓ Valid Git repository: {repo_name}[/green]")
        else:
            console.print(f"  [yellow]⚠ Not a valid Git repository, skipping.[/yellow]")
    except Exception as e:
        console.print(f"  [yellow]⚠ Could not validate repository: {e}[/yellow]")
        default_name = existing.repos[0].name if (has_existing and existing.repos) else Path(repo_path).name
        repo_name = Prompt.ask("  Project name", default=default_name)
        config.repos.append(RepoConfig(path=repo_path, name=repo_name))

    console.print()

    # Output configuration
    console.print("[bold]Step 3: Output Settings[/bold]")
    output_dir = Prompt.ask("  Output directory", default=config.output.dir or "diaries")
    config.output.dir = output_dir

    output_format = Prompt.ask(
        "  Output format",
        choices=["markdown", "html", "both"],
        default=config.output.format or "markdown",
    )
    config.output.format = output_format

    default_style = Prompt.ask(
        "  Default writing style",
        choices=["diary", "blog", "report"],
        default=config.output.style or "diary",
    )
    config.output.style = default_style

    # Save configuration
    config.save()
    console.print()
    console.print(
        Panel(
            f"[green]✅ Configuration saved to [bold]{config.config_path}[/bold][/green]\n\n"
            f"Try generating your first diary:\n"
            f"  [cyan]devdiary today[/cyan]",
            title="🎉 Initialization Complete",
            border_style="green",
        )
    )


def _display_config_summary(config: Config) -> None:
    """Display a summary of the current configuration."""
    table = Table(title="Current Configuration", border_style="blue")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("AI Provider", config.ai.provider)
    key = config.ai.api_key
    masked_key = f"{key[:6]}...{key[-4:]}" if len(key) > 10 else ("(set)" if key else "(not set)")
    table.add_row("API Key", masked_key)
    table.add_row("Model", config.ai.model)
    table.add_row("Base URL", config.ai.base_url or "(default)")
    table.add_row("Repos", ", ".join(r.name for r in config.repos) if config.repos else "(none)")
    table.add_row("Output Dir", config.output.dir)
    table.add_row("Output Format", config.output.format)
    table.add_row("Writing Style", config.output.style)

    console.print(table)
    console.print()


@cli.command()
@click.option("--config-dir", default=".devdiary", help="Configuration directory")
@click.option("--repo", "-r", default=None, help="Repository path (override config)")
@click.option("--style", "-s", type=click.Choice(["diary", "blog", "report"]), default=None, help="Writing style")
@click.option("--format", "-f", "output_format", type=click.Choice(["markdown", "html", "both"]), default=None, help="Output format")
@click.option("--output", "-o", default=None, help="Output directory")
@click.option("--from", "date_from_str", default=None, help="Start date (YYYY-MM-DD), override default")
@click.option("--to", "date_to_str", default=None, help="End date (YYYY-MM-DD), override default")
def today(config_dir: str, repo: Optional[str], style: Optional[str], output_format: Optional[str], output: Optional[str], date_from_str: Optional[str], date_to_str: Optional[str]) -> None:
    """📅 Generate today's development diary."""
    _banner()
    now = datetime.now(tz=timezone.utc)
    date_from = _parse_date(date_from_str) if date_from_str else now.replace(hour=0, minute=0, second=0, microsecond=0)
    date_to = _parse_date_end(date_to_str) if date_to_str else now

    _generate_diary(
        config_dir=config_dir,
        repo_path=repo,
        style=style,
        output_format=output_format,
        output_dir=output,
        date_from=date_from,
        date_to=date_to,
        period_label="Today",
    )


@cli.command()
@click.option("--config-dir", default=".devdiary", help="Configuration directory")
@click.option("--repo", "-r", default=None, help="Repository path (override config)")
@click.option("--style", "-s", type=click.Choice(["diary", "blog", "report"]), default=None, help="Writing style")
@click.option("--format", "-f", "output_format", type=click.Choice(["markdown", "html", "both"]), default=None, help="Output format")
@click.option("--output", "-o", default=None, help="Output directory")
@click.option("--from", "date_from_str", default=None, help="Start date (YYYY-MM-DD), override default")
@click.option("--to", "date_to_str", default=None, help="End date (YYYY-MM-DD), override default")
def week(config_dir: str, repo: Optional[str], style: Optional[str], output_format: Optional[str], output: Optional[str], date_from_str: Optional[str], date_to_str: Optional[str]) -> None:
    """📆 Generate this week's development report."""
    _banner()
    now = datetime.now(tz=timezone.utc)
    # Monday of this week
    date_from = _parse_date(date_from_str) if date_from_str else (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    date_to = _parse_date_end(date_to_str) if date_to_str else now

    _generate_diary(
        config_dir=config_dir,
        repo_path=repo,
        style=style or "report",
        output_format=output_format,
        output_dir=output,
        date_from=date_from,
        date_to=date_to,
        period_label="This Week",
    )


@cli.command()
@click.option("--config-dir", default=".devdiary", help="Configuration directory")
@click.option("--repo", "-r", default=None, help="Repository path (override config)")
@click.option("--style", "-s", type=click.Choice(["diary", "blog", "report"]), default=None, help="Writing style")
@click.option("--format", "-f", "output_format", type=click.Choice(["markdown", "html", "both"]), default=None, help="Output format")
@click.option("--output", "-o", default=None, help="Output directory")
@click.option("--from", "date_from_str", default=None, help="Start date (YYYY-MM-DD), override default")
@click.option("--to", "date_to_str", default=None, help="End date (YYYY-MM-DD), override default")
def month(config_dir: str, repo: Optional[str], style: Optional[str], output_format: Optional[str], output: Optional[str], date_from_str: Optional[str], date_to_str: Optional[str]) -> None:
    """📊 Generate this month's development report."""
    _banner()
    now = datetime.now(tz=timezone.utc)
    date_from = _parse_date(date_from_str) if date_from_str else now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    date_to = _parse_date_end(date_to_str) if date_to_str else now

    _generate_diary(
        config_dir=config_dir,
        repo_path=repo,
        style=style or "report",
        output_format=output_format,
        output_dir=output,
        date_from=date_from,
        date_to=date_to,
        period_label="This Month",
    )


@cli.command()
@click.option("--config-dir", default=".devdiary", help="Configuration directory")
@click.option("--repo", "-r", default=None, help="Repository path (override config)")
@click.option("--style", "-s", type=click.Choice(["diary", "blog", "report"]), default=None, help="Writing style")
@click.option("--format", "-f", "output_format", type=click.Choice(["markdown", "html", "both"]), default=None, help="Output format")
@click.option("--output", "-o", default=None, help="Output directory")
@click.argument("date_from_str")
@click.argument("date_to_str", required=False, default=None)
def generate(config_dir: str, repo: Optional[str], style: Optional[str], output_format: Optional[str], output: Optional[str], date_from_str: str, date_to_str: Optional[str]) -> None:
    """🗓️ Generate diary for a custom date range.

    \b
    Examples:
      devdiary generate 2026-03-01                  # Single day
      devdiary generate 2026-03-01 2026-03-09       # Date range
      devdiary generate 2026-02-01 2026-02-28 -s blog  # Feb as blog style
    """
    _banner()
    date_from = _parse_date(date_from_str)
    if date_to_str:
        date_to = _parse_date_end(date_to_str)
    else:
        # Single day: from 00:00 to 23:59:59
        date_to = date_from.replace(hour=23, minute=59, second=59)

    period_label = date_from.strftime("%Y-%m-%d")
    if date_from.date() != date_to.date():
        period_label += f" ~ {date_to.strftime('%Y-%m-%d')}"

    _generate_diary(
        config_dir=config_dir,
        repo_path=repo,
        style=style,
        output_format=output_format,
        output_dir=output,
        date_from=date_from,
        date_to=date_to,
        period_label=period_label,
    )


def _parse_date(date_str: str) -> datetime:
    """Parse a date string (YYYY-MM-DD) to datetime at 00:00:00 UTC."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=0, minute=0, second=0, tzinfo=timezone.utc
        )
    except ValueError:
        console.print(f"[red]Invalid date format: '{date_str}'. Expected YYYY-MM-DD.[/red]")
        raise SystemExit(1)


def _parse_date_end(date_str: str) -> datetime:
    """Parse a date string (YYYY-MM-DD) to datetime at 23:59:59 UTC."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59, tzinfo=timezone.utc
        )
    except ValueError:
        console.print(f"[red]Invalid date format: '{date_str}'. Expected YYYY-MM-DD.[/red]")
        raise SystemExit(1)


def _generate_diary(
    config_dir: str,
    repo_path: Optional[str],
    style: Optional[str],
    output_format: Optional[str],
    output_dir: Optional[str],
    date_from: datetime,
    date_to: datetime,
    period_label: str,
) -> None:
    """Core diary generation logic shared by today/week/month commands."""
    # Load config
    config = Config.load(config_dir)

    if not config.config_path.exists():
        console.print(
            "[red]❌ DevDiary not initialized. Run [bold]devdiary init[/bold] first.[/red]"
        )
        sys.exit(1)

    # Resolve parameters (CLI args override config)
    actual_style = style or config.output.style
    actual_format = output_format or config.output.format
    actual_output = output_dir or config.output.dir

    # Get repo path
    if repo_path:
        repos = [RepoConfig(path=repo_path, name=Path(repo_path).name)]
    elif config.repos:
        repos = config.repos
    else:
        console.print("[red]❌ No repository configured. Run [bold]devdiary init[/bold].[/red]")
        sys.exit(1)

    console.print(
        f"[bold]Generating {period_label} {actual_style}...[/bold]\n"
        f"  📅 Period: {date_from.strftime('%Y-%m-%d')} ~ {date_to.strftime('%Y-%m-%d')}\n"
    )

    for repo_cfg in repos:
        console.print(f"[bold cyan]📁 Repository: {repo_cfg.name}[/bold cyan] ({repo_cfg.path})")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Step 1: Scan commits
            task = progress.add_task("Scanning Git commits...", total=None)
            try:
                from devdiary.scanner.git_scanner import GitScanner
                scanner = GitScanner(repo_cfg.path)
                commits = scanner.scan_commits(date_from=date_from, date_to=date_to)
                file_exts = scanner.get_file_extensions()
            except Exception as e:
                console.print(f"  [red]❌ Error scanning repository: {e}[/red]")
                continue
            progress.update(task, description=f"Found {len(commits)} commits", completed=True)

            if not commits:
                console.print(f"  [yellow]⚠ No commits found in this period.[/yellow]\n")
                continue

            # Step 2: Analyze
            task2 = progress.add_task("Analyzing commit data...", total=None)
            from devdiary.scanner.tech_detector import TechDetector
            from devdiary.analyzer.stats_analyzer import StatsAnalyzer

            detector = TechDetector(repo_cfg.path)
            tech_stack = detector.detect(file_exts)
            analyzer = StatsAnalyzer()
            report = analyzer.analyze(commits, tech_stack.languages)
            progress.update(task2, description="Analysis complete", completed=True)

            # Step 3: Generate content with AI
            task3 = progress.add_task(f"Generating content via {config.ai.provider}...", total=None)

            if not config.ai.api_key:
                progress.update(task3, description="[yellow]No API key configured, generating summary only[/yellow]", completed=True)
                # Fallback: generate a basic summary without AI
                content = _generate_fallback_content(commits, report, tech_stack.to_tags(), repo_cfg.name, date_from, date_to)
                title = f"{repo_cfg.name} - {period_label} ({date_from.strftime('%Y-%m-%d')})"
            else:
                try:
                    from devdiary.generator.content_generator import ContentGenerator
                    generator = ContentGenerator.from_config(
                        provider_name=config.ai.provider,
                        api_key=config.ai.api_key,
                        model=config.ai.model,
                        base_url=config.ai.base_url,
                    )
                    result = _run_async(generator.generate(
                        commits=commits,
                        project_name=repo_cfg.name,
                        style=actual_style,
                        date_from=date_from,
                        date_to=date_to,
                        tech_stack=tech_stack.to_tags(),
                        analysis=report,
                        temperature=config.ai.temperature,
                        max_tokens=config.ai.max_tokens,
                    ))
                    content = result.content
                    title = f"{repo_cfg.name} - {period_label} ({date_from.strftime('%Y-%m-%d')})"
                    progress.update(task3, description=f"Generated ({result.tokens_used} tokens)", completed=True)
                except Exception as e:
                    progress.update(task3, description=f"[red]AI error: {e}[/red]", completed=True)
                    console.print(f"  [yellow]Falling back to summary mode...[/yellow]")
                    content = _generate_fallback_content(commits, report, tech_stack.to_tags(), repo_cfg.name, date_from, date_to)
                    title = f"{repo_cfg.name} - {period_label} ({date_from.strftime('%Y-%m-%d')})"

            # Step 4: Render output
            task4 = progress.add_task("Saving output files...", total=None)
            saved_files: list[str] = []

            if actual_format in ("markdown", "both"):
                from devdiary.renderer.markdown_renderer import MarkdownRenderer
                md_renderer = MarkdownRenderer(actual_output)
                md_path = md_renderer.save(
                    content=content,
                    title=title,
                    project_name=repo_cfg.name,
                    date=date_from,
                    style=actual_style,
                    tech_stack=tech_stack.to_tags(),
                )
                saved_files.append(str(md_path))

            if actual_format in ("html", "both"):
                from devdiary.renderer.html_renderer import HtmlRenderer
                html_renderer = HtmlRenderer(actual_output)
                html_path = html_renderer.save(
                    content=content,
                    title=title,
                    project_name=repo_cfg.name,
                    date=date_from,
                    style=actual_style,
                    tech_stack=tech_stack.to_tags(),
                )
                saved_files.append(str(html_path))

            progress.update(task4, description="Output saved", completed=True)

        # Display summary
        console.print()
        _display_summary(commits, report, tech_stack.to_tags(), saved_files)
        console.print()


def _generate_fallback_content(
    commits: list,
    report: object,
    tech_tags: list[str],
    project_name: str,
    date_from: datetime,
    date_to: datetime,
) -> str:
    """Generate basic content without AI when no API key is configured."""
    lines = [
        f"# {project_name} - Development Summary",
        f"",
        f"**Date**: {date_from.strftime('%Y-%m-%d')} ~ {date_to.strftime('%Y-%m-%d')}",
        f"**Tech Stack**: {', '.join(tech_tags) if tech_tags else 'N/A'}",
        f"",
        f"## Commit Summary",
        f"",
    ]

    for c in commits[:20]:
        date_str = c.date.strftime("%Y-%m-%d %H:%M")
        lines.append(f"- **[{date_str}]** {c.first_line} (+{c.total_insertions}/-{c.total_deletions})")

    if len(commits) > 20:
        lines.append(f"- ... and {len(commits) - 20} more commits")

    lines.extend([
        f"",
        f"## Statistics",
        f"",
        f"- Total commits: {len(commits)}",
        f"- Total insertions: {sum(c.total_insertions for c in commits)}",
        f"- Total deletions: {sum(c.total_deletions for c in commits)}",
        f"",
        f"> 💡 Configure an AI API key with `devdiary init` for AI-generated content.",
    ])

    return "\n".join(lines)


def _display_summary(commits: list, report: object, tech_tags: list[str], saved_files: list[str]) -> None:
    """Display a summary table in the terminal."""
    table = Table(title="📊 Generation Summary", border_style="blue")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Commits Analyzed", str(len(commits)))
    table.add_row("Code Changes", f"+{sum(c.total_insertions for c in commits)} / -{sum(c.total_deletions for c in commits)}")
    table.add_row("Tech Stack", ", ".join(tech_tags[:5]) if tech_tags else "N/A")

    for f in saved_files:
        ext = Path(f).suffix.upper()
        table.add_row(f"Output ({ext})", f)

    console.print(table)


if __name__ == "__main__":
    cli()
