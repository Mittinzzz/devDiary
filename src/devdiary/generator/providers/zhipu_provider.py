"""Zhipu AI (GLM) API provider implementation."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from devdiary.generator.ai_provider import AIProvider, GenerationResult, ProviderRegistry

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
DEFAULT_MODEL = "glm-4-flash"
MAX_RETRIES = 3


class ZhipuProvider(AIProvider):
    """Zhipu AI (ChatGLM) API provider."""

    @property
    def name(self) -> str:
        return "zhipu"

    @property
    def default_model(self) -> str:
        return DEFAULT_MODEL

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> GenerationResult:
        """Generate text using Zhipu AI API."""
        base_url = (self.base_url or DEFAULT_BASE_URL).rstrip("/")
        model = self.get_model()

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        f"{base_url}/chat/completions",
                        json=payload,
                        headers=headers,
                    )
                    response.raise_for_status()
                    data = response.json()

                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                tokens_used = usage.get("total_tokens", 0)

                return GenerationResult(
                    content=content,
                    tokens_used=tokens_used,
                    model=model,
                    provider=self.name,
                )

            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code in (429, 500, 502, 503):
                    wait = 2 ** attempt
                    logger.warning(
                        f"Zhipu API error (attempt {attempt + 1}/{MAX_RETRIES}): "
                        f"{e.response.status_code}. Retrying in {wait}s..."
                    )
                    await asyncio.sleep(wait)
                else:
                    raise

            except httpx.RequestError as e:
                last_error = e
                wait = 2 ** attempt
                logger.warning(
                    f"Network error (attempt {attempt + 1}/{MAX_RETRIES}): {e}. "
                    f"Retrying in {wait}s..."
                )
                await asyncio.sleep(wait)

        raise RuntimeError(f"Failed after {MAX_RETRIES} retries. Last error: {last_error}")


# Register the provider
ProviderRegistry.register("zhipu", ZhipuProvider)
