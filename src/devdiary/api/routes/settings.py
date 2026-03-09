"""Settings management API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from devdiary.config import Config
from devdiary.api.schemas import SettingsResponse, SettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _mask_api_key(api_key: str) -> str:
    """Mask API key for safe display: show first 6 and last 4 chars."""
    if not api_key:
        return ""
    if len(api_key) <= 10:
        return "***"
    return f"{api_key[:6]}***{api_key[-4:]}"


@router.get("", response_model=SettingsResponse)
async def get_settings():
    """Get current application settings with masked API key."""
    config = Config.load()

    return SettingsResponse(
        ai_provider=config.ai.provider,
        api_key_masked=_mask_api_key(config.ai.api_key),
        model=config.ai.model,
        base_url=config.ai.base_url,
        repos=[{"path": r.path, "name": r.name} for r in config.repos],
        output_dir=config.output.dir,
        output_format=config.output.format,
        output_style=config.output.style,
    )


@router.put("", response_model=SettingsResponse)
async def update_settings(data: SettingsUpdate):
    """Update application settings and persist to config file."""
    config = Config.load()

    # Update AI config fields
    if data.ai_provider is not None:
        config.ai.provider = data.ai_provider
    if data.api_key is not None:
        config.ai.api_key = data.api_key
    if data.model is not None:
        config.ai.model = data.model
    if data.base_url is not None:
        config.ai.base_url = data.base_url

    # Update output config fields
    if data.output_dir is not None:
        config.output.dir = data.output_dir
    if data.output_format is not None:
        config.output.format = data.output_format
    if data.output_style is not None:
        config.output.style = data.output_style

    # Persist to config file
    try:
        config.save()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存配置失败: {e}")

    return SettingsResponse(
        ai_provider=config.ai.provider,
        api_key_masked=_mask_api_key(config.ai.api_key),
        model=config.ai.model,
        base_url=config.ai.base_url,
        repos=[{"path": r.path, "name": r.name} for r in config.repos],
        output_dir=config.output.dir,
        output_format=config.output.format,
        output_style=config.output.style,
    )
