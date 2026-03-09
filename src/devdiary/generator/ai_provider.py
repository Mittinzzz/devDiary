"""Abstract AI provider interface and registry."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """Result from an AI generation call."""

    content: str
    tokens_used: int = 0
    model: str = ""
    provider: str = ""

    @property
    def is_empty(self) -> bool:
        return not self.content.strip()


class AIProvider(ABC):
    """Abstract base class for AI service providers."""

    def __init__(self, api_key: str, model: str = "", base_url: str | None = None, **kwargs: Any):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.extra_config = kwargs

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> GenerationResult:
        """
        Generate text from a prompt.

        Args:
            prompt: The user prompt to generate from.
            system_prompt: Optional system/instruction prompt.
            temperature: Sampling temperature (0-2).
            max_tokens: Maximum tokens in the response.

        Returns:
            GenerationResult containing the generated text and metadata.
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name identifier."""
        ...

    @property
    def default_model(self) -> str:
        """Default model for this provider."""
        return ""

    def get_model(self) -> str:
        """Get the model to use, falling back to default."""
        return self.model or self.default_model


class ProviderRegistry:
    """Registry for AI provider implementations."""

    _providers: dict[str, type[AIProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_class: type[AIProvider]) -> None:
        """Register a provider class by name."""
        cls._providers[name.lower()] = provider_class
        logger.debug(f"Registered AI provider: {name}")

    @classmethod
    def get(cls, name: str, **kwargs: Any) -> AIProvider:
        """
        Get an instance of a registered provider.

        Args:
            name: Provider name (case-insensitive).
            **kwargs: Arguments passed to the provider constructor.

        Returns:
            An instance of the requested AIProvider.

        Raises:
            ValueError: If the provider is not registered.
        """
        provider_class = cls._providers.get(name.lower())
        if provider_class is None:
            available = ", ".join(cls._providers.keys())
            raise ValueError(
                f"Unknown AI provider '{name}'. Available providers: {available}"
            )
        return provider_class(**kwargs)

    @classmethod
    def list_providers(cls) -> list[str]:
        """List all registered provider names."""
        return list(cls._providers.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a provider is registered."""
        return name.lower() in cls._providers
