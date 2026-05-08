"""Dashboard metrics for ClawForge.

Aggregates project statistics, cost tracking, and quality metrics.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from clawforge.storage import get_project_store, ProjectContext


@dataclass
class ProjectMetrics:
    """Metrics for a single project."""

    project_id: str
    app_name: str
    github_repo: str
    status: str  # "active", "deployed", "has_issues", "building"

    # Counts
    file_count: int = 0
    dart_file_count: int = 0
    iteration_count: int = 0
    message_count: int = 0

    # Cost
    total_cost_cents: int = 0

    # Quality (from last validation)
    quality_score: float | None = None
    error_count: int = 0
    warning_count: int = 0

    # Timestamps
    created_at: str = ""
    updated_at: str = ""
    last_build_at: str | None = None

    # Preview
    preview_url: str | None = None
    build_status: str = "unknown"  # "success", "failed", "building", "unknown"


@dataclass
class DashboardMetrics:
    """Aggregate metrics for the dashboard."""

    # Project counts
    total_projects: int = 0
    active_projects: int = 0
    deployed_projects: int = 0
    projects_with_issues: int = 0

    # Cost tracking
    total_cost_cents: int = 0
    cost_this_week_cents: int = 0
    cost_today_cents: int = 0
    average_cost_per_project_cents: int = 0

    # Activity
    total_iterations: int = 0
    total_messages: int = 0
    total_files_generated: int = 0

    # Quality
    average_quality_score: float | None = None
    projects_with_errors: int = 0

    # Time range
    projects_created_this_week: int = 0
    projects_created_today: int = 0

    # Recent activity
    recent_projects: list[dict] = field(default_factory=list)


async def get_project_metrics(project_id: str) -> ProjectMetrics | None:
    """Get metrics for a single project."""
    store = get_project_store()
    project = await store.load(project_id)

    if not project:
        return None

    # Count files
    dart_files = [f for f in project.files if f.get("path", "").endswith(".dart")]

    # Determine status
    status = _determine_project_status(project)

    return ProjectMetrics(
        project_id=project.project_id,
        app_name=project.app_name,
        github_repo=project.github_repo,
        status=status,
        file_count=len(project.files),
        dart_file_count=len(dart_files),
        iteration_count=project.iteration_count,
        message_count=len(project.messages),
        total_cost_cents=project.total_cost_cents,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


async def get_dashboard_metrics(user_id: str | None = None) -> DashboardMetrics:
    """Get aggregate dashboard metrics.

    Args:
        user_id: If provided, only include metrics for this user's projects.
    """
    store = get_project_store()
    projects_list = await store.list_projects(user_id=user_id)

    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    metrics = DashboardMetrics()
    metrics.total_projects = len(projects_list)

    quality_scores = []

    for project_summary in projects_list:
        project_id = project_summary.get("project_id")
        if not project_id:
            continue

        # Load full project for detailed metrics
        project = await store.load(project_id)
        if not project:
            continue

        # Count statuses
        status = _determine_project_status(project)
        if status == "active":
            metrics.active_projects += 1
        elif status == "deployed":
            metrics.deployed_projects += 1
        elif status == "has_issues":
            metrics.projects_with_issues += 1

        # Cost tracking
        metrics.total_cost_cents += project.total_cost_cents

        # Check if created this week/today
        try:
            created = datetime.fromisoformat(project.created_at.replace("Z", "+00:00"))
            if created.replace(tzinfo=None) > week_ago:
                metrics.projects_created_this_week += 1
                metrics.cost_this_week_cents += project.total_cost_cents
            if created.replace(tzinfo=None) > today_start:
                metrics.projects_created_today += 1
                metrics.cost_today_cents += project.total_cost_cents
        except (ValueError, AttributeError):
            pass

        # Activity counts
        metrics.total_iterations += project.iteration_count
        metrics.total_messages += len(project.messages)
        metrics.total_files_generated += len(project.files)

    # Calculate averages
    if metrics.total_projects > 0:
        metrics.average_cost_per_project_cents = metrics.total_cost_cents // metrics.total_projects

    if quality_scores:
        metrics.average_quality_score = sum(quality_scores) / len(quality_scores)

    # Recent projects (top 5)
    metrics.recent_projects = projects_list[:5]

    return metrics


def _determine_project_status(project: ProjectContext) -> str:
    """Determine project status based on its state."""
    # Check if it has a GitHub repo (deployed)
    if project.github_repo:
        # Check if there are error messages
        has_errors = any(
            "error" in (m.content or "").lower()
            for m in project.messages
            if m.role == "assistant"
        )
        if has_errors:
            return "has_issues"
        return "deployed"

    # Check if it's been recently updated (active)
    try:
        updated = datetime.fromisoformat(project.updated_at.replace("Z", "+00:00"))
        if datetime.utcnow() - updated.replace(tzinfo=None) < timedelta(hours=24):
            return "active"
    except (ValueError, AttributeError):
        pass

    return "active"


async def get_cost_breakdown(days: int = 30) -> dict[str, Any]:
    """Get cost breakdown by day for the last N days."""
    store = get_project_store()
    projects_list = await store.list_projects()

    # Build daily cost map
    daily_costs: dict[str, int] = {}
    now = datetime.utcnow()

    for project_summary in projects_list:
        project = await store.load(project_summary.get("project_id", ""))
        if not project:
            continue

        try:
            created = datetime.fromisoformat(project.created_at.replace("Z", "+00:00"))
            date_key = created.strftime("%Y-%m-%d")
            daily_costs[date_key] = daily_costs.get(date_key, 0) + project.total_cost_cents
        except (ValueError, AttributeError):
            continue

    # Fill in missing days with 0
    result = []
    for i in range(days):
        date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        result.append({
            "date": date,
            "cost_cents": daily_costs.get(date, 0),
        })

    return {
        "days": days,
        "daily_costs": list(reversed(result)),
        "total_cents": sum(d["cost_cents"] for d in result),
    }


async def get_project_activity(project_id: str) -> dict[str, Any]:
    """Get activity timeline for a project."""
    store = get_project_store()
    project = await store.load(project_id)

    if not project:
        return {"error": "Project not found"}

    activity = []

    # Initial creation
    activity.append({
        "type": "created",
        "timestamp": project.created_at,
        "description": f"Project '{project.app_name}' created",
    })

    # Messages as activity
    for msg in project.messages:
        if msg.role == "user":
            activity.append({
                "type": "user_message",
                "timestamp": msg.timestamp,
                "description": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content,
            })
        else:
            activity.append({
                "type": "assistant_response",
                "timestamp": msg.timestamp,
                "description": f"Made changes to {len(msg.files_changed)} file(s)" if msg.files_changed else "Responded",
                "files_changed": msg.files_changed,
            })

    return {
        "project_id": project_id,
        "app_name": project.app_name,
        "activity_count": len(activity),
        "activity": sorted(activity, key=lambda x: x.get("timestamp", ""), reverse=True),
    }
