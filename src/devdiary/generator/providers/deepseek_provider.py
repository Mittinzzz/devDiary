"""DeepSeek AI API provider implementation."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from devdiary.generator.ai_provider import AIProvider, GenerationResult, ProviderRegistry

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-chat"
MAX_RETRIES = 3


class DeepSeekProvider(AIProvider):
    """
    DeepSeek AI API provider.

    DeepSeek uses an OpenAI-compatible API format, supporting models like:
    - deepseek-chat (DeepSeek-V3)
    - deepseek-reasoner (DeepSeek-R1)
    """

    @property
    def name(self) -> str:
        return "deepseek"

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
        """Generate text using DeepSeek Chat API."""
        base_url = (self.base_url or DEFAULT_BASE_URL).rstrip("/")
        model = self.get_model()

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # DeepSeek-R1 (reasoner) doesn't support temperature / max_tokens
        if "reasoner" in model.lower():
            payload.pop("temperature", None)
            payload.pop("max_tokens", None)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=180.0) as client:
                    response = await client.post(
                        f"{base_url}/chat/completions",
                        json=payload,
                        headers=headers,
                    )
                    response.raise_for_status()
                    data = response.json()

                content = data["choices"][0]["message"]["content"]

                # DeepSeek-R1 may include reasoning_content
                reasoning = data["choices"][0]["message"].get("reasoning_content", "")
                if reasoning and not content:
                    content = reasoning

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
                        f"DeepSeek API error (attempt {attempt + 1}/{MAX_RETRIES}): "
                        f"{e.response.status_code}. Retrying in {wait}s..."
                    )
                    await asyncio.sleep(wait)
                else:
                    logger.error(
                        f"DeepSeek API error: {e.response.status_code} - {e.response.text}"
                    )
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
ProviderRegistry.register("deepseek", DeepSeekProvider)
