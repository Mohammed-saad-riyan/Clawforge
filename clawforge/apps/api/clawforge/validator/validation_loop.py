"""Validation loop orchestrator.

Runs the validate → fix → re-validate loop:
1. Run Docker validation (pub get, build_runner, analyze)
2. If errors, pass to Refiner Agent
3. Re-validate fixed code
4. Repeat up to max_iterations times
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

from clawforge.validator.docker_validator import (
    DockerValidator,
    FullValidationResult,
    ValidationError,
    ValidationStage,
    get_docker_validator,
)
from clawforge.validator.error_parser import format_errors_for_llm


@dataclass
class ValidationLoopResult:
    """Result of the full validation loop."""
    success: bool
    iterations_used: int
    max_iterations: int
    final_validation: FullValidationResult | None
    all_iterations: list[FullValidationResult] = field(default_factory=list)
    fixes_applied: list[dict[str, Any]] = field(default_factory=list)
    final_files: list[dict[str, str]] = field(default_factory=list)
    generated_files: list[dict[str, str]] = field(default_factory=list)
    total_duration_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "iterations_used": self.iterations_used,
            "max_iterations": self.max_iterations,
            "final_errors": [e.to_dict() for e in (self.final_validation.all_errors if self.final_validation else [])],
            "final_warnings": [w.to_dict() for w in (self.final_validation.all_warnings if self.final_validation else [])],
            "fixes_applied_count": len(self.fixes_applied),
            "generated_files_count": len(self.generated_files),
            "total_duration_seconds": self.total_duration_seconds,
        }


# Type alias for the fix function
FixFunction = Callable[
    [list[ValidationError], list[dict[str, str]], dict[str, Any]],
    Awaitable[list[dict[str, str]]]
]


class ValidationLoop:
    """Orchestrates the validation → fix → re-validate loop.

    The loop runs until:
    1. Validation passes (no errors)
    2. Max iterations reached
    3. No fixes were made in an iteration (stuck)
    """

    def __init__(
        self,
        validator: DockerValidator | None = None,
        max_iterations: int = 3,
        fix_function: FixFunction | None = None,
    ):
        """Initialize the validation loop.

        Args:
            validator: DockerValidator instance (uses singleton if not provided)
            max_iterations: Maximum fix attempts
            fix_function: Async function to fix errors.
                         Signature: (errors, files, context) -> fixed_files
        """
        self.validator = validator or get_docker_validator()
        self.max_iterations = max_iterations
        self.fix_function = fix_function

    async def run(
        self,
        files: list[dict[str, str]],
        project_id: str | None = None,
        context: dict[str, Any] | None = None,
        skip_build_runner: bool = False,
        on_iteration: Callable[[int, FullValidationResult], None] | None = None,
    ) -> ValidationLoopResult:
        """Run the validation loop.

        Args:
            files: List of {"path": "...", "content": "..."} dictionaries
            project_id: Optional project identifier
            context: Additional context for the fix function (plan, conversation, etc.)
            skip_build_runner: Skip build_runner step for faster iteration
            on_iteration: Callback after each iteration

        Returns:
            ValidationLoopResult with final state
        """
        import time
        import uuid

        start_time = time.time()
        project_id = project_id or f"proj_{uuid.uuid4().hex[:12]}"
        context = context or {}

        all_iterations: list[FullValidationResult] = []
        fixes_applied: list[dict[str, Any]] = []
        current_files = files.copy()

        for iteration in range(1, self.max_iterations + 1):
            print(f"\n{'='*60}")
            print(f"🔄 Validation Loop - Iteration {iteration}/{self.max_iterations}")
            print(f"{'='*60}")

            # Run validation
            validation_result = await self.validator.validate(
                files=current_files,
                project_id=project_id,
                skip_build_runner=skip_build_runner,
            )
            all_iterations.append(validation_result)

            # Callback for progress tracking
            if on_iteration:
                on_iteration(iteration, validation_result)

            # Check if validation passed
            if validation_result.success:
                print(f"✅ Validation passed on iteration {iteration}!")

                # Get generated files
                generated_files = await self.validator.get_generated_files(project_id)

                return ValidationLoopResult(
                    success=True,
                    iterations_used=iteration,
                    max_iterations=self.max_iterations,
                    final_validation=validation_result,
                    all_iterations=all_iterations,
                    fixes_applied=fixes_applied,
                    final_files=current_files,
                    generated_files=generated_files,
                    total_duration_seconds=time.time() - start_time,
                )

            # If no fix function, can't proceed
            if self.fix_function is None:
                print("❌ Validation failed and no fix function provided")
                break

            # Get all errors to fix
            errors_to_fix = validation_result.all_errors

            if not errors_to_fix:
                # No errors but not successful? Unusual, but break
                print("⚠️ No errors found but validation not successful")
                break

            print(f"\n📋 Found {len(errors_to_fix)} errors to fix:")
            print(format_errors_for_llm(errors_to_fix))

            # If this is the last iteration, don't try to fix
            if iteration == self.max_iterations:
                print(f"⚠️ Max iterations ({self.max_iterations}) reached")
                break

            # Call fix function
            print(f"\n🔧 Attempting to fix errors...")
            try:
                fixed_files = await self.fix_function(
                    errors_to_fix,
                    current_files,
                    {
                        **context,
                        "iteration": iteration,
                        "validation_result": validation_result.to_dict(),
                    }
                )

                # Check if any files were actually changed
                files_changed = self._count_changed_files(current_files, fixed_files)

                if files_changed == 0:
                    print("⚠️ Fix function returned no changes - stuck")
                    break

                print(f"✅ Fixed {files_changed} file(s)")

                fixes_applied.append({
                    "iteration": iteration,
                    "errors_count": len(errors_to_fix),
                    "files_changed": files_changed,
                })

                current_files = fixed_files

            except Exception as e:
                print(f"❌ Fix function failed: {e}")
                break

        # Loop ended without success
        final_validation = all_iterations[-1] if all_iterations else None

        # Get generated files even on failure
        generated_files = []
        try:
            generated_files = await self.validator.get_generated_files(project_id)
        except Exception:
            pass

        return ValidationLoopResult(
            success=False,
            iterations_used=len(all_iterations),
            max_iterations=self.max_iterations,
            final_validation=final_validation,
            all_iterations=all_iterations,
            fixes_applied=fixes_applied,
            final_files=current_files,
            generated_files=generated_files,
            total_duration_seconds=time.time() - start_time,
        )

    def _count_changed_files(
        self,
        original: list[dict[str, str]],
        updated: list[dict[str, str]],
    ) -> int:
        """Count how many files were changed.

        Args:
            original: Original files
            updated: Updated files

        Returns:
            Number of files that changed
        """
        original_dict = {f["path"]: f["content"] for f in original}
        updated_dict = {f["path"]: f["content"] for f in updated}

        changed = 0

        # Check for new or modified files
        for path, content in updated_dict.items():
            if path not in original_dict:
                changed += 1
            elif original_dict[path] != content:
                changed += 1

        return changed


async def run_validation_loop(
    files: list[dict[str, str]],
    fix_function: FixFunction | None = None,
    project_id: str | None = None,
    max_iterations: int = 3,
    context: dict[str, Any] | None = None,
    skip_build_runner: bool = False,
) -> ValidationLoopResult:
    """Run the validation loop with default settings.

    Convenience function that creates a ValidationLoop and runs it.

    Args:
        files: List of {"path": "...", "content": "..."} dictionaries
        fix_function: Async function to fix errors
        project_id: Optional project identifier
        max_iterations: Maximum fix attempts
        context: Additional context for the fix function
        skip_build_runner: Skip build_runner step

    Returns:
        ValidationLoopResult with final state
    """
    loop = ValidationLoop(
        max_iterations=max_iterations,
        fix_function=fix_function,
    )

    return await loop.run(
        files=files,
        project_id=project_id,
        context=context,
        skip_build_runner=skip_build_runner,
    )


# Example fix function using Refiner Agent
async def create_refiner_fix_function(
    refiner_agent_fn: Callable,
    plan: dict[str, Any] | None = None,
) -> FixFunction:
    """Create a fix function that uses the Refiner Agent.

    Args:
        refiner_agent_fn: The refiner agent's run function
        plan: The app plan for context

    Returns:
        A FixFunction that can be passed to ValidationLoop
    """
    async def fix_with_refiner(
        errors: list[ValidationError],
        files: list[dict[str, str]],
        context: dict[str, Any],
    ) -> list[dict[str, str]]:
        """Fix errors using the Refiner Agent."""

        # Format errors for the LLM
        error_summary = format_errors_for_llm(errors)

        # Create a refinement request message
        fix_message = f"""Please fix the following validation errors in the Flutter code:

{error_summary}

Focus on:
1. Adding missing imports
2. Creating missing files/classes that are referenced
3. Fixing type errors
4. Resolving any other issues

Return the complete fixed files."""

        # Build file contents dict
        file_contents = {f["path"]: f["content"] for f in files}

        # Call refiner agent
        result = await refiner_agent_fn(
            message=fix_message,
            current_files=file_contents,
            plan=plan,
            validation_errors=errors,
            auto_fix_mode=True,
        )

        # Convert result back to list format
        if hasattr(result, 'files_changed'):
            # Merge changed files with original
            updated_dict = file_contents.copy()
            for file_change in result.files_changed:
                updated_dict[file_change["path"]] = file_change["content"]

            return [{"path": k, "content": v} for k, v in updated_dict.items()]

        return files  # Return original if refiner didn't work

    return fix_with_refiner
