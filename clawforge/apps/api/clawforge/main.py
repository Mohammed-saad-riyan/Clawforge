"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware

from clawforge.config import get_settings
from clawforge.models.workflow import (
    WorkflowCreate,
    WorkflowResponse,
    WorkflowStatus,
    WorkflowRunRequest,
    WorkflowRunResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ProjectSummary,
    ProjectDetail,
)
from clawforge.graph.workflow import run_clawforge_workflow
from clawforge.storage import get_project_store, ProjectContext, ChatMessage
from clawforge.agents.refiner import RefinerAgent
from clawforge.preview import generate_preview
from clawforge.dashboard import get_dashboard_metrics, get_project_metrics
from clawforge.webhooks import GitHubWebhookHandler, verify_github_signature
from clawforge.components.library import get_component_library, ComponentCategory

# Supabase imports (optional - falls back to file storage if not configured)
try:
    from clawforge.supabase import get_auth_client, get_supabase_project_store
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    settings = get_settings()
    print(f"🔥 ClawForge API starting on {settings.api_host}:{settings.api_port}")
    print(f"📡 Local LLM: {'enabled' if settings.use_local_llm else 'disabled'}")
    yield
    # Shutdown
    print("👋 ClawForge API shutting down")


app = FastAPI(
    title="ClawForge API",
    description="AI-powered Flutter app generation from natural language",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "clawforge-api"}


@app.get("/api/v1/config")
async def get_config() -> dict[str, bool | str]:
    """Get public configuration (no secrets)."""
    settings = get_settings()
    return {
        "local_llm_enabled": settings.use_local_llm,
        "ollama_model": settings.ollama_model,
        "claude_model_routing": settings.claude_model_routing,
        "claude_model_coding": settings.claude_model_coding,
        "max_cost_per_workflow": str(settings.max_cost_per_workflow),
    }


@app.post("/api/v1/workflows", response_model=WorkflowResponse)
async def create_workflow(workflow: WorkflowCreate) -> WorkflowResponse:
    """Create a new workflow and start execution."""
    # TODO: Implement workflow creation with LangGraph
    return WorkflowResponse(
        id="wf_" + "0" * 24,
        name=workflow.name,
        status=WorkflowStatus.PENDING,
        current_step=0,
        total_steps=10,
        cost_cents=0,
    )


@app.get("/api/v1/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str) -> WorkflowResponse:
    """Get workflow status and details."""
    # TODO: Implement workflow retrieval
    return WorkflowResponse(
        id=workflow_id,
        name="Example Workflow",
        status=WorkflowStatus.PENDING,
        current_step=0,
        total_steps=10,
        cost_cents=0,
    )


@app.post("/api/v1/workflows/{workflow_id}/run")
async def run_workflow(workflow_id: str) -> dict[str, str]:
    """Start or resume workflow execution."""
    # TODO: Implement workflow execution with LangGraph
    return {"status": "started", "workflow_id": workflow_id}


@app.post("/api/v1/workflows/{workflow_id}/stop")
async def stop_workflow(workflow_id: str) -> dict[str, str]:
    """Stop workflow execution."""
    # TODO: Implement workflow stop
    return {"status": "stopped", "workflow_id": workflow_id}


@app.post("/api/workflow/run", response_model=WorkflowRunResponse)
async def run_workflow_full(
    request: WorkflowRunRequest,
    x_user_id: str | None = Header(None, alias="X-User-Id"),
) -> WorkflowRunResponse:
    """
    Run the full ClawForge workflow to generate a Flutter app.

    This endpoint:
    1. Takes user inputs (app idea, features, etc.)
    2. Runs through the multi-agent pipeline
    3. Generates Flutter code
    4. Pushes to GitHub and creates a PR
    """
    import uuid

    workflow_id = f"wf_{uuid.uuid4().hex[:24]}"

    try:
        # Run the LangGraph workflow
        result = await run_clawforge_workflow(
            basic_inputs=request.basic_inputs.model_dump(),
            advanced_options=request.advanced_options.model_dump(),
            github_config=request.github_config.model_dump(),
            user_id=x_user_id,
        )

        return WorkflowRunResponse(
            workflow_id=workflow_id,
            status=WorkflowStatus.COMPLETED if result.get("success") else WorkflowStatus.FAILED,
            message=result.get("message", "Workflow completed"),
            github_repo_url=result.get("github_repo_url"),
            pr_url=result.get("pr_url"),
            steps_completed=result.get("steps_completed", []),
            error=result.get("error"),
            cost_cents=result.get("cost_cents", 0),
            project_id=result.get("project_id"),  # For iterative development
        )
    except Exception as e:
        return WorkflowRunResponse(
            workflow_id=workflow_id,
            status=WorkflowStatus.FAILED,
            message="Workflow execution failed",
            error=str(e),
        )


# ============ Project & Chat Endpoints for Iterative Development ============

@app.get("/api/v1/projects", response_model=list[ProjectSummary])
async def list_projects(x_user_id: str | None = Header(None, alias="X-User-Id")) -> list[ProjectSummary]:
    """List all stored projects for the current user."""
    store = get_project_store()
    projects = await store.list_projects(user_id=x_user_id)
    return [ProjectSummary(**p) for p in projects]


@app.get("/api/v1/projects/{project_id}", response_model=ProjectDetail)
async def get_project(project_id: str) -> ProjectDetail:
    """Get project details."""
    store = get_project_store()
    project = await store.load(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectDetail(
        project_id=project.project_id,
        app_name=project.app_name,
        app_idea=project.app_idea,
        target_users=getattr(project, 'target_users', ''),
        features=getattr(project, 'features', ''),
        ui_design=getattr(project, 'ui_design', ''),
        github_repo=project.github_repo,
        files=project.files,
        messages=[
            {
                "id": f"msg_{i}",
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "files_changed": msg.files_changed or [],
            }
            for i, msg in enumerate(project.messages)
        ],
        full_spec=getattr(project, 'full_spec', {}),
        message_count=len(project.messages),
        iteration_count=project.iteration_count,
        total_cost_cents=project.total_cost_cents,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@app.post("/api/v1/projects/{project_id}/chat", response_model=ChatMessageResponse)
async def chat_with_project(project_id: str, request: ChatMessageRequest) -> ChatMessageResponse:
    """
    Send a chat message to refine the project.

    This allows iterative development of the generated app.
    """
    import uuid

    store = get_project_store()
    project = await store.load(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    message_id = f"msg_{uuid.uuid4().hex[:12]}"

    # Add user message to history
    user_message = ChatMessage(
        role="user",
        content=request.message,
    )
    project.messages.append(user_message)

    # Run refiner agent
    refiner = RefinerAgent()
    result = await refiner.execute({
        "user_request": request.message,
        "files": project.files,
        "spec": project.full_spec,
        "conversation_history": [
            {"role": m.role, "content": m.content}
            for m in project.messages[-10:]  # Last 10 messages
        ],
    })

    if result.success:
        # Update project with new files
        output = result.output
        project.files = output.get("merged_files", project.files)
        project.iteration_count += 1
        project.total_cost_cents += result.cost_cents

        # Add assistant message to history
        assistant_message = ChatMessage(
            role="assistant",
            content=output.get("explanation", "Changes applied."),
            files_changed=output.get("files_changed", []),
        )
        project.messages.append(assistant_message)

        # Save updated project
        await store.save(project)

        return ChatMessageResponse(
            message_id=message_id,
            assistant_message=output.get("explanation", "Changes applied."),
            files_changed=output.get("files_changed", []),
            cost_cents=result.cost_cents,
        )
    else:
        # Add error message
        assistant_message = ChatMessage(
            role="assistant",
            content=f"Sorry, I couldn't process that request: {result.error}",
        )
        project.messages.append(assistant_message)
        await store.save(project)

        return ChatMessageResponse(
            message_id=message_id,
            assistant_message=f"Sorry, I couldn't process that request.",
            error=result.error,
        )


@app.delete("/api/v1/projects/{project_id}")
async def delete_project(project_id: str) -> dict[str, str]:
    """Delete a project."""
    store = get_project_store()
    deleted = await store.delete(project_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")

    return {"status": "deleted", "project_id": project_id}


@app.post("/api/v1/projects/{project_id}/push")
async def push_project_changes(project_id: str) -> dict[str, Any]:
    """
    Push project changes to GitHub.

    Creates a new PR with the latest changes.
    """
    store = get_project_store()
    project = await store.load(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.github_repo:
        raise HTTPException(status_code=400, detail="No GitHub repository linked")

    # TODO: Implement push to GitHub
    # This would use the GitHubAgent to push changes

    return {
        "status": "pending",
        "message": "Push to GitHub not yet implemented",
        "project_id": project_id,
    }


@app.post("/api/v1/projects/{project_id}/preview")
async def generate_project_preview(project_id: str) -> dict[str, Any]:
    """
    Generate a Flutter web preview of the project.

    This builds the Flutter web version and returns build status.
    For full deployment, VERCEL_TOKEN must be set.
    """
    store = get_project_store()
    project = await store.load(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.files:
        raise HTTPException(status_code=400, detail="No files in project")

    print(f"🌐 Generating preview for {project.app_name}...")

    result = await generate_preview(
        files=project.files,
        app_name=project.app_name,
        deploy=False,  # Don't deploy by default
    )

    return {
        "success": result.success,
        "preview_url": result.preview_url or None,
        "build_time_seconds": result.build_time_seconds,
        "error": result.error or None,
        "project_id": project_id,
    }


@app.get("/api/v1/projects/{project_id}/files")
async def get_project_files(project_id: str) -> dict[str, Any]:
    """
    Get all files in a project.

    Returns the complete file list for download or review.
    """
    store = get_project_store()
    project = await store.load(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "project_id": project_id,
        "app_name": project.app_name,
        "file_count": len(project.files),
        "files": project.files,
    }


@app.get("/api/v1/projects/{project_id}/messages")
async def get_project_messages(project_id: str) -> dict[str, Any]:
    """
    Get chat message history for a project.
    """
    store = get_project_store()
    project = await store.load(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "project_id": project_id,
        "message_count": len(project.messages),
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "files_changed": msg.files_changed,
            }
            for msg in project.messages
        ],
    }


# ============ Authentication Endpoints (Supabase) ============

@app.post("/api/v1/auth/signup")
async def signup(
    email: str,
    password: str,
    full_name: str | None = None,
) -> dict[str, Any]:
    """
    Sign up a new user with email and password.

    Requires Supabase to be configured.
    """
    settings = get_settings()

    if not settings.supabase_url:
        raise HTTPException(status_code=503, detail="Authentication not configured")

    auth = get_auth_client()
    user_metadata = {"full_name": full_name} if full_name else None

    user, error = await auth.sign_up(email, password, user_metadata)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return {
        "success": True,
        "message": "Account created. Please check your email to confirm.",
        "user": {
            "id": user.id,
            "email": user.email,
            "email_confirmed": user.email_confirmed,
        } if user else None,
    }


@app.post("/api/v1/auth/login")
async def login(
    email: str,
    password: str,
) -> dict[str, Any]:
    """
    Log in with email and password.

    Returns access token and refresh token.
    """
    settings = get_settings()

    if not settings.supabase_url:
        raise HTTPException(status_code=503, detail="Authentication not configured")

    auth = get_auth_client()
    session, error = await auth.sign_in(email, password)

    if error:
        raise HTTPException(status_code=401, detail=error)

    return {
        "success": True,
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "expires_in": session.expires_in,
        "token_type": session.token_type,
        "user": {
            "id": session.user.id,
            "email": session.user.email,
        } if session.user else None,
    }


@app.post("/api/v1/auth/logout")
async def logout() -> dict[str, Any]:
    """Log out the current user."""
    settings = get_settings()

    if not settings.supabase_url:
        raise HTTPException(status_code=503, detail="Authentication not configured")

    auth = get_auth_client()
    success, error = await auth.sign_out()

    if error:
        raise HTTPException(status_code=400, detail=error)

    return {"success": True, "message": "Logged out successfully"}


@app.post("/api/v1/auth/refresh")
async def refresh_token(refresh_token: str) -> dict[str, Any]:
    """Refresh an expired access token."""
    settings = get_settings()

    if not settings.supabase_url:
        raise HTTPException(status_code=503, detail="Authentication not configured")

    auth = get_auth_client()
    session, error = await auth.refresh_session(refresh_token)

    if error:
        raise HTTPException(status_code=401, detail=error)

    return {
        "success": True,
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "expires_in": session.expires_in,
    }


@app.get("/api/v1/auth/me")
async def get_current_user(authorization: str | None = None) -> dict[str, Any]:
    """Get current user from access token."""
    settings = get_settings()

    if not settings.supabase_url:
        raise HTTPException(status_code=503, detail="Authentication not configured")

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    access_token = authorization.replace("Bearer ", "")
    auth = get_auth_client()
    user, error = await auth.get_user(access_token)

    if error:
        raise HTTPException(status_code=401, detail=error)

    return {
        "id": user.id,
        "email": user.email,
        "email_confirmed": user.email_confirmed,
        "created_at": user.created_at,
        "user_metadata": user.user_metadata,
    }


@app.post("/api/v1/auth/forgot-password")
async def forgot_password(email: str) -> dict[str, Any]:
    """Send password reset email."""
    settings = get_settings()

    if not settings.supabase_url:
        raise HTTPException(status_code=503, detail="Authentication not configured")

    auth = get_auth_client()
    success, error = await auth.reset_password(email)

    # Always return success to prevent email enumeration
    return {
        "success": True,
        "message": "If an account exists with this email, a reset link has been sent.",
    }


# ============ Dashboard Endpoints ============

@app.get("/api/v1/dashboard")
async def get_dashboard(x_user_id: str | None = Header(None, alias="X-User-Id")) -> dict[str, Any]:
    """
    Get dashboard metrics including project counts, cost tracking, and activity.

    Pass X-User-Id header to filter by user.
    """
    metrics = await get_dashboard_metrics(user_id=x_user_id)
    return {
        "total_projects": metrics.total_projects,
        "active_projects": metrics.active_projects,
        "deployed_projects": metrics.deployed_projects,
        "projects_with_issues": metrics.projects_with_issues,
        "total_cost_cents": metrics.total_cost_cents,
        "cost_this_week_cents": metrics.cost_this_week_cents,
        "cost_today_cents": metrics.cost_today_cents,
        "average_cost_per_project_cents": metrics.average_cost_per_project_cents,
        "total_iterations": metrics.total_iterations,
        "total_messages": metrics.total_messages,
        "total_files_generated": metrics.total_files_generated,
        "projects_created_this_week": metrics.projects_created_this_week,
        "projects_created_today": metrics.projects_created_today,
        "recent_projects": metrics.recent_projects,
    }


@app.get("/api/v1/dashboard/projects/{project_id}/metrics")
async def get_project_metrics_endpoint(project_id: str) -> dict[str, Any]:
    """
    Get detailed metrics for a specific project.
    """
    metrics = await get_project_metrics(project_id)

    if not metrics:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "project_id": metrics.project_id,
        "app_name": metrics.app_name,
        "github_repo": metrics.github_repo,
        "status": metrics.status,
        "file_count": metrics.file_count,
        "dart_file_count": metrics.dart_file_count,
        "iteration_count": metrics.iteration_count,
        "message_count": metrics.message_count,
        "total_cost_cents": metrics.total_cost_cents,
        "created_at": metrics.created_at,
        "updated_at": metrics.updated_at,
    }


@app.get("/api/v1/dashboard/cost-breakdown")
async def get_cost_breakdown_endpoint(days: int = 30) -> dict[str, Any]:
    """
    Get cost breakdown by day for the last N days.
    """
    from clawforge.dashboard.metrics import get_cost_breakdown
    return await get_cost_breakdown(days=min(days, 90))  # Cap at 90 days


@app.get("/api/v1/dashboard/projects/{project_id}/activity")
async def get_project_activity_endpoint(project_id: str) -> dict[str, Any]:
    """
    Get activity timeline for a project.
    """
    from clawforge.dashboard.metrics import get_project_activity
    result = await get_project_activity(project_id)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


# ============ GitHub Webhook Endpoints ============

@app.post("/webhook/github")
async def github_webhook(
    request: Any,
) -> dict[str, Any]:
    """
    Handle GitHub webhook events.

    Supported events:
    - issues.opened: Auto-analyze issues and suggest fixes
    - pull_request.opened: Acknowledge PRs
    - push: Track code changes
    - ping: Webhook setup verification

    Configure in GitHub:
    1. Go to repo Settings > Webhooks > Add webhook
    2. Payload URL: https://your-api.com/webhook/github
    3. Content type: application/json
    4. Secret: (optional) for signature verification
    5. Events: Select "Issues", "Pull requests", "Pushes"
    """
    from fastapi import Request, Header

    # Get the actual request object
    if hasattr(request, 'json'):
        payload = await request.json()
    else:
        payload = request

    # Get headers (this is a simplified version)
    event_type = "unknown"
    signature = None

    # In production, you'd get these from request headers:
    # event_type = request.headers.get("X-GitHub-Event", "unknown")
    # signature = request.headers.get("X-Hub-Signature-256")

    handler = GitHubWebhookHandler()
    return await handler.handle_event(event_type, payload)


@app.post("/api/v1/webhooks/github")
async def github_webhook_v1(
    payload: dict[str, Any],
    x_github_event: str | None = None,
    x_hub_signature_256: str | None = None,
) -> dict[str, Any]:
    """
    Handle GitHub webhook events (v1 API).

    This endpoint properly handles GitHub webhook headers.
    """
    settings = get_settings()

    # Verify signature if webhook secret is configured
    if settings.github_webhook_secret and x_hub_signature_256:
        import json
        payload_bytes = json.dumps(payload).encode()
        if not verify_github_signature(payload_bytes, x_hub_signature_256, settings.github_webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    handler = GitHubWebhookHandler()
    return await handler.handle_event(x_github_event or "unknown", payload)


@app.post("/api/v1/webhooks/test-analysis")
async def test_issue_analysis(
    repo: str,
    issue_title: str,
    issue_body: str = "",
) -> dict[str, Any]:
    """
    Test issue analysis without a real GitHub webhook.

    Useful for testing the analysis logic.
    """
    from clawforge.storage import get_project_store

    store = get_project_store()
    project = await store.find_by_repo(repo)

    if not project:
        raise HTTPException(status_code=404, detail=f"No ClawForge project found for repo '{repo}'")

    handler = GitHubWebhookHandler()
    analysis = await handler._analyze_issue(
        title=issue_title,
        body=issue_body,
        issue_url=f"https://github.com/{repo}/issues/test",
        project_files=project.files,
    )

    return {
        "issue_title": analysis.issue_title,
        "issue_type": "bug" if analysis.is_bug else "feature" if analysis.is_feature_request else "question",
        "affected_files": analysis.affected_files,
        "suggested_fix": analysis.suggested_fix,
        "confidence": analysis.confidence,
        "implementation_suggestion": analysis.implementation_suggestion,
        "cost_cents": analysis.cost_cents,
    }


# ============ Component Library Endpoints ============

@app.get("/api/v1/components")
async def list_components() -> dict[str, Any]:
    """
    List all available Flutter components.

    Returns component metadata including categories, dependencies, and tags.
    """
    library = get_component_library()
    return library.to_dict()


@app.get("/api/v1/components/categories")
async def list_component_categories() -> dict[str, Any]:
    """
    List all component categories.
    """
    return {
        "categories": [
            {"id": c.value, "name": c.value.title()}
            for c in ComponentCategory
        ]
    }


@app.get("/api/v1/components/category/{category}")
async def get_components_by_category(category: str) -> dict[str, Any]:
    """
    List components in a specific category.
    """
    library = get_component_library()

    try:
        cat = ComponentCategory(category.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Valid categories: {[c.value for c in ComponentCategory]}"
        )

    components = library.list_by_category(cat)

    return {
        "category": category,
        "count": len(components),
        "components": [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "tags": c.tags,
                "file_count": len(c.files),
                "requires": c.requires,
            }
            for c in components
        ],
    }


@app.get("/api/v1/components/search")
async def search_components(q: str) -> dict[str, Any]:
    """
    Search components by name, description, or tags.
    """
    library = get_component_library()
    components = library.search(q)

    return {
        "query": q,
        "count": len(components),
        "components": [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "category": c.category.value,
                "tags": c.tags,
                "file_count": len(c.files),
                "requires": c.requires,
            }
            for c in components
        ],
    }


@app.get("/api/v1/components/{component_id}")
async def get_component(component_id: str) -> dict[str, Any]:
    """
    Get detailed information about a specific component.

    Includes full source code, dependencies, and requirements.
    """
    library = get_component_library()
    component = library.get(component_id)

    if not component:
        raise HTTPException(status_code=404, detail="Component not found")

    return {
        "id": component.id,
        "name": component.name,
        "description": component.description,
        "category": component.category.value,
        "tags": component.tags,
        "requires": component.requires,
        "dependencies": component.dependencies,
        "dev_dependencies": component.dev_dependencies,
        "files": component.files,
        "preview_url": component.preview_url or None,
    }


@app.get("/api/v1/components/{component_id}/files")
async def get_component_files(component_id: str, include_deps: bool = True) -> dict[str, Any]:
    """
    Get all files for a component, optionally including dependencies.

    This is useful for directly copying component code into a project.
    """
    library = get_component_library()
    component = library.get(component_id)

    if not component:
        raise HTTPException(status_code=404, detail="Component not found")

    if include_deps:
        files = library.get_all_files([component_id])
        deps, dev_deps = library.get_all_dependencies([component_id])
    else:
        files = component.files
        deps = component.dependencies
        dev_deps = component.dev_dependencies

    return {
        "component_id": component_id,
        "file_count": len(files),
        "files": files,
        "dependencies": deps,
        "dev_dependencies": dev_deps,
    }


@app.post("/api/v1/components/bundle")
async def bundle_components(component_ids: list[str]) -> dict[str, Any]:
    """
    Bundle multiple components together.

    Resolves dependencies and deduplicates files.
    Useful for adding multiple components to a project at once.
    """
    library = get_component_library()

    # Validate all component IDs
    for cid in component_ids:
        if not library.get(cid):
            raise HTTPException(status_code=404, detail=f"Component not found: {cid}")

    files = library.get_all_files(component_ids)
    deps, dev_deps = library.get_all_dependencies(component_ids)

    return {
        "requested_components": component_ids,
        "file_count": len(files),
        "files": files,
        "dependencies": deps,
        "dev_dependencies": dev_deps,
    }


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "clawforge.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
    )
