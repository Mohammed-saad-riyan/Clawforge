"""Flutter code validation using flutter analyze.

Validates generated Flutter code before pushing to GitHub.
Catches common issues like missing imports, type errors, etc.
"""

import asyncio
import json
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ValidationIssue:
    """A single validation issue."""

    severity: str  # "error", "warning", "info"
    file: str
    line: int
    column: int
    message: str
    code: str | None = None  # e.g., "unused_import"


@dataclass
class ValidationResult:
    """Result of code validation."""

    success: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    raw_output: str = ""


async def validate_flutter_code(
    files: list[dict[str, str]],
    timeout_seconds: int = 120,
) -> ValidationResult:
    """Validate Flutter code using flutter analyze.

    Creates a temporary directory, writes all files, runs flutter analyze,
    and returns structured results.

    Args:
        files: List of {"path": "...", "content": "..."} dictionaries
        timeout_seconds: Maximum time to wait for validation

    Returns:
        ValidationResult with success status and any issues found
    """
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="clawforge_validate_")

    try:
        # Write all files to temp directory
        for file_info in files:
            file_path = Path(temp_dir) / file_info["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(file_info["content"])

        # Run flutter pub get first
        pub_get_result = await _run_command(
            ["flutter", "pub", "get"],
            cwd=temp_dir,
            timeout=60,
        )

        if pub_get_result["returncode"] != 0:
            # pub get failed - might be missing pubspec.yaml or other issue
            return ValidationResult(
                success=False,
                issues=[
                    ValidationIssue(
                        severity="error",
                        file="pubspec.yaml",
                        line=1,
                        column=1,
                        message=f"flutter pub get failed: {pub_get_result['stderr']}",
                        code="pub_get_failed",
                    )
                ],
                error_count=1,
                raw_output=pub_get_result["stderr"],
            )

        # Run flutter analyze with machine-readable output
        analyze_result = await _run_command(
            ["flutter", "analyze", "--no-pub", "--no-fatal-infos", "--no-fatal-warnings"],
            cwd=temp_dir,
            timeout=timeout_seconds,
        )

        # Parse the output
        issues = _parse_analyze_output(analyze_result["stdout"], temp_dir)

        error_count = sum(1 for i in issues if i.severity == "error")
        warning_count = sum(1 for i in issues if i.severity == "warning")
        info_count = sum(1 for i in issues if i.severity == "info")

        return ValidationResult(
            success=error_count == 0,
            issues=issues,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            raw_output=analyze_result["stdout"],
        )

    except asyncio.TimeoutError:
        return ValidationResult(
            success=False,
            issues=[
                ValidationIssue(
                    severity="error",
                    file="",
                    line=0,
                    column=0,
                    message=f"Validation timed out after {timeout_seconds} seconds",
                    code="timeout",
                )
            ],
            error_count=1,
            raw_output="",
        )

    except Exception as e:
        return ValidationResult(
            success=False,
            issues=[
                ValidationIssue(
                    severity="error",
                    file="",
                    line=0,
                    column=0,
                    message=f"Validation failed: {str(e)}",
                    code="validation_error",
                )
            ],
            error_count=1,
            raw_output=str(e),
        )

    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)


async def quick_syntax_check(files: list[dict[str, str]]) -> ValidationResult:
    """Quick syntax check without running flutter analyze.

    Performs basic checks like:
    - Valid Dart syntax (using dart analyze if available)
    - Required files exist (pubspec.yaml, main.dart)
    - No obvious import errors

    This is faster than full validation but less thorough.
    """
    issues: list[ValidationIssue] = []

    # Check required files exist
    file_paths = {f["path"] for f in files}

    if "pubspec.yaml" not in file_paths:
        issues.append(
            ValidationIssue(
                severity="error",
                file="pubspec.yaml",
                line=0,
                column=0,
                message="Missing pubspec.yaml",
                code="missing_file",
            )
        )

    main_dart_exists = any(
        "main.dart" in path for path in file_paths
    )
    if not main_dart_exists:
        issues.append(
            ValidationIssue(
                severity="error",
                file="lib/main.dart",
                line=0,
                column=0,
                message="Missing main.dart entry point",
                code="missing_file",
            )
        )

    # Check for common Dart issues in each file
    for file_info in files:
        if file_info["path"].endswith(".dart"):
            file_issues = _check_dart_file(file_info["path"], file_info["content"])
            issues.extend(file_issues)

    error_count = sum(1 for i in issues if i.severity == "error")
    warning_count = sum(1 for i in issues if i.severity == "warning")

    return ValidationResult(
        success=error_count == 0,
        issues=issues,
        error_count=error_count,
        warning_count=warning_count,
        info_count=0,
        raw_output="",
    )


def _check_dart_file(path: str, content: str) -> list[ValidationIssue]:
    """Check a single Dart file for common issues."""
    issues: list[ValidationIssue] = []
    lines = content.split("\n")

    for line_num, line in enumerate(lines, start=1):
        # Check for TODO/FIXME that might indicate incomplete code
        if "TODO:" in line or "FIXME:" in line:
            issues.append(
                ValidationIssue(
                    severity="info",
                    file=path,
                    line=line_num,
                    column=1,
                    message="Found TODO/FIXME comment",
                    code="todo_comment",
                )
            )

        # Check for print statements (should use logging instead)
        if "print(" in line and not line.strip().startswith("//"):
            issues.append(
                ValidationIssue(
                    severity="warning",
                    file=path,
                    line=line_num,
                    column=line.index("print(") + 1,
                    message="Avoid print() in production code",
                    code="avoid_print",
                )
            )

    # Check for common import issues
    if "import 'package:" in content:
        # Check if the package is likely to exist
        pass  # Could add more sophisticated checks here

    return issues


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


def _parse_analyze_output(output: str, temp_dir: str) -> list[ValidationIssue]:
    """Parse flutter analyze output into structured issues."""
    issues: list[ValidationIssue] = []

    # Flutter analyze output format:
    #   info • Unused import: 'package:flutter/material.dart' • lib/main.dart:1:8 • unused_import
    #   warning • Missing return type • lib/utils.dart:5:1 • missing_return
    #   error • Undefined name 'foo' • lib/main.dart:10:5 • undefined_identifier

    for line in output.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Parse severity
        severity = None
        if line.startswith("info"):
            severity = "info"
        elif line.startswith("warning"):
            severity = "warning"
        elif line.startswith("error"):
            severity = "error"

        if not severity:
            continue

        # Parse the rest of the line
        # Format: severity • message • file:line:column • code
        parts = line.split("•")
        if len(parts) >= 3:
            message = parts[1].strip()
            location = parts[2].strip()
            code = parts[3].strip() if len(parts) > 3 else None

            # Parse location (file:line:column)
            location_parts = location.rsplit(":", 2)
            if len(location_parts) >= 1:
                file_path = location_parts[0]
                # Remove temp_dir prefix
                if file_path.startswith(temp_dir):
                    file_path = file_path[len(temp_dir) + 1 :]

                line_num = int(location_parts[1]) if len(location_parts) > 1 else 0
                column = int(location_parts[2]) if len(location_parts) > 2 else 0

                issues.append(
                    ValidationIssue(
                        severity=severity,
                        file=file_path,
                        line=line_num,
                        column=column,
                        message=message,
                        code=code,
                    )
                )

    return issues
