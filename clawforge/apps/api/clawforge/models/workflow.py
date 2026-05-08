"""Workflow models for API requests and responses."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    """Workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStep(BaseModel):
    """Individual workflow step data."""

    step_number: int = Field(..., ge=1, le=10)
    name: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    data: dict[str, Any] = Field(default_factory=dict)
    output: str | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class WorkflowCreate(BaseModel):
    """Request body for creating a new workflow."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    steps: list[WorkflowStep] = Field(default_factory=list)

    # GitHub settings
    github_repo_name: str | None = None
    github_repo_private: bool = True

    # User preferences
    user_email: str | None = None  # For notifications


class WorkflowResponse(BaseModel):
    """Response body for workflow operations."""

    id: str
    name: str
    status: WorkflowStatus
    current_step: int
    total_steps: int
    cost_cents: int  # Total cost in cents

    # Optional detailed info
    steps: list[WorkflowStep] | None = None
    github_repo_url: str | None = None
    error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WorkflowStepUpdate(BaseModel):
    """Request body for updating a workflow step."""

    data: dict[str, Any]


# ============ New models for workflow execution ============

class BasicInputs(BaseModel):
    """Basic user inputs for app generation."""

    app_idea: str = Field(..., min_length=10, description="Description of the app idea")
    target_users: str = Field(..., min_length=5, description="Target user description")
    features: str = Field(..., min_length=10, description="List of features")
    ui_design: str = Field(..., min_length=3, description="UI design style")


class ArchitectureOptions(BaseModel):
    """Architecture configuration options."""

    state: str = Field(default="riverpod", description="State management library")
    nav: str = Field(default="go_router", description="Navigation library")
    db: str = Field(default="drift", description="Database library")


class BackendOptions(BaseModel):
    """Backend configuration options."""

    type: str = Field(default="offline-first", description="Backend type")


class CodeSettingsOptions(BaseModel):
    """Code generation settings."""

    defensive: bool = Field(default=True, description="Enable defensive coding prompts")
    tests: str = Field(default="basic", description="Test coverage level")
    docs: str = Field(default="inline", description="Documentation level")


class QualityOptions(BaseModel):
    """Quality and accessibility options."""

    a11y: str = Field(default="standard", description="Accessibility level")
    performance: str = Field(default="balanced", description="Performance optimization level")


class AdvancedOptions(BaseModel):
    """Advanced configuration options."""

    architecture: ArchitectureOptions = Field(default_factory=ArchitectureOptions)
    backend: BackendOptions = Field(default_factory=BackendOptions)
    code_settings: CodeSettingsOptions = Field(default_factory=CodeSettingsOptions)
    quality: QualityOptions = Field(default_factory=QualityOptions)
    environment: dict[str, str] = Field(default_factory=dict, description="Environment variables")


class GitHubConfig(BaseModel):
    """GitHub repository configuration."""

    token: str = Field(..., min_length=10, description="GitHub personal access token")
    repo_name: str = Field(..., min_length=1, description="Repository name")
    create_new: bool = Field(default=True, description="Create new repository")


class WorkflowRunRequest(BaseModel):
    """Request body for running a full workflow."""

    basic_inputs: BasicInputs
    advanced_options: AdvancedOptions = Field(default_factory=AdvancedOptions)
    github_config: GitHubConfig


class WorkflowRunResponse(BaseModel):
    """Response for workflow execution."""

    workflow_id: str
    status: WorkflowStatus
    message: str
    github_repo_url: str | None = None
    pr_url: str | None = None
    steps_completed: list[str] = Field(default_factory=list)
    error: str | None = None
    cost_cents: int = 0
    project_id: str | None = None  # For iterative development


# ============ Chat models for iterative development ============

class ChatMessageRequest(BaseModel):
    """Request body for chat message."""

    message: str = Field(..., min_length=1, description="User message/request")


class ChatMessageResponse(BaseModel):
    """Response for chat message."""

    message_id: str
    assistant_message: str
    files_changed: list[str] = Field(default_factory=list)
    cost_cents: int = 0
    error: str | None = None


class ProjectSummary(BaseModel):
    """Summary of a project for listing."""

    project_id: str
    app_name: str
    github_repo: str = ""
    created_at: str
    updated_at: str
    iteration_count: int = 0


class ProjectDetail(BaseModel):
    """Full project details."""

    project_id: str
    app_name: str
    app_idea: str
    target_users: str = ""
    features: str = ""
    ui_design: str = ""
    github_repo: str = ""
    files: list[dict[str, str]] = Field(default_factory=list)
    messages: list[dict[str, Any]] = Field(default_factory=list)
    full_spec: dict[str, Any] = Field(default_factory=dict)
    message_count: int = 0
    iteration_count: int = 0
    total_cost_cents: int = 0
    created_at: str
    updated_at: str
