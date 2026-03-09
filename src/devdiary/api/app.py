"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from devdiary import __version__
from devdiary.database import init_db, close_db
from devdiary.api.routes.diaries import router as diaries_router
from devdiary.api.routes.projects import router as projects_router
from devdiary.api.routes.stats import router as stats_router
from devdiary.api.routes.settings import router as settings_router
from devdiary.api.routes.report import router as report_router
from devdiary.api.routes.watcher import router as watcher_router


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    """Application lifespan: startup and shutdown events."""
    # Startup
    await init_db()
    yield
    # Shutdown
    from devdiary.watcher import stop_watcher
    await stop_watcher()
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="DevDiary API",
        description="DevDiary - Your Second Brain for Development. "
                    "REST API for managing dev diaries, projects, and analytics.",
        version=__version__,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routes
    app.include_router(diaries_router)
    app.include_router(projects_router)
    app.include_router(stats_router)
    app.include_router(settings_router)
    app.include_router(report_router)
    app.include_router(watcher_router)

    # Health check
    @app.get("/api/health")
    async def health_check():
        return {"status": "ok", "version": __version__}

    # Serve frontend static files (if built)
    frontend_dist = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

    return app


# Default app instance
app = create_app()
