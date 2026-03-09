"""Watcher management API routes."""

from __future__ import annotations

from fastapi import APIRouter

from devdiary.watcher import (
    WatchConfig,
    get_watcher_state,
    start_watcher_background,
    stop_watcher,
)

router = APIRouter(prefix="/api/watcher", tags=["watcher"])


@router.get("/status")
async def get_status():
    """Get current watcher service status."""
    state = get_watcher_state()
    config = WatchConfig.load()
    return {
        "config": config.to_dict(),
        "state": {
            "running": state.running,
            "last_check": state.last_check,
            "last_generated": state.last_generated,
            "next_run": state.next_run,
            "diaries_generated": state.diaries_generated,
            "errors": state.errors[-5:],  # last 5 errors
        },
    }


@router.post("/start")
async def start_watcher():
    """Start the watcher service."""
    state = get_watcher_state()
    if state.running:
        return {"message": "Watcher is already running", "running": True}
    await start_watcher_background()
    return {"message": "Watcher started", "running": True}


@router.post("/stop")
async def stop_watcher_endpoint():
    """Stop the watcher service."""
    await stop_watcher()
    return {"message": "Watcher stopped", "running": False}


@router.get("/config")
async def get_watch_config():
    """Get watcher configuration."""
    config = WatchConfig.load()
    return config.to_dict()


@router.put("/config")
async def update_watch_config(data: dict):
    """Update watcher configuration."""
    config = WatchConfig.load()

    if "enabled" in data:
        config.enabled = bool(data["enabled"])
    if "schedule" in data and data["schedule"] in ("daily", "weekly", "on_push"):
        config.schedule = data["schedule"]
    if "time" in data:
        config.time = str(data["time"])
    if "weekday" in data:
        config.weekday = str(data["weekday"])
    if "auto_scan" in data:
        config.auto_scan = bool(data["auto_scan"])
    if "notify_desktop" in data:
        config.notify_desktop = bool(data["notify_desktop"])
    if "notify_email" in data:
        config.notify_email = data["notify_email"] or None
    if "notify_webhook" in data:
        config.notify_webhook = data["notify_webhook"] or None

    config.save()
    return config.to_dict()
