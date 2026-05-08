"""Orchestrator agent - Central manager for the entire workflow.

The Orchestrator:
1. Receives user inputs from the frontend
2. Routes tasks to appropriate agents
3. Manages workflow state and transitions
4. Handles errors and retries
5. Tracks costs across all agents
"""

from typing import Any
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from clawforge.agents.base import AgentResult, BaseAgent
from clawforge.agents.planner import PlannerAgent
from clawforge.agents.coder import CoderAgent
from clawforge.agents.claws import ClawsAgent
from clawforge.agents.github import GitHubAgent
from clawforge.config import get_settings
from clawforge.validation import validate_flutter_code, quick_syntax_check
from clawforge.storage import get_project_store, ProjectContext
from clawforge.autofixer import fix_with_llm


class WorkflowStage(str, Enum):
    """Workflow execution stages."""
    PLANNING = "planning"
    CODING = "coding"
    VALIDATING = "validating"
    REVIEWING = "reviewing"
    PUBLISHING = "publishing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowContext:
    """Shared context across all agents in a workflow."""

    # Input data
    app_idea: str = ""
    target_users: str = ""
    features: str = ""
    ui_design: str = ""

    # Advanced options
    architecture: dict = field(default_factory=dict)
    backend_config: dict = field(default_factory=dict)
    code_settings: dict = field(default_factory=dict)
    quality_settings: dict = field(default_factory=dict)
    env_vars: dict = field(default_factory=dict)

    # GitHub config
    github_token: str = ""
    repo_name: str = ""
    create_new_repo: bool = True

    # Generated data
    app_name: str = ""
    full_spec: dict = field(default_factory=dict)
    generated_files: list = field(default_factory=list)

    # GitHub results
    github_repo_url: str = ""
    github_pr_url: str = ""

    # Validation
    validation_passed: bool = False
    validation_issues: list = field(default_factory=list)

    # Quality
    quality_score: float = 0.0
    issues: list = field(default_factory=list)

    # Tracking
    current_stage: WorkflowStage = WorkflowStage.PLANNING
    completed_stages: list = field(default_factory=list)
    total_cost_cents: int = 0
    total_tokens: int = 0
    errors: list = field(default_factory=list)


class OrchestratorAgent(BaseAgent):
    """Central orchestrator that manages the entire app generation workflow.

    Workflow:
    1. PLANNING - PlannerAgent consolidates inputs into a full specification
    2. CODING - CoderAgent generates Flutter code using RAG
    3. REVIEWING - ClawsAgent evaluates and fixes code quality
    4. PUBLISHING - GitHubAgent pushes to GitHub and creates PR
    """

    name = "orchestrator"
    description = "Manages the complete workflow from idea to GitHub PR"

    def __init__(self):
        self.planner = PlannerAgent()
        self.coder = CoderAgent()
        self.claws = ClawsAgent()
        self.github = GitHubAgent()
        self.settings = get_settings()

    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """Execute the complete workflow."""

        # Initialize context from input
        ctx = self._create_context(input_data)

        try:
            # Stage 1: Planning
            ctx = await self._run_planning(ctx)
            if ctx.current_stage == WorkflowStage.FAILED:
                return self._create_failed_result(ctx)

            # Stage 2: Code Generation
            ctx = await self._run_coding(ctx)
            if ctx.current_stage == WorkflowStage.FAILED:
                return self._create_failed_result(ctx)

            # Stage 2.5: Code Validation (syntax check + flutter analyze)
            ctx = await self._run_validation(ctx)
            # Validation failure is a warning, not fatal (continue to GitHub)

            # Stage 3: Code Review
            ctx = await self._run_reviewing(ctx)
            if ctx.current_stage == WorkflowStage.FAILED:
                return self._create_failed_result(ctx)

            # Stage 4: GitHub Publishing
            ctx = await self._run_publishing(ctx)
            if ctx.current_stage == WorkflowStage.FAILED:
                return self._create_failed_result(ctx)

            # Success!
            ctx.current_stage = WorkflowStage.COMPLETED

            # Save project context for iterative development
            project_id = await self._save_project_context(ctx)

            return self._create_success_result(ctx, project_id)

        except Exception as e:
            ctx.errors.append(f"Orchestrator error: {str(e)}")
            ctx.current_stage = WorkflowStage.FAILED
            return self._create_failed_result(ctx)

    def _create_context(self, input_data: dict[str, Any]) -> WorkflowContext:
        """Create workflow context from input data."""
        basic = input_data.get("basic_inputs", {})
        advanced = input_data.get("advanced_options", {})
        github = input_data.get("github_config", {})

        # Extract app name from idea
        app_idea = basic.get("app_idea", "My App")
        app_name = self._extract_app_name(app_idea)

        return WorkflowContext(
            # Basic inputs
            app_idea=app_idea,
            target_users=basic.get("target_users", ""),
            features=basic.get("features", ""),
            ui_design=basic.get("ui_design", "Modern"),

            # Advanced options
            architecture=advanced.get("architecture", {
                "state": "riverpod",
                "nav": "go_router",
                "db": "drift"
            }),
            backend_config=advanced.get("backend", {"type": "offline-first"}),
            code_settings=advanced.get("code_settings", {
                "defensive": True,
                "tests": "basic",
                "docs": "inline"
            }),
            quality_settings=advanced.get("quality", {
                "a11y": "standard",
                "performance": "balanced"
            }),
            env_vars=advanced.get("environment", {}),

            # GitHub
            github_token=github.get("token", ""),
            repo_name=github.get("repo_name", app_name.lower().replace(" ", "-")),
            create_new_repo=github.get("create_new", True),

            # Generated
            app_name=app_name,
        )

    def _extract_app_name(self, app_idea: str) -> str:
        """Extract a reasonable app name from the idea."""
        # Take first sentence, limit to 30 chars
        name = app_idea.split(".")[0].strip()[:30]
        # Clean up
        name = "".join(c for c in name if c.isalnum() or c.isspace())
        return name.strip() or "My Flutter App"

    async def _run_planning(self, ctx: WorkflowContext) -> WorkflowContext:
        """Run the planning stage."""
        ctx.current_stage = WorkflowStage.PLANNING
        print(f"🎯 Stage 1: Planning - Consolidating specifications...")

        result = await self.planner.execute({
            "action": "finalize_spec",
            "basic": {
                "app_idea": ctx.app_idea,
                "target_users": ctx.target_users,
                "features": ctx.features,
                "ui_design": ctx.ui_design,
            },
            "advanced": {
                "architecture": ctx.architecture,
                "backend": ctx.backend_config,
                "code_settings": ctx.code_settings,
                "quality": ctx.quality_settings,
            },
            "app_name": ctx.app_name,
        })

        ctx.total_cost_cents += result.cost_cents
        ctx.total_tokens += result.tokens_used

        if result.success:
            ctx.full_spec = result.output
            ctx.completed_stages.append("planning")
            print(f"✅ Planning complete - Cost: ${result.cost_cents/100:.2f}")
        else:
            ctx.errors.append(f"Planning failed: {result.error}")
            ctx.current_stage = WorkflowStage.FAILED
            print(f"❌ Planning failed: {result.error}")

        return ctx

    async def _run_coding(self, ctx: WorkflowContext) -> WorkflowContext:
        """Run the code generation stage."""
        ctx.current_stage = WorkflowStage.CODING
        print(f"💻 Stage 2: Coding - Generating Flutter code...")

        result = await self.coder.execute({
            "app_name": ctx.app_name,
            "spec": ctx.full_spec,
            "settings": ctx.code_settings,
            "env_vars": ctx.env_vars,
        })

        ctx.total_cost_cents += result.cost_cents
        ctx.total_tokens += result.tokens_used

        if result.success:
            ctx.generated_files = result.output.get("files", [])
            ctx.completed_stages.append("coding")
            print(f"✅ Code generation complete - {len(ctx.generated_files)} files - Cost: ${result.cost_cents/100:.2f}")
        else:
            ctx.errors.append(f"Code generation failed: {result.error}")
            ctx.current_stage = WorkflowStage.FAILED
            print(f"❌ Code generation failed: {result.error}")

        return ctx

    async def _run_validation(self, ctx: WorkflowContext) -> WorkflowContext:
        """Run code validation using flutter analyze."""
        ctx.current_stage = WorkflowStage.VALIDATING
        print(f"🔬 Stage 2.5: Validating - Running flutter analyze...")

        if not ctx.generated_files:
            print("⚠️ No files to validate")
            return ctx

        try:
            # First do a quick syntax check (fast, no flutter required)
            print("  Quick syntax check...")
            quick_result = await quick_syntax_check(ctx.generated_files)

            if quick_result.error_count > 0:
                print(f"  ⚠️ Found {quick_result.error_count} syntax issues")
                ctx.validation_issues.extend([
                    {
                        "severity": issue.severity,
                        "file": issue.file,
                        "line": issue.line,
                        "message": issue.message,
                        "code": issue.code,
                    }
                    for issue in quick_result.issues
                ])

            # Then run full flutter analyze (requires Flutter SDK)
            print("  Running flutter analyze (this may take a moment)...")
            validation_result = await validate_flutter_code(
                ctx.generated_files,
                timeout_seconds=120,
            )

            ctx.validation_passed = validation_result.success
            ctx.validation_issues.extend([
                {
                    "severity": issue.severity,
                    "file": issue.file,
                    "line": issue.line,
                    "message": issue.message,
                    "code": issue.code,
                }
                for issue in validation_result.issues
            ])

            if validation_result.success:
                print(f"✅ Validation passed! ({validation_result.warning_count} warnings)")
                ctx.completed_stages.append("validating")
            else:
                print(f"⚠️ Validation found {validation_result.error_count} errors, {validation_result.warning_count} warnings")

                # Try model-driven autofix for errors (v0-inspired)
                if validation_result.error_count > 0 and ctx.code_settings.get("defensive", True):
                    print(f"  🤖 Attempting model-driven autofix for {validation_result.error_count} errors...")

                    # Format errors for the model fixer
                    errors_for_fix = [
                        {
                            "file": issue.file,
                            "line": issue.line,
                            "message": issue.message,
                        }
                        for issue in validation_result.issues
                        if issue.severity == "error"
                    ]

                    fix_result = await fix_with_llm(
                        files=ctx.generated_files,
                        errors=errors_for_fix,
                        use_local_llm=True,  # Use local LLM for speed
                    )

                    if fix_result.success and fix_result.fixes_applied:
                        ctx.generated_files = fix_result.fixed_files
                        ctx.total_cost_cents += fix_result.cost_cents
                        ctx.total_tokens += fix_result.tokens_used
                        print(f"    ✅ Applied {len(fix_result.fixes_applied)} model-driven fixes")

                        # Re-run validation to check if fixes worked
                        print("  🔬 Re-validating after fixes...")
                        revalidation = await validate_flutter_code(
                            ctx.generated_files,
                            timeout_seconds=120,
                        )
                        ctx.validation_passed = revalidation.success
                        if revalidation.success:
                            print(f"    ✅ Re-validation passed!")
                        else:
                            print(f"    ⚠️ Still has {revalidation.error_count} errors after fixes")
                    else:
                        if fix_result.errors:
                            print(f"    ⚠️ Model fixer had issues: {fix_result.errors[:2]}")

                # Don't fail the workflow - continue to publishing
                ctx.completed_stages.append("validating")
                ctx.issues.append(f"Code validation found {validation_result.error_count} errors")

        except Exception as e:
            # Validation failure should not stop the workflow
            print(f"⚠️ Validation skipped: {str(e)}")
            ctx.validation_issues.append({
                "severity": "warning",
                "file": "",
                "line": 0,
                "message": f"Validation could not run: {str(e)}",
                "code": "validation_skipped",
            })
            ctx.completed_stages.append("validating")

        return ctx

    async def _run_reviewing(self, ctx: WorkflowContext) -> WorkflowContext:
        """Run the code review stage."""
        ctx.current_stage = WorkflowStage.REVIEWING
        print(f"🔍 Stage 3: Reviewing - Evaluating code quality...")

        if not ctx.generated_files:
            ctx.errors.append("No code to review")
            ctx.current_stage = WorkflowStage.FAILED
            return ctx

        result = await self.claws.execute({
            "action": "evaluate",
            "files": ctx.generated_files,
            "spec": ctx.full_spec,
            "quality_settings": ctx.quality_settings,
        })

        ctx.total_cost_cents += result.cost_cents
        ctx.total_tokens += result.tokens_used

        if result.success:
            evaluation = result.output
            ctx.quality_score = evaluation.get("score", 0)
            ctx.issues = evaluation.get("issues", [])

            # Auto-fix if there are fixable issues
            if evaluation.get("fixable_issues") and ctx.code_settings.get("defensive", True):
                print(f"🔧 Auto-fixing {len(evaluation['fixable_issues'])} issues...")
                fix_result = await self.claws.execute({
                    "action": "fix",
                    "files": ctx.generated_files,
                    "issues": evaluation["fixable_issues"],
                })
                if fix_result.success:
                    ctx.generated_files = fix_result.output.get("files", ctx.generated_files)
                    ctx.total_cost_cents += fix_result.cost_cents
                    ctx.total_tokens += fix_result.tokens_used

            ctx.completed_stages.append("reviewing")
            print(f"✅ Review complete - Score: {ctx.quality_score}/10 - Cost: ${result.cost_cents/100:.2f}")
        else:
            # Review failure is not fatal, continue with warning
            ctx.issues.append(f"Review warning: {result.error}")
            ctx.completed_stages.append("reviewing")
            print(f"⚠️ Review had issues: {result.error}")

        return ctx

    async def _run_publishing(self, ctx: WorkflowContext) -> WorkflowContext:
        """Run the GitHub publishing stage."""
        ctx.current_stage = WorkflowStage.PUBLISHING
        print(f"🚀 Stage 4: Publishing - Pushing to GitHub...")

        if not ctx.github_token:
            ctx.errors.append("GitHub token is required")
            ctx.current_stage = WorkflowStage.FAILED
            return ctx

        # Create repository
        if ctx.create_new_repo:
            print(f"📁 Creating repository: {ctx.repo_name}")
            create_result = await self.github.execute({
                "action": "create_repo",
                "name": ctx.repo_name,
                "description": f"{ctx.app_name} - Generated by ClawForge",
                "private": False,
                "token": ctx.github_token,
            })

            if not create_result.success:
                ctx.errors.append(f"Failed to create repo: {create_result.error}")
                ctx.current_stage = WorkflowStage.FAILED
                return ctx

            ctx.github_repo_url = create_result.output.get("repo_url", "")
            repo_full_name = create_result.output.get("full_name", "")
        else:
            repo_full_name = ctx.repo_name
            ctx.github_repo_url = f"https://github.com/{repo_full_name}"

        # Create feature branch
        print(f"🌿 Creating feature branch...")
        branch_result = await self.github.execute({
            "action": "create_branch",
            "repo_name": repo_full_name,
            "branch_name": "feature/clawforge-generated",
            "base_branch": "main",
            "token": ctx.github_token,
        })

        if not branch_result.success:
            # Branch might already exist, continue
            print(f"⚠️ Branch creation: {branch_result.error}")

        # Push generated files
        print(f"📤 Pushing {len(ctx.generated_files)} files...")
        push_result = await self.github.execute({
            "action": "push_files",
            "repo_name": repo_full_name,
            "files": ctx.generated_files,
            "branch": "feature/clawforge-generated",
            "message": f"feat: Initial {ctx.app_name} implementation\n\nGenerated by ClawForge AI",
            "token": ctx.github_token,
        })

        if not push_result.success:
            ctx.errors.append(f"Failed to push files: {push_result.error}")
            ctx.current_stage = WorkflowStage.FAILED
            return ctx

        # Create pull request
        print(f"📝 Creating pull request...")
        pr_result = await self.github.execute({
            "action": "create_pr",
            "repo_name": repo_full_name,
            "title": f"feat: {ctx.app_name} - AI Generated Flutter App",
            "body": self._create_pr_body(ctx),
            "head": "feature/clawforge-generated",
            "base": "main",
            "token": ctx.github_token,
        })

        if pr_result.success:
            ctx.github_pr_url = pr_result.output.get("pr_url", "")
            ctx.completed_stages.append("publishing")
            print(f"✅ Published! PR: {ctx.github_pr_url}")
        else:
            ctx.errors.append(f"Failed to create PR: {pr_result.error}")
            ctx.current_stage = WorkflowStage.FAILED

        return ctx

    def _create_pr_body(self, ctx: WorkflowContext) -> str:
        """Create a detailed PR description."""
        return f"""## 🎉 {ctx.app_name}

AI-generated Flutter app based on your specifications.

### 📋 App Concept
{ctx.app_idea[:500]}

### 👥 Target Users
{ctx.target_users[:300]}

### ✨ Features
{ctx.features[:500]}

### 🎨 Design Style
{ctx.ui_design}

### 🔬 Validation Status
{"✅ Passed" if ctx.validation_passed else f"⚠️ {len([i for i in ctx.validation_issues if i.get('severity') == 'error'])} errors found"}

### 📊 Quality Score
**{ctx.quality_score}/10**

### 🏗️ Architecture
- State Management: `{ctx.architecture.get('state', 'riverpod')}`
- Navigation: `{ctx.architecture.get('nav', 'go_router')}`
- Database: `{ctx.architecture.get('db', 'drift')}`

### 📁 Files Generated
{len(ctx.generated_files)} files

### 💰 Generation Cost
${ctx.total_cost_cents/100:.2f}

---

### 🚀 Next Steps
1. Clone this repository
2. Run `flutter pub get`
3. Run `flutter run`

---
*Generated by [ClawForge](https://github.com/clawforge) - AI Flutter App Builder*
"""

    async def _save_project_context(self, ctx: WorkflowContext) -> str:
        """Save project context for iterative development."""
        store = get_project_store()

        project = ProjectContext(
            project_id=store.generate_project_id(ctx.app_name, ctx.github_repo_url),
            github_repo=ctx.github_repo_url,
            app_name=ctx.app_name,
            app_idea=ctx.app_idea,
            target_users=ctx.target_users,
            features=ctx.features,
            ui_design=ctx.ui_design,
            full_spec=ctx.full_spec,
            files=ctx.generated_files,
            total_cost_cents=ctx.total_cost_cents,
        )

        await store.save(project)
        print(f"📦 Project saved: {project.project_id}")
        return project.project_id

    def _create_success_result(self, ctx: WorkflowContext, project_id: str | None = None) -> AgentResult:
        """Create success result."""
        return AgentResult(
            success=True,
            output={
                "message": f"Successfully generated {ctx.app_name}!",
                "github_repo_url": ctx.github_repo_url,
                "pr_url": ctx.github_pr_url,
                "files_count": len(ctx.generated_files),
                "quality_score": ctx.quality_score,
                "validation_passed": ctx.validation_passed,
                "validation_issues": len(ctx.validation_issues),
                "stages_completed": ctx.completed_stages,
                "project_id": project_id,  # For iterative development
            },
            cost_cents=ctx.total_cost_cents,
            tokens_used=ctx.total_tokens,
        )

    def _create_failed_result(self, ctx: WorkflowContext) -> AgentResult:
        """Create failure result."""
        return AgentResult(
            success=False,
            output={
                "stages_completed": ctx.completed_stages,
                "current_stage": ctx.current_stage.value,
            },
            error="; ".join(ctx.errors) if ctx.errors else "Unknown error",
            cost_cents=ctx.total_cost_cents,
            tokens_used=ctx.total_tokens,
        )
