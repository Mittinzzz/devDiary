"""Configuration management for DevDiary."""

from __future__ import annotations

import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG_DIR = ".devdiary"
DEFAULT_CONFIG_FILE = "config.yaml"
DEFAULT_DB_NAME = "devdiary.db"
DEFAULT_OUTPUT_DIR = "diaries"


@dataclass
class AIConfig:
    """AI provider configuration."""

    provider: str = "openai"
    api_key: str = ""
    model: str = "gpt-4o-mini"
    base_url: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096


@dataclass
class RepoConfig:
    """Repository configuration."""

    path: str = ""
    name: str = ""

    def __post_init__(self) -> None:
        if not self.name and self.path:
            self.name = Path(self.path).name


@dataclass
class OutputConfig:
    """Output configuration."""

    dir: str = DEFAULT_OUTPUT_DIR
    format: str = "markdown"  # markdown / html / both
    style: str = "diary"  # diary / blog / report


@dataclass
class Config:
    """Main application configuration."""

    ai: AIConfig = field(default_factory=AIConfig)
    repos: list[RepoConfig] = field(default_factory=list)
    output: OutputConfig = field(default_factory=OutputConfig)
    db_url: str = ""
    config_dir: str = DEFAULT_CONFIG_DIR

    def __post_init__(self) -> None:
        if not self.db_url:
            db_path = Path(self.config_dir) / DEFAULT_DB_NAME
            self.db_url = f"sqlite+aiosqlite:///{db_path}"

    @property
    def config_path(self) -> Path:
        """Path to the config file."""
        return Path(self.config_dir) / DEFAULT_CONFIG_FILE

    @property
    def db_path(self) -> Path:
        """Path to the database file."""
        return Path(self.config_dir) / DEFAULT_DB_NAME

    @property
    def output_path(self) -> Path:
        """Path to the output directory."""
        return Path(self.output.dir)

    def ensure_dirs(self) -> None:
        """Create necessary directories."""
        Path(self.config_dir).mkdir(parents=True, exist_ok=True)
        self.output_path.mkdir(parents=True, exist_ok=True)

    def save(self) -> None:
        """Save configuration to YAML file."""
        self.ensure_dirs()
        data = {
            "ai": {
                "provider": self.ai.provider,
                "api_key": self.ai.api_key,
                "model": self.ai.model,
                "base_url": self.ai.base_url,
                "temperature": self.ai.temperature,
                "max_tokens": self.ai.max_tokens,
            },
            "repos": [{"path": r.path, "name": r.name} for r in self.repos],
            "output": {
                "dir": self.output.dir,
                "format": self.output.format,
                "style": self.output.style,
            },
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    @classmethod
    def load(cls, config_dir: str = DEFAULT_CONFIG_DIR) -> Config:
        """Load configuration from YAML file."""
        config_path = Path(config_dir) / DEFAULT_CONFIG_FILE
        if not config_path.exists():
            return cls(config_dir=config_dir)

        with open(config_path, "r", encoding="utf-8") as f:
            data: dict[str, Any] = yaml.safe_load(f) or {}

        ai_data = data.get("ai", {})
        ai_config = AIConfig(
            provider=ai_data.get("provider", "openai"),
            api_key=ai_data.get("api_key", ""),
            model=ai_data.get("model", "gpt-4o-mini"),
            base_url=ai_data.get("base_url"),
            temperature=ai_data.get("temperature", 0.7),
            max_tokens=ai_data.get("max_tokens", 4096),
        )

        repos_data = data.get("repos", [])
        repos = [RepoConfig(path=r.get("path", ""), name=r.get("name", "")) for r in repos_data]

        output_data = data.get("output", {})
        output_config = OutputConfig(
            dir=output_data.get("dir", DEFAULT_OUTPUT_DIR),
            format=output_data.get("format", "markdown"),
            style=output_data.get("style", "diary"),
        )

        return cls(
            ai=ai_config,
            repos=repos,
            output=output_config,
            config_dir=config_dir,
        )

    @classmethod
    def load_or_create(cls, config_dir: str = DEFAULT_CONFIG_DIR) -> Config:
        """Load existing config or create a default one."""
        config = cls.load(config_dir)
        if not config.config_path.exists():
            config.save()
        return config
