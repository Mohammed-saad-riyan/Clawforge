"""Dashboard module for ClawForge.

Provides project statistics, metrics aggregation, and monitoring data.
"""

from clawforge.dashboard.metrics import (
    DashboardMetrics,
    ProjectMetrics,
    get_dashboard_metrics,
    get_project_metrics,
)

__all__ = [
    "DashboardMetrics",
    "ProjectMetrics",
    "get_dashboard_metrics",
    "get_project_metrics",
]
