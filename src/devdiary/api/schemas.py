"""Pydantic schemas for API request/response models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ---- Project schemas ----

class ProjectCreate(BaseModel):
    """Request schema for creating a project."""

    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    repo_path: str = Field(..., min_length=1, description="Local Git repository path")
    description: str = Field("", description="Project description")


class ProjectResponse(BaseModel):
    """Response schema for a project."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    repo_path: str
    description: str
    last_scanned: Optional[datetime] = None
    total_commits: int = 0
    languages: dict = {}
    created_at: datetime


class ProjectStatsResponse(BaseModel):
    """Response schema for project statistics."""

    project: ProjectResponse
    language_distribution: list[dict] = []
    commit_trend: list[dict] = []
    recent_commits: list[dict] = []


# ---- Diary schemas ----

class DiaryResponse(BaseModel):
    """Response schema for a diary entry."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    summary: str
    style: str
    date_from: datetime
    date_to: datetime
    project_id: int
    project_name: str = ""
    commit_count: int = 0
    insertions: int = 0
    deletions: int = 0
    tech_stack: list = []
    ai_provider: str = ""
    ai_model: str = ""
    tokens_used: int = 0
    created_at: datetime


class DiaryListResponse(BaseModel):
    """Response schema for paginated diary list."""

    items: list[DiaryResponse]
    total: int
    page: int
    page_size: int


class DiaryUpdate(BaseModel):
    """Request schema for updating a diary entry."""

    title: Optional[str] = Field(None, min_length=1, max_length=500, description="Diary title")
    content: Optional[str] = Field(None, description="Diary content")
    summary: Optional[str] = Field(None, description="Diary summary")
    style: Optional[str] = Field(None, description="Writing style: diary/blog/report")


class BatchDeleteRequest(BaseModel):
    """Request schema for batch deleting diaries."""

    ids: list[int] = Field(..., min_length=1, description="List of diary IDs to delete")


class BatchDeleteResponse(BaseModel):
    """Response schema for batch delete operation."""

    deleted_count: int = Field(..., description="Number of diaries deleted")


class GenerateRequest(BaseModel):
    """Request schema for generating a diary."""

    project_id: int = Field(..., description="Project ID to generate diary for")
    date_from: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    style: str = Field("diary", description="Writing style: diary/blog/report")
    output_format: str = Field("markdown", description="Output format: markdown/html/both")


class GenerateResponse(BaseModel):
    """Response schema for diary generation."""

    diary: DiaryResponse
    files_saved: list[str] = []
    tokens_used: int = 0
    message: str = "Diary generated successfully"


# ---- Stats schemas ----

class StatsOverviewResponse(BaseModel):
    """Response schema for dashboard overview statistics."""

    total_diaries: int = 0
    total_commits: int = 0
    total_projects: int = 0
    total_insertions: int = 0
    total_deletions: int = 0
    this_week_diaries: int = 0
    this_week_commits: int = 0
    recent_diaries: list[DiaryResponse] = []


class ExportResponse(BaseModel):
    """Response schema for diary export."""

    content: str
    filename: str
    content_type: str


# ---- Stats schemas ----

class CommitTrendItem(BaseModel):
    """Single data point in commit trend."""

    date: str = Field(..., description="Date string (YYYY-MM-DD)")
    commit_count: int = Field(0, description="Number of commits on this date")
    insertions: int = Field(0, description="Lines inserted on this date")
    deletions: int = Field(0, description="Lines deleted on this date")


class CommitTrendResponse(BaseModel):
    """Response schema for commit trend API."""

    items: list[CommitTrendItem] = []


class HeatmapItem(BaseModel):
    """Single cell in the commit heatmap."""

    hour: int = Field(..., ge=0, le=23, description="Hour of day (0-23)")
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    count: int = Field(0, description="Number of commits")


class HeatmapResponse(BaseModel):
    """Response schema for heatmap API."""

    items: list[HeatmapItem] = []


class InsightsResponse(BaseModel):
    """Response schema for developer insights."""

    most_active_hour: str = Field("", description="Most active hour range, e.g. '14:00-15:00'")
    most_active_day: str = Field("", description="Most active day of week, e.g. '周三'")
    most_active_project: str = Field("", description="Most active project name")
    current_streak: int = Field(0, description="Current consecutive active days")
    total_diaries: int = Field(0, description="Total number of diaries")
    this_month_commits: int = Field(0, description="Number of commits this month")


# ---- Settings schemas ----

class SettingsResponse(BaseModel):
    """Response schema for current settings."""

    ai_provider: str = ""
    api_key_masked: str = ""
    model: str = ""
    base_url: Optional[str] = None
    repos: list[dict] = []
    output_dir: str = ""
    output_format: str = ""
    output_style: str = ""


class SettingsUpdate(BaseModel):
    """Request schema for updating settings."""

    ai_provider: Optional[str] = Field(None, description="AI provider name")
    api_key: Optional[str] = Field(None, description="AI API key")
    model: Optional[str] = Field(None, description="AI model name")
    base_url: Optional[str] = Field(None, description="AI API base URL")
    output_dir: Optional[str] = Field(None, description="Output directory")
    output_format: Optional[str] = Field(None, description="Output format: markdown/html/both")
    output_style: Optional[str] = Field(None, description="Writing style: diary/blog/report")
