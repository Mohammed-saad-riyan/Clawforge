"""Supabase database storage for ClawForge projects.

Replaces the file-based ProjectStore with Supabase tables.

Required Tables (create in Supabase Dashboard):

-- Users table (managed by Supabase Auth, but we extend it)
create table public.user_profiles (
    id uuid references auth.users on delete cascade primary key,
    email text,
    full_name text,
    avatar_url text,
    created_at timestamp with time zone default timezone('utc'::text, now()),
    updated_at timestamp with time zone default timezone('utc'::text, now())
);

-- Projects table
create table public.projects (
    id text primary key,
    user_id uuid references auth.users on delete cascade,
    app_name text not null,
    app_idea text,
    target_users text,
    features text,
    ui_design text,
    full_spec jsonb default '{}'::jsonb,
    github_repo text,
    total_cost_cents integer default 0,
    iteration_count integer default 0,
    created_at timestamp with time zone default timezone('utc'::text, now()),
    updated_at timestamp with time zone default timezone('utc'::text, now())
);

-- Project files table
create table public.project_files (
    id uuid default gen_random_uuid() primary key,
    project_id text references public.projects on delete cascade,
    path text not null,
    content text,
    created_at timestamp with time zone default timezone('utc'::text, now()),
    updated_at timestamp with time zone default timezone('utc'::text, now()),
    unique(project_id, path)
);

-- Chat messages table
create table public.chat_messages (
    id uuid default gen_random_uuid() primary key,
    project_id text references public.projects on delete cascade,
    role text not null check (role in ('user', 'assistant')),
    content text not null,
    files_changed text[] default '{}',
    created_at timestamp with time zone default timezone('utc'::text, now())
);

-- Enable RLS
alter table public.user_profiles enable row level security;
alter table public.projects enable row level security;
alter table public.project_files enable row level security;
alter table public.chat_messages enable row level security;

-- RLS Policies (users can only access their own data)
create policy "Users can view own profile" on public.user_profiles
    for select using (auth.uid() = id);

create policy "Users can update own profile" on public.user_profiles
    for update using (auth.uid() = id);

create policy "Users can view own projects" on public.projects
    for select using (auth.uid() = user_id);

create policy "Users can insert own projects" on public.projects
    for insert with check (auth.uid() = user_id);

create policy "Users can update own projects" on public.projects
    for update using (auth.uid() = user_id);

create policy "Users can delete own projects" on public.projects
    for delete using (auth.uid() = user_id);

-- Similar policies for project_files and chat_messages...
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any

from clawforge.supabase.client import get_supabase_admin_client
from clawforge.storage.project_store import ProjectContext, ChatMessage


class SupabaseProjectStore:
    """Supabase-backed project storage.

    Uses the service key to bypass RLS for server-side operations.
    For user-scoped operations, use the anon client with proper auth.
    """

    def __init__(self):
        self.client = get_supabase_admin_client()

    def generate_project_id(self, app_name: str, github_repo: str = "") -> str:
        """Generate a unique project ID."""
        import hashlib
        unique_str = f"{app_name}:{github_repo}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(unique_str.encode()).hexdigest()[:12]

    async def save(self, project: ProjectContext, user_id: str | None = None) -> None:
        """Save project to Supabase.

        Args:
            project: Project context to save
            user_id: Optional user ID for ownership (required for new projects)
        """
        now = datetime.utcnow().isoformat()

        # Check if project exists
        existing = self.client.table("projects").select("id").eq(
            "id", project.project_id
        ).execute()

        project_data = {
            "id": project.project_id,
            "app_name": project.app_name,
            "app_idea": project.app_idea,
            "target_users": project.target_users,
            "features": project.features,
            "ui_design": project.ui_design,
            "full_spec": project.full_spec,
            "github_repo": project.github_repo,
            "total_cost_cents": project.total_cost_cents,
            "iteration_count": project.iteration_count,
            "updated_at": now,
        }

        if existing.data:
            # Update existing project
            self.client.table("projects").update(project_data).eq(
                "id", project.project_id
            ).execute()
        else:
            # Insert new project
            project_data["user_id"] = user_id
            project_data["created_at"] = project.created_at or now
            self.client.table("projects").insert(project_data).execute()

        # Save files (upsert)
        if project.files:
            for file_info in project.files:
                file_data = {
                    "project_id": project.project_id,
                    "path": file_info.get("path", ""),
                    "content": file_info.get("content", ""),
                    "updated_at": now,
                }

                # Try to upsert (insert or update on conflict)
                self.client.table("project_files").upsert(
                    file_data,
                    on_conflict="project_id,path",
                ).execute()

        # Save new messages
        for msg in project.messages:
            # Check if message already exists (by timestamp)
            existing_msg = self.client.table("chat_messages").select("id").eq(
                "project_id", project.project_id
            ).eq("created_at", msg.timestamp).execute()

            if not existing_msg.data:
                msg_data = {
                    "project_id": project.project_id,
                    "role": msg.role,
                    "content": msg.content,
                    "files_changed": msg.files_changed or [],
                    "created_at": msg.timestamp,
                }
                self.client.table("chat_messages").insert(msg_data).execute()

    async def load(self, project_id: str) -> ProjectContext | None:
        """Load project from Supabase."""
        # Get project
        result = self.client.table("projects").select("*").eq(
            "id", project_id
        ).execute()

        if not result.data:
            return None

        project_data = result.data[0]

        # Get files
        files_result = self.client.table("project_files").select(
            "path, content"
        ).eq("project_id", project_id).execute()

        files = [
            {"path": f["path"], "content": f["content"]}
            for f in files_result.data
        ]

        # Get messages
        messages_result = self.client.table("chat_messages").select(
            "role, content, files_changed, created_at"
        ).eq("project_id", project_id).order("created_at").execute()

        messages = [
            ChatMessage(
                role=m["role"],
                content=m["content"],
                files_changed=m.get("files_changed") or [],
                timestamp=m["created_at"],
            )
            for m in messages_result.data
        ]

        return ProjectContext(
            project_id=project_data["id"],
            github_repo=project_data.get("github_repo") or "",
            app_name=project_data.get("app_name") or "",
            app_idea=project_data.get("app_idea") or "",
            target_users=project_data.get("target_users") or "",
            features=project_data.get("features") or "",
            ui_design=project_data.get("ui_design") or "",
            full_spec=project_data.get("full_spec") or {},
            files=files,
            messages=messages,
            created_at=project_data.get("created_at") or "",
            updated_at=project_data.get("updated_at") or "",
            total_cost_cents=project_data.get("total_cost_cents") or 0,
            iteration_count=project_data.get("iteration_count") or 0,
        )

    async def delete(self, project_id: str) -> bool:
        """Delete project from Supabase."""
        # Files and messages will be deleted by CASCADE
        result = self.client.table("projects").delete().eq(
            "id", project_id
        ).execute()

        return len(result.data) > 0

    async def list_projects(self, user_id: str | None = None) -> list[dict]:
        """List all projects (optionally filtered by user)."""
        query = self.client.table("projects").select(
            "id, app_name, github_repo, created_at, updated_at, iteration_count, total_cost_cents"
        )

        if user_id:
            query = query.eq("user_id", user_id)

        result = query.order("updated_at", desc=True).execute()

        return [
            {
                "project_id": p["id"],
                "app_name": p["app_name"],
                "github_repo": p.get("github_repo") or "",
                "created_at": p["created_at"],
                "updated_at": p["updated_at"],
                "iteration_count": p.get("iteration_count") or 0,
                "total_cost_cents": p.get("total_cost_cents") or 0,
            }
            for p in result.data
        ]

    async def find_by_repo(self, github_repo: str) -> ProjectContext | None:
        """Find project by GitHub repository."""
        result = self.client.table("projects").select("id").eq(
            "github_repo", github_repo
        ).execute()

        if result.data:
            return await self.load(result.data[0]["id"])

        return None

    async def get_user_stats(self, user_id: str) -> dict:
        """Get statistics for a user's projects."""
        # Count projects
        projects = self.client.table("projects").select(
            "id, total_cost_cents, iteration_count"
        ).eq("user_id", user_id).execute()

        total_projects = len(projects.data)
        total_cost = sum(p.get("total_cost_cents", 0) for p in projects.data)
        total_iterations = sum(p.get("iteration_count", 0) for p in projects.data)

        # Count files
        if projects.data:
            project_ids = [p["id"] for p in projects.data]
            files = self.client.table("project_files").select(
                "id", count="exact"
            ).in_("project_id", project_ids).execute()
            total_files = files.count or 0
        else:
            total_files = 0

        return {
            "total_projects": total_projects,
            "total_cost_cents": total_cost,
            "total_iterations": total_iterations,
            "total_files": total_files,
        }


# Global store instance
_supabase_store: SupabaseProjectStore | None = None


def get_supabase_project_store() -> SupabaseProjectStore:
    """Get the global Supabase project store instance."""
    global _supabase_store
    if _supabase_store is None:
        _supabase_store = SupabaseProjectStore()
    return _supabase_store
