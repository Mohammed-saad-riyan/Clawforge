"""Project storage for iterative development.

Stores generated project context so users can iterate on their apps
through chat-based refinements.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any
import hashlib


@dataclass
class ChatMessage:
    """A single chat message in the conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    files_changed: list[str] = field(default_factory=list)


@dataclass
class ProjectContext:
    """Full context for a generated project."""

    # Identifiers
    project_id: str
    user_id: str = ""  # User who owns this project
    github_repo: str = ""

    # Original specification
    app_name: str = ""
    app_idea: str = ""
    target_users: str = ""
    features: str = ""
    ui_design: str = ""
    full_spec: dict = field(default_factory=dict)

    # Generated code
    files: list[dict] = field(default_factory=list)  # [{path, content}]

    # Conversation history
    messages: list[ChatMessage] = field(default_factory=list)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    total_cost_cents: int = 0
    iteration_count: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert ChatMessage objects
        data["messages"] = [
            asdict(m) if isinstance(m, ChatMessage) else m
            for m in self.messages
        ]
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectContext":
        """Create from dictionary."""
        messages = [
            ChatMessage(**m) if isinstance(m, dict) else m
            for m in data.get("messages", [])
        ]
        data["messages"] = messages
        return cls(**data)


class ProjectStore:
    """Simple file-based project storage.

    In production, this should be replaced with a proper database
    (PostgreSQL, MongoDB, etc.)
    """

    def __init__(self, storage_dir: str = "./project_store"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_project_path(self, project_id: str) -> Path:
        """Get path to project file."""
        return self.storage_dir / f"{project_id}.json"

    def generate_project_id(self, app_name: str, github_repo: str = "") -> str:
        """Generate a unique project ID."""
        unique_str = f"{app_name}:{github_repo}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(unique_str.encode()).hexdigest()[:12]

    async def save(self, project: ProjectContext) -> None:
        """Save project to storage."""
        project.updated_at = datetime.utcnow().isoformat()
        path = self._get_project_path(project.project_id)
        path.write_text(json.dumps(project.to_dict(), indent=2))

    async def load(self, project_id: str) -> ProjectContext | None:
        """Load project from storage."""
        path = self._get_project_path(project_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        return ProjectContext.from_dict(data)

    async def delete(self, project_id: str) -> bool:
        """Delete project from storage."""
        path = self._get_project_path(project_id)
        if path.exists():
            path.unlink()
            return True
        return False

    async def list_projects(self, user_id: str | None = None) -> list[dict]:
        """List all stored projects (metadata only).

        Args:
            user_id: If provided, only return projects owned by this user.
        """
        projects = []
        for path in self.storage_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text())
                # Filter by user_id if provided
                if user_id and data.get("user_id") != user_id:
                    continue
                projects.append({
                    "id": data.get("project_id"),  # Frontend expects 'id'
                    "project_id": data.get("project_id"),  # Keep for compatibility
                    "app_name": data.get("app_name"),
                    "app_idea": data.get("app_idea", ""),
                    "github_repo": data.get("github_repo"),
                    "total_cost_cents": data.get("total_cost_cents", 0),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                    "iteration_count": data.get("iteration_count", 0),
                })
            except Exception:
                continue
        return sorted(projects, key=lambda x: x.get("updated_at", ""), reverse=True)

    async def find_by_repo(self, github_repo: str) -> ProjectContext | None:
        """Find project by GitHub repository."""
        for path in self.storage_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text())
                if data.get("github_repo") == github_repo:
                    return ProjectContext.from_dict(data)
            except Exception:
                continue
        return None


# Global store instance
_store: ProjectStore | None = None


def get_project_store() -> ProjectStore:
    """Get the global project store instance."""
    global _store
    if _store is None:
        _store = ProjectStore()
    return _store
