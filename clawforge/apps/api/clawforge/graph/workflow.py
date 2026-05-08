"""LangGraph workflow for Flutter app generation.

New Architecture (2024-04-03):
- Basic Flow: App Idea → Target Users → Features → UI Design → Generate & Publish
- Advanced Options: Architecture, Backend, Environment, Code Settings, Quality
- All inputs routed through orchestrator to appropriate agents
- Docker validation loop: pub get → build_runner → analyze → fix → repeat
"""

from typing import Any, TypedDict, Literal
from langgraph.graph import StateGraph, END

from clawforge.agents import (
    RouterAgent,
    GitHubAgent,
    PlannerAgent,
    CoderAgent,
    ClawsAgent,
    RefinerAgent,
)
from clawforge.storage import get_project_store, ProjectContext
from clawforge.validator import (
    ValidationLoop,
    ValidationLoopResult,
    get_docker_validator,
)


class WorkflowState(TypedDict):
    """State that flows through the workflow graph."""

    # Workflow metadata
    workflow_id: str
    app_name: str

    # Basic flow inputs (required)
    app_idea: str
    target_users: str
    features: str
    ui_design: str

    # Advanced options (with defaults)
    architecture: dict[str, Any]
    backend_config: dict[str, Any]
    env_vars: dict[str, str]
    code_settings: dict[str, Any]
    quality_settings: dict[str, Any]

    # GitHub config (token, repo name, etc.)
    github_config: dict[str, Any]

    # Processed data
    full_spec: dict[str, Any]  # Consolidated by planner

    # Generated code
    generated_files: list[dict[str, str]]

    # GitHub
    github_repo_url: str | None
    github_pr_url: str | None

    # Evaluation
    quality_score: float
    issues: list[str]

    # Docker Validation (NEW)
    validation_passed: bool
    validation_iterations: int
    validation_errors: list[dict[str, Any]]
    validation_warnings: list[dict[str, Any]]
    generated_dart_files: list[dict[str, str]]  # .g.dart, .freezed.dart

    # Cost tracking
    total_cost_cents: int
    total_tokens: int

    # Progress
    current_stage: str
    completed_stages: list[str]

    # Error handling
    error: str | None


# Default values for advanced options
DEFAULT_ARCHITECTURE = {
    "state_management": "riverpod",
    "navigation": "go_router",
    "database": "drift",
}

DEFAULT_BACKEND = {
    "type": "offline-first",
    "services": [],
}

DEFAULT_CODE_SETTINGS = {
    "defensive_prompts": True,
    "test_coverage": "basic",
    "documentation": "inline",
}

DEFAULT_QUALITY_SETTINGS = {
    "accessibility": "standard",
    "performance": "balanced",
}


def create_initial_state(
    workflow_id: str,
    app_name: str,
    basic_inputs: dict[str, str],
    advanced_inputs: dict[str, Any] | None = None,
    github_config: dict[str, Any] | None = None,
) -> WorkflowState:
    """Create initial workflow state with defaults for advanced options."""
    advanced = advanced_inputs or {}

    return WorkflowState(
        workflow_id=workflow_id,
        app_name=app_name,
        # Basic inputs
        app_idea=basic_inputs.get("app_idea", ""),
        target_users=basic_inputs.get("target_users", ""),
        features=basic_inputs.get("features", ""),
        ui_design=basic_inputs.get("ui_design", ""),
        # Advanced with defaults
        architecture=advanced.get("architecture", DEFAULT_ARCHITECTURE),
        backend_config=advanced.get("backend", DEFAULT_BACKEND),
        env_vars=advanced.get("environment", {}),
        code_settings=advanced.get("code_settings", DEFAULT_CODE_SETTINGS),
        quality_settings=advanced.get("quality", DEFAULT_QUALITY_SETTINGS),
        # GitHub config
        github_config=github_config or {},
        # Initialize empty
        full_spec={},
        generated_files=[],
        github_repo_url=None,
        github_pr_url=None,
        quality_score=0.0,
        issues=[],
        # Validation state
        validation_passed=False,
        validation_iterations=0,
        validation_errors=[],
        validation_warnings=[],
        generated_dart_files=[],
        # Tracking
        total_cost_cents=0,
        total_tokens=0,
        current_stage="init",
        completed_stages=[],
        error=None,
    )


# Initialize agents
router_agent = RouterAgent()
github_agent = GitHubAgent()
planner_agent = PlannerAgent()
coder_agent = CoderAgent()
claws_agent = ClawsAgent()
refiner_agent = RefinerAgent()


async def finalize_spec(state: WorkflowState) -> WorkflowState:
    """Stage 1: Consolidate all inputs into a full specification."""
    state["current_stage"] = "finalizing_spec"
    print(f"🎯 Stage 1: Planning - Creating specification for {state['app_name']}...")

    result = await planner_agent.execute({
        "action": "finalize_spec",
        "basic": {
            "app_idea": state["app_idea"],
            "target_users": state["target_users"],
            "features": state["features"],
            "ui_design": state["ui_design"],
        },
        "advanced": {
            "architecture": state["architecture"],
            "backend": state["backend_config"],
            "code_settings": state["code_settings"],
            "quality": state["quality_settings"],
        },
        "app_name": state["app_name"],
    })

    if result.success:
        state["full_spec"] = result.output
        state["completed_stages"].append("spec")
        state["total_cost_cents"] += result.cost_cents
        state["total_tokens"] += result.tokens_used
        print(f"✅ Spec complete - Cost: ${result.cost_cents / 100:.2f}")
    else:
        state["error"] = result.error
        print(f"❌ Planning failed: {result.error}")

    return state


async def generate_code(state: WorkflowState) -> WorkflowState:
    """Stage 2: Generate Flutter code based on spec."""
    state["current_stage"] = "generating_code"
    print(f"💻 Stage 2: Coding - Generating Flutter code...")

    result = await coder_agent.execute({
        "app_name": state["app_name"],
        "spec": state["full_spec"],
        "settings": state["code_settings"],
        "env_vars": state["env_vars"],
    })

    if result.success:
        state["generated_files"] = result.output.get("files", [])
        state["completed_stages"].append("code")
        state["total_cost_cents"] += result.cost_cents
        state["total_tokens"] += result.tokens_used
        file_count = len(state["generated_files"])
        print(f"✅ Generated {file_count} files - Cost: ${result.cost_cents / 100:.2f}")
    else:
        state["error"] = result.error
        print(f"❌ Code generation failed: {result.error}")

    return state


async def evaluate_code(state: WorkflowState) -> WorkflowState:
    """Stage 3: Evaluate and fix code quality."""
    state["current_stage"] = "evaluating_code"

    if not state["generated_files"]:
        state["error"] = "No code to evaluate"
        return state

    print(f"🔍 Evaluating {len(state['generated_files'])} files...")

    # New ClawsAgent takes files list, not combined code
    result = await claws_agent.execute({
        "action": "evaluate",
        "files": state["generated_files"],
        "spec": state["full_spec"],
        "quality_settings": state["quality_settings"],
    })

    if result.success:
        evaluation = result.output
        state["quality_score"] = evaluation.get("score", 0)
        state["issues"] = evaluation.get("issues", [])
        state["completed_stages"].append("evaluate")
        state["total_cost_cents"] += result.cost_cents
        state["total_tokens"] += result.tokens_used

        print(f"✅ Quality Score: {state['quality_score']}/10")

        # Auto-fix if there are fixable issues and defensive mode is enabled
        fixable_issues = evaluation.get("fixable_issues", [])
        if fixable_issues and state["code_settings"].get("defensive_prompts", True):
            print(f"🔧 Auto-fixing {len(fixable_issues)} issues...")
            fix_result = await claws_agent.execute({
                "action": "fix",
                "files": state["generated_files"],
                "issues": fixable_issues,
            })
            if fix_result.success:
                state["generated_files"] = fix_result.output.get(
                    "files", state["generated_files"]
                )
                state["total_cost_cents"] += fix_result.cost_cents
                state["total_tokens"] += fix_result.tokens_used
                print(f"✅ Fixed {fix_result.output.get('fixes_applied', 0)} files")
    else:
        # Evaluation failure is not fatal, continue with warning
        state["issues"].append(f"Evaluation warning: {result.error}")
        state["completed_stages"].append("evaluate")
        print(f"⚠️ Evaluation had issues: {result.error}")

    return state


async def validate_code(state: WorkflowState) -> WorkflowState:
    """Stage 3.5: Docker-based validation loop.

    Runs:
    1. flutter pub get - Check dependencies
    2. dart run build_runner build - Generate .g.dart/.freezed.dart
    3. dart analyze - Static analysis

    If errors found, uses RefinerAgent to fix and loops (max 3x).
    """
    state["current_stage"] = "validating_code"

    if not state["generated_files"]:
        state["error"] = "No code to validate"
        return state

    print(f"🐳 Stage 3.5: Docker Validation - Validating {len(state['generated_files'])} files...")

    # Create fix function using RefinerAgent
    async def fix_with_refiner(
        errors: list,
        files: list[dict[str, str]],
        context: dict[str, Any],
    ) -> list[dict[str, str]]:
        """Fix errors using the Refiner Agent."""
        result = await refiner_agent.execute({
            "files": files,
            "spec": state["full_spec"],
            "validation_errors": errors,
            "auto_fix_mode": True,
        })

        if result.success and result.output:
            state["total_cost_cents"] += result.cost_cents
            state["total_tokens"] += result.tokens_used
            return result.output.get("merged_files", files)

        return files

    # Run validation loop
    try:
        validation_loop = ValidationLoop(
            max_iterations=3,
            fix_function=fix_with_refiner,
        )

        result = await validation_loop.run(
            files=state["generated_files"],
            project_id=state["workflow_id"],
            context={
                "spec": state["full_spec"],
                "app_name": state["app_name"],
            },
        )

        # Update state with validation results
        state["validation_passed"] = result.success
        state["validation_iterations"] = result.iterations_used
        state["generated_files"] = result.final_files  # Updated/fixed files
        state["generated_dart_files"] = result.generated_files  # .g.dart files

        if result.final_validation:
            state["validation_errors"] = [
                e.to_dict() for e in result.final_validation.all_errors
            ]
            state["validation_warnings"] = [
                w.to_dict() for w in result.final_validation.all_warnings
            ]

        state["completed_stages"].append("validate")

        if result.success:
            print(f"✅ Validation passed after {result.iterations_used} iteration(s)")
            print(f"   Generated {len(result.generated_files)} .g.dart/.freezed.dart files")
        else:
            # Validation failed but we continue (partial push OK per user request)
            error_count = len(state["validation_errors"])
            warning_count = len(state["validation_warnings"])
            print(f"⚠️ Validation completed with {error_count} errors, {warning_count} warnings")
            print(f"   Continuing with partial code (tracking errors for iterative fixes)")
            state["issues"].append(
                f"Validation: {error_count} errors remaining after {result.iterations_used} fix attempts"
            )

    except Exception as e:
        # Docker validation failure is not fatal - continue without it
        print(f"⚠️ Docker validation skipped: {e}")
        state["issues"].append(f"Validation skipped: {str(e)}")
        state["completed_stages"].append("validate")

    return state


async def publish_to_github(state: WorkflowState) -> WorkflowState:
    """Stage 4: Publish to GitHub."""
    state["current_stage"] = "publishing"

    github_config = state.get("github_config", {})
    github_token = github_config.get("token")
    repo_name = github_config.get("repo_name")
    create_new = github_config.get("create_new", True)

    if not github_token:
        state["error"] = "GitHub token is required"
        return state

    if not state["generated_files"]:
        state["error"] = "No files to publish"
        return state

    # Use provided repo name or generate from app name
    app_slug = repo_name or state["app_name"].lower().replace(" ", "-").replace("_", "-")
    # Remove any characters that aren't valid in repo names
    app_slug = "".join(c for c in app_slug if c.isalnum() or c == "-")

    import asyncio
    import sys

    print(f"🚀 Publishing to GitHub: {app_slug}")
    sys.stdout.flush()

    # Create repository (if creating new)
    if create_new:
        print(f"📁 Creating repository: {app_slug}")
        sys.stdout.flush()

        try:
            create_result = await github_agent.execute({
                "action": "create_repo",
                "name": app_slug,
                "description": state["full_spec"].get(
                    "description",
                    f"{state['app_name']} - Generated by ClawForge"
                )[:200],
                "private": False,  # Public by default for easy access
                "token": github_token,
            })
        except Exception as e:
            print(f"❌ Exception during repo creation: {e}")
            sys.stdout.flush()
            state["error"] = f"Exception creating repo: {str(e)}"
            return state

        if not create_result.success:
            print(f"❌ Failed to create repo: {create_result.error}")
            sys.stdout.flush()
            state["error"] = f"Failed to create repo: {create_result.error}"
            return state

        state["github_repo_url"] = create_result.output["repo_url"]
        full_repo_name = create_result.output.get("full_name")

        if not full_repo_name:
            # Fallback: get username from token and construct full name
            print("⚠️ full_name not in response, getting username...")
            sys.stdout.flush()
            try:
                user_result = await github_agent.execute({
                    "action": "get_user",
                    "token": github_token,
                })
                if user_result.success:
                    full_repo_name = f"{user_result.output['login']}/{app_slug}"
                else:
                    full_repo_name = app_slug
            except Exception as e:
                print(f"⚠️ Failed to get user: {e}")
                full_repo_name = app_slug

        print(f"✅ Repository created: {full_repo_name}")
        sys.stdout.flush()

        # Wait for GitHub to propagate the new repo (5 seconds recommended)
        print("⏳ Waiting for GitHub to propagate (5s)...")
        sys.stdout.flush()
        await asyncio.sleep(5)
    else:
        # Use existing repo
        full_repo_name = repo_name
        state["github_repo_url"] = f"https://github.com/{repo_name}"

    # Create feature branch with retry logic for propagation delays
    print(f"🌿 Creating feature branch on {full_repo_name}...")
    sys.stdout.flush()
    branch_name = "feature/clawforge-generated"
    branch_result = None
    max_retries = 3

    for attempt in range(max_retries):
        try:
            branch_result = await github_agent.execute({
                "action": "create_branch",
                "repo_name": full_repo_name,
                "branch_name": branch_name,
                "base_branch": "main",
                "token": github_token,
            })
        except Exception as e:
            print(f"❌ Exception during branch creation (attempt {attempt + 1}): {e}")
            sys.stdout.flush()
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
                continue
            break

        if branch_result.success:
            print(f"✅ Branch '{branch_name}' created successfully")
            sys.stdout.flush()
            break

        # Check if it's a 404 error (propagation issue) - retry
        error_str = str(branch_result.error).lower()
        if "404" in error_str or "not found" in error_str:
            if attempt < max_retries - 1:
                wait_time = 2 ** (attempt + 1)  # 2, 4 seconds
                print(f"⏳ Repository not yet available, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                sys.stdout.flush()
                await asyncio.sleep(wait_time)
                continue

        # Check if branch already exists - that's okay
        if "already exists" in error_str:
            print(f"ℹ️ Branch '{branch_name}' already exists, using it")
            sys.stdout.flush()
            break

        # For other errors, break immediately
        print(f"⚠️ Branch creation error: {branch_result.error}")
        sys.stdout.flush()
        break

    # If all retries failed, fall back to main branch
    if branch_result and not branch_result.success and "already exists" not in str(branch_result.error).lower():
        print(f"⚠️ Branch creation failed after {max_retries} attempts: {branch_result.error}")
        print("📝 Falling back to pushing directly to main branch...")
        sys.stdout.flush()
        branch_name = "main"

    # Push generated files with retry logic
    print(f"📤 Pushing {len(state['generated_files'])} files to {branch_name}...")
    sys.stdout.flush()
    push_result = None

    for attempt in range(max_retries):
        try:
            push_result = await github_agent.execute({
                "action": "push_files",
                "repo_name": full_repo_name,
                "branch": branch_name,
                "files": state["generated_files"],
                "message": f"feat: Initial {state['app_name']} implementation\n\nGenerated by ClawForge AI",
                "token": github_token,
            })
        except Exception as e:
            print(f"❌ Exception during file push (attempt {attempt + 1}): {e}")
            sys.stdout.flush()
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
                continue
            break

        if push_result.success:
            print(f"✅ Successfully pushed {len(state['generated_files'])} files")
            sys.stdout.flush()
            break

        # Check if it's a propagation issue - retry
        error_str = str(push_result.error).lower()
        if "404" in error_str or "not found" in error_str:
            if attempt < max_retries - 1:
                wait_time = 2 ** (attempt + 1)
                print(f"⏳ Repository not yet ready, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                sys.stdout.flush()
                await asyncio.sleep(wait_time)
                continue

        # For other errors, break immediately
        print(f"⚠️ Push error: {push_result.error}")
        sys.stdout.flush()
        break

    if not push_result or not push_result.success:
        error_msg = push_result.error if push_result else 'Unknown error'
        print(f"❌ Failed to push files: {error_msg}")
        sys.stdout.flush()
        state["error"] = f"Failed to push files: {error_msg}"
        return state

    # Create pull request
    print(f"📝 Creating pull request...")
    pr_body = f"""## 🎉 {state['app_name']}

AI-generated Flutter app based on your specifications.

### 📋 App Concept
{state['app_idea'][:500]}

### 👥 Target Users
{state['target_users'][:300]}

### ✨ Features
{state['features'][:500]}

### 🎨 UI Style
{state['ui_design']}

### 📊 Quality Score
**{state['quality_score']}/10**

### 🏗️ Architecture
- State Management: `{state['architecture'].get('state_management', 'riverpod')}`
- Navigation: `{state['architecture'].get('navigation', 'go_router')}`
- Database: `{state['architecture'].get('database', 'drift')}`

### 📁 Files Generated
{len(state['generated_files'])} files

### 🐳 Validation Status
{'✅ Passed' if state.get('validation_passed') else '⚠️ Partial (some errors remaining)'}
- Iterations: {state.get('validation_iterations', 0)}/3
- Errors: {len(state.get('validation_errors', []))}
- Warnings: {len(state.get('validation_warnings', []))}

### 💰 Generation Cost
${state['total_cost_cents'] / 100:.2f}

---

### 🚀 Next Steps
1. Clone this repository
2. Run `flutter pub get`
3. Run `dart run build_runner build --delete-conflicting-outputs`
4. Run `flutter run`

{'### ⚠️ Known Issues' if state.get('validation_errors') else ''}
{chr(10).join(f"- {e.get('file_path', 'unknown')}: {e.get('message', '')}" for e in state.get('validation_errors', [])[:5]) if state.get('validation_errors') else ''}
{f'...and {len(state.get("validation_errors", [])) - 5} more' if len(state.get('validation_errors', [])) > 5 else ''}

---
*Generated by [ClawForge](https://github.com/clawforge) - AI Flutter App Builder*
"""

    # Only create PR if we pushed to a feature branch (not main)
    if branch_name != "main":
        pr_result = await github_agent.execute({
            "action": "create_pr",
            "repo_name": full_repo_name,
            "title": f"feat: {state['app_name']} - AI Generated Flutter App",
            "body": pr_body,
            "head": branch_name,
            "base": "main",
            "token": github_token,
        })

        if pr_result.success:
            state["github_pr_url"] = pr_result.output["pr_url"]
            print(f"✅ Published! PR: {state['github_pr_url']}")
        else:
            # PR creation failed but files are pushed - not a critical error
            print(f"⚠️ PR creation failed: {pr_result.error}")
            print("📝 Files were pushed successfully, but PR could not be created")
    else:
        # Pushed directly to main - no PR needed
        print(f"✅ Published! Files pushed directly to main branch")
        print(f"📁 Repository: {state['github_repo_url']}")

    state["completed_stages"].append("publish")

    return state


def should_continue(state: WorkflowState) -> Literal["continue", "end"]:
    """Check if workflow should continue or stop."""
    if state.get("error"):
        return "end"
    return "continue"


def create_workflow_graph() -> StateGraph:
    """Create the LangGraph workflow for the new architecture.

    Flow: finalize_spec → generate_code → evaluate_code → validate_code → publish_github
    """
    workflow = StateGraph(WorkflowState)

    # Add nodes (stages)
    workflow.add_node("finalize_spec", finalize_spec)
    workflow.add_node("generate_code", generate_code)
    workflow.add_node("evaluate_code", evaluate_code)
    workflow.add_node("validate_code", validate_code)  # NEW: Docker validation
    workflow.add_node("publish_github", publish_to_github)

    # Set entry point
    workflow.set_entry_point("finalize_spec")

    # Linear flow with error checking
    workflow.add_conditional_edges(
        "finalize_spec",
        should_continue,
        {"continue": "generate_code", "end": END},
    )
    workflow.add_conditional_edges(
        "generate_code",
        should_continue,
        {"continue": "evaluate_code", "end": END},
    )
    workflow.add_conditional_edges(
        "evaluate_code",
        should_continue,
        {"continue": "validate_code", "end": END},  # Now goes to validation
    )
    workflow.add_conditional_edges(
        "validate_code",
        should_continue,
        {"continue": "publish_github", "end": END},  # Then to GitHub
    )
    workflow.add_edge("publish_github", END)

    return workflow.compile()


# Node to agent routing (for individual node updates)
NODE_TO_AGENT = {
    "app-idea": "planner",
    "target-users": "planner",
    "features": "planner",
    "ui-design": "planner",
    "architecture": "planner",
    "backend": "planner",
    "environment": None,  # Direct storage
    "code-settings": "coder",
    "quality": "claws",
}


async def route_node_input(node_id: str, input_data: Any) -> dict[str, Any]:
    """Route a single node's input to the appropriate agent for validation."""
    agent_name = NODE_TO_AGENT.get(node_id)

    if agent_name is None:
        # Direct storage (e.g., environment variables)
        return {"success": True, "output": input_data}

    agent_map = {
        "planner": planner_agent,
        "coder": coder_agent,
        "claws": claws_agent,
    }

    agent = agent_map.get(agent_name)
    if not agent:
        return {"success": False, "error": f"Unknown agent: {agent_name}"}

    result = await agent.execute({
        "action": "validate_input",
        "node": node_id,
        "input": input_data,
    })

    return {
        "success": result.success,
        "output": result.output if result.success else None,
        "error": result.error if not result.success else None,
        "cost_cents": result.cost_cents,
        "tokens": result.tokens_used,
    }


async def run_clawforge_workflow(
    basic_inputs: dict[str, Any],
    advanced_options: dict[str, Any],
    github_config: dict[str, str],
    user_id: str | None = None,
) -> dict[str, Any]:
    """
    Main entry point to run the full ClawForge workflow.

    Args:
        basic_inputs: Required user inputs (app_idea, target_users, features, ui_design)
        advanced_options: Optional advanced configuration
        github_config: GitHub token and repo settings
        user_id: ID of the user creating this project

    Returns:
        Dictionary with workflow results including repo URL, PR URL, etc.
    """
    import uuid

    workflow_id = f"wf_{uuid.uuid4().hex[:16]}"

    # Extract app name from the idea
    app_name = basic_inputs.get("app_idea", "My Flutter App")[:50].split(".")[0].strip()

    # Create initial state with GitHub config
    state = create_initial_state(
        workflow_id=workflow_id,
        app_name=app_name,
        basic_inputs=basic_inputs,
        advanced_inputs=advanced_options,
        github_config=github_config,
    )

    try:
        # Create and run the workflow graph
        workflow = create_workflow_graph()
        final_state = await workflow.ainvoke(state)

        # Save project context for iterative development
        project_id = None
        if final_state.get("error") is None and final_state.get("generated_files"):
            store = get_project_store()
            project = ProjectContext(
                project_id=store.generate_project_id(
                    app_name,
                    final_state.get("github_repo_url", "")
                ),
                user_id=user_id or "",
                github_repo=final_state.get("github_repo_url", ""),
                app_name=app_name,
                app_idea=basic_inputs.get("app_idea", ""),
                target_users=basic_inputs.get("target_users", ""),
                features=basic_inputs.get("features", ""),
                ui_design=basic_inputs.get("ui_design", ""),
                full_spec=final_state.get("full_spec", {}),
                files=final_state.get("generated_files", []),
                total_cost_cents=final_state.get("total_cost_cents", 0),
            )
            await store.save(project)
            project_id = project.project_id
            print(f"📦 Project saved: {project_id}")

        return {
            "success": final_state.get("error") is None,
            "message": "App generated successfully!" if not final_state.get("error") else final_state["error"],
            "github_repo_url": final_state.get("github_repo_url"),
            "pr_url": final_state.get("github_pr_url"),
            "steps_completed": final_state.get("completed_stages", []),
            "quality_score": final_state.get("quality_score", 0),
            "cost_cents": final_state.get("total_cost_cents", 0),
            "error": final_state.get("error"),
            "project_id": project_id,  # For iterative development
            # Validation info
            "validation": {
                "passed": final_state.get("validation_passed", False),
                "iterations": final_state.get("validation_iterations", 0),
                "errors": final_state.get("validation_errors", []),
                "warnings": final_state.get("validation_warnings", []),
                "generated_files": len(final_state.get("generated_dart_files", [])),
            },
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Workflow failed: {str(e)}",
            "error": str(e),
            "steps_completed": state.get("completed_stages", []),
            "cost_cents": state.get("total_cost_cents", 0),
        }
