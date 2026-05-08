"""Flutter web preview service.

Builds Flutter web version of generated code and deploys to a preview URL.
"""

import asyncio
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class PreviewResult:
    """Result of preview generation."""

    success: bool
    preview_url: str = ""
    build_output: str = ""
    error: str = ""
    build_time_seconds: float = 0.0


async def build_flutter_web(
    files: list[dict[str, str]],
    app_name: str,
    timeout_seconds: int = 300,
) -> PreviewResult:
    """Build Flutter web version of the generated code.

    Args:
        files: List of {"path": "...", "content": "..."} dictionaries
        app_name: Name of the app
        timeout_seconds: Maximum time for build

    Returns:
        PreviewResult with success status and build output
    """
    import time
    start_time = time.time()

    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix=f"clawforge_preview_{app_name}_")

    try:
        # Write all files to temp directory
        for file_info in files:
            file_path = Path(temp_dir) / file_info["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(file_info["content"])

        # Run flutter pub get
        print(f"📦 Running flutter pub get...")
        pub_result = await _run_command(
            ["flutter", "pub", "get"],
            cwd=temp_dir,
            timeout=60,
        )

        if pub_result["returncode"] != 0:
            return PreviewResult(
                success=False,
                error=f"flutter pub get failed: {pub_result['stderr']}",
                build_output=pub_result["stdout"],
            )

        # Run build_runner if needed (for generated code)
        if _has_build_runner(files):
            print(f"🔨 Running build_runner...")
            build_runner_result = await _run_command(
                ["dart", "run", "build_runner", "build", "--delete-conflicting-outputs"],
                cwd=temp_dir,
                timeout=120,
            )

            if build_runner_result["returncode"] != 0:
                # Build runner failure is not fatal, continue
                print(f"⚠️ build_runner warning: {build_runner_result['stderr'][:200]}")

        # Build Flutter web
        print(f"🌐 Building Flutter web...")
        build_result = await _run_command(
            ["flutter", "build", "web", "--release"],
            cwd=temp_dir,
            timeout=timeout_seconds,
        )

        build_time = time.time() - start_time

        if build_result["returncode"] != 0:
            return PreviewResult(
                success=False,
                error=f"flutter build web failed: {build_result['stderr']}",
                build_output=build_result["stdout"],
                build_time_seconds=build_time,
            )

        # Build successful - the output is in build/web/
        build_dir = Path(temp_dir) / "build" / "web"

        if not build_dir.exists():
            return PreviewResult(
                success=False,
                error="Build succeeded but build/web directory not found",
                build_output=build_result["stdout"],
                build_time_seconds=build_time,
            )

        return PreviewResult(
            success=True,
            build_output=build_result["stdout"],
            build_time_seconds=build_time,
            # Note: preview_url will be set by the deployment step
        )

    except asyncio.TimeoutError:
        return PreviewResult(
            success=False,
            error=f"Build timed out after {timeout_seconds} seconds",
        )

    except Exception as e:
        return PreviewResult(
            success=False,
            error=f"Build failed: {str(e)}",
        )

    finally:
        # Keep temp directory for now (for deployment)
        # In production, clean up after deployment
        pass


async def deploy_to_vercel(
    build_dir: str,
    project_name: str,
) -> dict[str, Any]:
    """Deploy built Flutter web to Vercel.

    Args:
        build_dir: Path to build/web directory
        project_name: Name for the Vercel project

    Returns:
        Dict with deployment URL and status
    """
    # Check if Vercel CLI is available
    vercel_check = await _run_command(["vercel", "--version"], cwd="/tmp", timeout=5)

    if vercel_check["returncode"] != 0:
        return {
            "success": False,
            "error": "Vercel CLI not installed. Install with: npm i -g vercel",
        }

    # Deploy to Vercel (requires VERCEL_TOKEN environment variable)
    token = os.environ.get("VERCEL_TOKEN")
    if not token:
        return {
            "success": False,
            "error": "VERCEL_TOKEN environment variable not set",
        }

    deploy_result = await _run_command(
        [
            "vercel",
            "--yes",
            "--token", token,
            "--name", project_name,
            "--prod",
        ],
        cwd=build_dir,
        timeout=120,
    )

    if deploy_result["returncode"] != 0:
        return {
            "success": False,
            "error": f"Vercel deployment failed: {deploy_result['stderr']}",
        }

    # Parse the preview URL from output
    # Vercel outputs the URL on success
    url = deploy_result["stdout"].strip().split("\n")[-1]

    return {
        "success": True,
        "preview_url": url,
        "output": deploy_result["stdout"],
    }


async def generate_preview(
    files: list[dict[str, str]],
    app_name: str,
    deploy: bool = False,
) -> PreviewResult:
    """Generate a preview of the Flutter app.

    Args:
        files: List of generated files
        app_name: Name of the app
        deploy: Whether to deploy to Vercel

    Returns:
        PreviewResult with preview URL if deployed
    """
    # Build the Flutter web version
    result = await build_flutter_web(files, app_name)

    if not result.success:
        return result

    if deploy:
        # Deploy to Vercel
        # TODO: Implement Vercel deployment
        pass

    return result


def _has_build_runner(files: list[dict[str, str]]) -> bool:
    """Check if project uses build_runner."""
    for file in files:
        if file["path"] == "pubspec.yaml":
            content = file["content"]
            return "build_runner:" in content
    return False


async def _run_command(
    cmd: list[str],
    cwd: str,
    timeout: int,
) -> dict[str, Any]:
    """Run a command asynchronously."""
    process = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout,
        )
        return {
            "returncode": process.returncode,
            "stdout": stdout.decode("utf-8"),
            "stderr": stderr.decode("utf-8"),
        }
    except asyncio.TimeoutError:
        process.kill()
        raise
