"""Technology stack detection from repository files."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# Mapping of file extensions to programming languages
EXTENSION_LANGUAGE_MAP: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".java": "Java",
    ".kt": "Kotlin",
    ".go": "Go",
    ".rs": "Rust",
    ".cpp": "C++",
    ".c": "C",
    ".h": "C/C++",
    ".hpp": "C++",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".scala": "Scala",
    ".r": "R",
    ".R": "R",
    ".dart": "Dart",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".lua": "Lua",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".ps1": "PowerShell",
    ".sql": "SQL",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".less": "Less",
    ".md": "Markdown",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".xml": "XML",
    ".toml": "TOML",
}

# Mapping of config files / dirs to frameworks/tools
FRAMEWORK_INDICATORS: dict[str, str] = {
    "package.json": "Node.js",
    "requirements.txt": "Python (pip)",
    "pyproject.toml": "Python (modern)",
    "setup.py": "Python (setuptools)",
    "Pipfile": "Python (Pipenv)",
    "poetry.lock": "Python (Poetry)",
    "Cargo.toml": "Rust (Cargo)",
    "go.mod": "Go Modules",
    "pom.xml": "Java (Maven)",
    "build.gradle": "Java (Gradle)",
    "build.gradle.kts": "Kotlin (Gradle)",
    "Gemfile": "Ruby (Bundler)",
    "composer.json": "PHP (Composer)",
    "pubspec.yaml": "Dart (Flutter/Pub)",
    "CMakeLists.txt": "C/C++ (CMake)",
    "Makefile": "Make",
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose",
    ".github/workflows": "GitHub Actions",
    "Jenkinsfile": "Jenkins",
    ".gitlab-ci.yml": "GitLab CI",
    "vue.config.js": "Vue.js",
    "vite.config.ts": "Vite",
    "vite.config.js": "Vite",
    "next.config.js": "Next.js",
    "next.config.mjs": "Next.js",
    "nuxt.config.ts": "Nuxt.js",
    "angular.json": "Angular",
    "svelte.config.js": "SvelteKit",
    "tailwind.config.js": "TailwindCSS",
    "tailwind.config.ts": "TailwindCSS",
    "webpack.config.js": "Webpack",
    "tsconfig.json": "TypeScript",
    ".eslintrc.js": "ESLint",
    ".eslintrc.json": "ESLint",
    "jest.config.js": "Jest",
    "vitest.config.ts": "Vitest",
    "pytest.ini": "pytest",
    "tox.ini": "Tox",
    "alembic.ini": "Alembic (DB Migration)",
    ".env": "dotenv",
    "terraform": "Terraform",
    "k8s": "Kubernetes",
}


@dataclass
class TechStack:
    """Detected technology stack information."""

    languages: dict[str, int] = field(default_factory=dict)  # language -> file count
    frameworks: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)

    @property
    def primary_language(self) -> str | None:
        """Get the most used programming language."""
        if not self.languages:
            return None
        return max(self.languages, key=self.languages.get)  # type: ignore

    @property
    def language_percentages(self) -> dict[str, float]:
        """Get language distribution as percentages."""
        total = sum(self.languages.values())
        if total == 0:
            return {}
        return {lang: (count / total) * 100 for lang, count in self.languages.items()}

    def to_tags(self) -> list[str]:
        """Convert to a list of tag strings for display."""
        tags: list[str] = []
        if self.primary_language:
            tags.append(self.primary_language)
        # Add top 3 languages (excluding primary)
        sorted_langs = sorted(self.languages.items(), key=lambda x: x[1], reverse=True)
        for lang, _ in sorted_langs[1:4]:
            if lang not in tags:
                tags.append(lang)
        # Add frameworks
        tags.extend(self.frameworks[:5])
        return tags


class TechDetector:
    """Detects technology stack from repository file structure."""

    def __init__(self, repo_path: str | Path) -> None:
        self.repo_path = Path(repo_path).resolve()

    def detect(self, file_extensions: dict[str, int] | None = None) -> TechStack:
        """
        Detect the technology stack of a repository.

        Args:
            file_extensions: Pre-computed file extension counts (from GitScanner).
                           If None, will scan the filesystem directly.

        Returns:
            TechStack with detected languages, frameworks, and tools.
        """
        tech = TechStack()

        # Detect languages from file extensions
        if file_extensions:
            for ext, count in file_extensions.items():
                lang = EXTENSION_LANGUAGE_MAP.get(ext)
                if lang and lang not in ("Markdown", "JSON", "YAML", "TOML", "XML", "HTML", "CSS", "SCSS", "Less"):
                    tech.languages[lang] = tech.languages.get(lang, 0) + count
        else:
            tech.languages = self._scan_languages()

        # Detect frameworks and tools from config files
        frameworks, tools = self._scan_frameworks()
        tech.frameworks = frameworks
        tech.tools = tools

        return tech

    def _scan_languages(self) -> dict[str, int]:
        """Scan repository directory for programming language files."""
        languages: dict[str, int] = {}
        try:
            for path in self.repo_path.rglob("*"):
                if path.is_file() and not self._should_ignore(path):
                    ext = path.suffix.lower()
                    lang = EXTENSION_LANGUAGE_MAP.get(ext)
                    if lang and lang not in ("Markdown", "JSON", "YAML", "TOML", "XML", "HTML", "CSS", "SCSS", "Less"):
                        languages[lang] = languages.get(lang, 0) + 1
        except Exception as e:
            logger.debug(f"Error scanning languages: {e}")
        return languages

    def _scan_frameworks(self) -> tuple[list[str], list[str]]:
        """Detect frameworks and tools from configuration files."""
        frameworks: list[str] = []
        tools: list[str] = []

        # Check for known indicator files
        for indicator, name in FRAMEWORK_INDICATORS.items():
            indicator_path = self.repo_path / indicator
            if indicator_path.exists():
                # Classify as framework or tool
                if any(kw in name.lower() for kw in ["docker", "ci", "actions", "jenkins",
                                                       "gitlab", "make", "terraform",
                                                       "kubernetes", "eslint", "jest",
                                                       "vitest", "pytest", "tox", "dotenv"]):
                    if name not in tools:
                        tools.append(name)
                else:
                    if name not in frameworks:
                        frameworks.append(name)

        # Check package.json for specific frameworks
        package_json = self.repo_path / "package.json"
        if package_json.exists():
            self._detect_from_package_json(package_json, frameworks)

        # Check requirements.txt for specific frameworks
        requirements_txt = self.repo_path / "requirements.txt"
        if requirements_txt.exists():
            self._detect_from_requirements(requirements_txt, frameworks)

        return frameworks, tools

    def _detect_from_package_json(self, path: Path, frameworks: list[str]) -> None:
        """Detect frameworks from package.json dependencies."""
        try:
            import json
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            all_deps = {}
            all_deps.update(data.get("dependencies", {}))
            all_deps.update(data.get("devDependencies", {}))

            npm_framework_map = {
                "react": "React",
                "vue": "Vue.js",
                "svelte": "Svelte",
                "@angular/core": "Angular",
                "express": "Express.js",
                "fastify": "Fastify",
                "next": "Next.js",
                "nuxt": "Nuxt.js",
                "electron": "Electron",
                "react-native": "React Native",
                "echarts": "ECharts",
                "d3": "D3.js",
                "three": "Three.js",
                "tailwindcss": "TailwindCSS",
                "naive-ui": "Naive UI",
                "element-plus": "Element Plus",
                "ant-design-vue": "Ant Design Vue",
            }

            for dep, fw_name in npm_framework_map.items():
                if dep in all_deps and fw_name not in frameworks:
                    frameworks.append(fw_name)

        except Exception as e:
            logger.debug(f"Error reading package.json: {e}")

    def _detect_from_requirements(self, path: Path, frameworks: list[str]) -> None:
        """Detect frameworks from requirements.txt."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            pip_framework_map = {
                "django": "Django",
                "flask": "Flask",
                "fastapi": "FastAPI",
                "sqlalchemy": "SQLAlchemy",
                "celery": "Celery",
                "scrapy": "Scrapy",
                "pandas": "Pandas",
                "numpy": "NumPy",
                "tensorflow": "TensorFlow",
                "pytorch": "PyTorch",
                "torch": "PyTorch",
            }

            for line in lines:
                pkg = line.strip().split("==")[0].split(">=")[0].split("<=")[0].split("[")[0].lower()
                if pkg in pip_framework_map:
                    fw_name = pip_framework_map[pkg]
                    if fw_name not in frameworks:
                        frameworks.append(fw_name)

        except Exception as e:
            logger.debug(f"Error reading requirements.txt: {e}")

    @staticmethod
    def _should_ignore(path: Path) -> bool:
        """Check if a file path should be ignored."""
        ignore_dirs = {
            "node_modules", ".git", "__pycache__", ".venv", "venv",
            "env", "dist", "build", ".idea", ".vscode", ".tox",
            "target", "vendor", ".next", ".nuxt",
        }
        return any(part in ignore_dirs for part in path.parts)
