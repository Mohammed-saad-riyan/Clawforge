"""Docker-based Flutter validator.

Runs Flutter validation commands in a Docker container:
1. flutter pub get - Check dependencies
2. dart run build_runner build - Generate .g.dart/.freezed.dart
3. dart analyze - Static analysis

Uses a warm container for fast execution.
"""

import asyncio
import os
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from clawforge.validator.error_parser import (
    parse_dart_analyze_output,
    parse_pub_get_output,
    parse_build_runner_output,
)


class ValidationStage(Enum):
    """Stages of validation."""
    PUB_GET = "pub_get"
    BUILD_RUNNER = "build_runner"
    ANALYZE = "analyze"


@dataclass
class ValidationError:
    """A single validation error."""
    file_path: str
    line: int
    column: int
    message: str
    severity: str  # "error" | "warning" | "info"
    code: str  # e.g., "undefined_class", "unused_import"

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line": self.line,
            "column": self.column,
            "message": self.message,
            "severity": self.severity,
            "code": self.code,
        }


@dataclass
class ValidationResult:
    """Result of a validation run."""
    success: bool
    stage: ValidationStage
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)
    generated_files: list[str] = field(default_factory=list)  # .g.dart files created
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "stage": self.stage.value,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "generated_files": self.generated_files,
            "duration_seconds": self.duration_seconds,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }


@dataclass
class FullValidationResult:
    """Result of the full validation pipeline."""
    success: bool
    stages_completed: list[ValidationStage]
    pub_get_result: ValidationResult | None = None
    build_runner_result: ValidationResult | None = None
    analyze_result: ValidationResult | None = None
    all_errors: list[ValidationError] = field(default_factory=list)
    all_warnings: list[ValidationError] = field(default_factory=list)
    generated_files: list[str] = field(default_factory=list)
    total_duration_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "stages_completed": [s.value for s in self.stages_completed],
            "all_errors": [e.to_dict() for e in self.all_errors],
            "all_warnings": [w.to_dict() for w in self.all_warnings],
            "generated_files": self.generated_files,
            "total_duration_seconds": self.total_duration_seconds,
            "error_count": len(self.all_errors),
            "warning_count": len(self.all_warnings),
        }


class DockerValidator:
    """Validates Flutter code using Docker container.

    Uses a warm container with Flutter SDK for fast validation.
    Container image: ghcr.io/cirruslabs/flutter:stable
    """

    DOCKER_IMAGE = "ghcr.io/cirruslabs/flutter:stable"
    CONTAINER_NAME = "clawforge-flutter-validator"
    WORKSPACE_BASE = "/tmp/clawforge-workspaces"

    def __init__(
        self,
        docker_image: str | None = None,
        container_name: str | None = None,
        workspace_base: str | None = None,
        timeout_seconds: int = 120,
    ):
        """Initialize the Docker validator.

        Args:
            docker_image: Docker image to use (default: Flutter stable)
            container_name: Name for the warm container
            workspace_base: Base directory for project workspaces
            timeout_seconds: Timeout for each command
        """
        self.docker_image = docker_image or self.DOCKER_IMAGE
        self.container_name = container_name or self.CONTAINER_NAME
        self.workspace_base = workspace_base or self.WORKSPACE_BASE
        self.timeout_seconds = timeout_seconds

        # Ensure workspace base exists
        os.makedirs(self.workspace_base, exist_ok=True)

    async def ensure_container_running(self) -> bool:
        """Ensure the warm container is running.

        Returns:
            True if container is running, False if failed to start
        """
        # Check if container exists and is running
        check_cmd = f"docker ps -q -f name={self.container_name}"
        proc = await asyncio.create_subprocess_shell(
            check_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()

        if stdout.strip():
            # Container is running
            return True

        # Check if container exists but stopped
        check_exists = f"docker ps -aq -f name={self.container_name}"
        proc = await asyncio.create_subprocess_shell(
            check_exists,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()

        if stdout.strip():
            # Container exists but stopped, start it
            start_cmd = f"docker start {self.container_name}"
            proc = await asyncio.create_subprocess_shell(
                start_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            return proc.returncode == 0

        # Container doesn't exist, create it
        print(f"🐳 Creating warm Flutter container: {self.container_name}")
        create_cmd = f"""docker run -d \
            --name {self.container_name} \
            -v {self.workspace_base}:/workspaces \
            {self.docker_image} \
            tail -f /dev/null"""

        proc = await asyncio.create_subprocess_shell(
            create_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()

        if proc.returncode != 0:
            print(f"❌ Failed to create container: {stderr.decode()}")
            return False

        print(f"✅ Container created and running")
        return True

    async def get_container_status(self) -> str:
        """Get the status of the warm container.

        Returns:
            Status string: "running", "stopped", "not_found", or "error"
        """
        check_cmd = f"docker inspect -f '{{{{.State.Status}}}}' {self.container_name} 2>/dev/null"
        proc = await asyncio.create_subprocess_shell(
            check_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()

        if proc.returncode != 0:
            return "not_found"

        return stdout.decode().strip()

    async def _prepare_workspace(
        self,
        project_id: str,
        files: list[dict[str, str]],
    ) -> str:
        """Prepare a workspace directory with project files.

        Args:
            project_id: Unique project identifier
            files: List of {"path": "...", "content": "..."} dictionaries

        Returns:
            Path to the workspace directory
        """
        workspace_path = os.path.join(self.workspace_base, project_id)

        # Clean up existing workspace
        if os.path.exists(workspace_path):
            shutil.rmtree(workspace_path)

        os.makedirs(workspace_path, exist_ok=True)

        # Write all files
        for file_info in files:
            file_path = os.path.join(workspace_path, file_info["path"])
            file_dir = os.path.dirname(file_path)

            if file_dir:
                os.makedirs(file_dir, exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_info["content"])

        return workspace_path

    async def _run_docker_command(
        self,
        project_id: str,
        command: str,
    ) -> tuple[int, str, str]:
        """Run a command in the Docker container.

        Args:
            project_id: Project workspace to run in
            command: Command to execute

        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        full_cmd = f"""docker exec {self.container_name} bash -c "cd /workspaces/{project_id} && {command}" """

        try:
            proc = await asyncio.wait_for(
                asyncio.create_subprocess_shell(
                    full_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                ),
                timeout=self.timeout_seconds,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.timeout_seconds,
            )

            return proc.returncode, stdout.decode(), stderr.decode()

        except asyncio.TimeoutError:
            return -1, "", f"Command timed out after {self.timeout_seconds}s"

    async def run_pub_get(self, project_id: str) -> ValidationResult:
        """Run flutter pub get.

        Args:
            project_id: Project workspace identifier

        Returns:
            ValidationResult with dependency resolution status
        """
        start_time = time.time()

        return_code, stdout, stderr = await self._run_docker_command(
            project_id,
            "flutter pub get 2>&1",
        )

        duration = time.time() - start_time
        errors = []

        if return_code != 0:
            # Parse pub get errors
            errors = parse_pub_get_output(stdout + stderr)

        return ValidationResult(
            success=return_code == 0,
            stage=ValidationStage.PUB_GET,
            errors=errors,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration,
        )

    async def run_build_runner(self, project_id: str) -> ValidationResult:
        """Run dart run build_runner build.

        Args:
            project_id: Project workspace identifier

        Returns:
            ValidationResult with code generation status
        """
        start_time = time.time()

        return_code, stdout, stderr = await self._run_docker_command(
            project_id,
            "dart run build_runner build --delete-conflicting-outputs 2>&1",
        )

        duration = time.time() - start_time

        # Parse generated files
        generated_files = []
        errors = []

        if return_code == 0:
            # Extract generated file names from output
            for line in stdout.split("\n"):
                if ".g.dart" in line or ".freezed.dart" in line:
                    # Extract file path from build_runner output
                    parts = line.split()
                    for part in parts:
                        if part.endswith(".g.dart") or part.endswith(".freezed.dart"):
                            generated_files.append(part)
        else:
            errors = parse_build_runner_output(stdout + stderr)

        return ValidationResult(
            success=return_code == 0,
            stage=ValidationStage.BUILD_RUNNER,
            errors=errors,
            generated_files=generated_files,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration,
        )

    async def run_analyze(self, project_id: str) -> ValidationResult:
        """Run dart analyze.

        Args:
            project_id: Project workspace identifier

        Returns:
            ValidationResult with static analysis results
        """
        start_time = time.time()

        return_code, stdout, stderr = await self._run_docker_command(
            project_id,
            "dart analyze --format=machine 2>&1",
        )

        duration = time.time() - start_time

        # Parse analyze output
        errors, warnings = parse_dart_analyze_output(stdout)

        # Success if no errors (warnings are OK)
        success = len(errors) == 0

        return ValidationResult(
            success=success,
            stage=ValidationStage.ANALYZE,
            errors=errors,
            warnings=warnings,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration,
        )

    async def validate(
        self,
        files: list[dict[str, str]],
        project_id: str | None = None,
        skip_build_runner: bool = False,
    ) -> FullValidationResult:
        """Run the full validation pipeline.

        Args:
            files: List of {"path": "...", "content": "..."} dictionaries
            project_id: Optional project ID (auto-generated if not provided)
            skip_build_runner: Skip build_runner step (for faster iteration)

        Returns:
            FullValidationResult with all validation data
        """
        import uuid

        project_id = project_id or f"proj_{uuid.uuid4().hex[:12]}"
        start_time = time.time()
        stages_completed = []
        all_errors = []
        all_warnings = []
        generated_files = []

        # Ensure container is running
        if not await self.ensure_container_running():
            return FullValidationResult(
                success=False,
                stages_completed=[],
                all_errors=[ValidationError(
                    file_path="",
                    line=0,
                    column=0,
                    message="Failed to start Docker container",
                    severity="error",
                    code="docker_error",
                )],
                total_duration_seconds=time.time() - start_time,
            )

        # Prepare workspace
        print(f"📁 Preparing workspace: {project_id}")
        await self._prepare_workspace(project_id, files)

        # Step 1: flutter pub get
        print("📦 Running flutter pub get...")
        pub_get_result = await self.run_pub_get(project_id)
        stages_completed.append(ValidationStage.PUB_GET)

        if not pub_get_result.success:
            all_errors.extend(pub_get_result.errors)
            return FullValidationResult(
                success=False,
                stages_completed=stages_completed,
                pub_get_result=pub_get_result,
                all_errors=all_errors,
                total_duration_seconds=time.time() - start_time,
            )

        print(f"✅ pub get completed ({pub_get_result.duration_seconds:.1f}s)")

        # Step 2: build_runner (optional)
        build_runner_result = None
        if not skip_build_runner:
            print("🔨 Running build_runner...")
            build_runner_result = await self.run_build_runner(project_id)
            stages_completed.append(ValidationStage.BUILD_RUNNER)
            generated_files = build_runner_result.generated_files

            if not build_runner_result.success:
                # Build runner failure is not always fatal
                # Sometimes it fails on first run but analyze still works
                all_warnings.extend(build_runner_result.errors)
                print(f"⚠️ build_runner had issues, continuing...")
            else:
                print(f"✅ build_runner completed ({build_runner_result.duration_seconds:.1f}s)")
                print(f"   Generated {len(generated_files)} files")

        # Step 3: dart analyze
        print("🔍 Running dart analyze...")
        analyze_result = await self.run_analyze(project_id)
        stages_completed.append(ValidationStage.ANALYZE)
        all_errors.extend(analyze_result.errors)
        all_warnings.extend(analyze_result.warnings)

        if analyze_result.success:
            print(f"✅ analyze completed - No errors! ({analyze_result.duration_seconds:.1f}s)")
        else:
            print(f"❌ analyze found {len(analyze_result.errors)} errors ({analyze_result.duration_seconds:.1f}s)")

        total_duration = time.time() - start_time

        return FullValidationResult(
            success=len(all_errors) == 0,
            stages_completed=stages_completed,
            pub_get_result=pub_get_result,
            build_runner_result=build_runner_result,
            analyze_result=analyze_result,
            all_errors=all_errors,
            all_warnings=all_warnings,
            generated_files=generated_files,
            total_duration_seconds=total_duration,
        )

    async def cleanup_workspace(self, project_id: str) -> None:
        """Clean up a project workspace.

        Args:
            project_id: Project workspace to clean up
        """
        workspace_path = os.path.join(self.workspace_base, project_id)
        if os.path.exists(workspace_path):
            shutil.rmtree(workspace_path)

    async def get_generated_files(self, project_id: str) -> list[dict[str, str]]:
        """Get the generated .g.dart and .freezed.dart files.

        Args:
            project_id: Project workspace identifier

        Returns:
            List of {"path": "...", "content": "..."} for generated files
        """
        workspace_path = os.path.join(self.workspace_base, project_id)
        generated = []

        for root, _, files in os.walk(workspace_path):
            for file in files:
                if file.endswith(".g.dart") or file.endswith(".freezed.dart"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, workspace_path)

                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    generated.append({
                        "path": rel_path,
                        "content": content,
                    })

        return generated


# Singleton instance for reuse
_validator_instance: DockerValidator | None = None


def get_docker_validator() -> DockerValidator:
    """Get the singleton DockerValidator instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = DockerValidator()
    return _validator_instance
