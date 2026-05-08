"""Error parsers for Flutter/Dart command outputs.

Parses output from:
- dart analyze --format=machine
- flutter pub get
- dart run build_runner build
"""

import re
from dataclasses import dataclass
from typing import Any


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


class DartAnalyzeParser:
    """Parser for dart analyze --format=machine output.

    Machine format:
    SEVERITY|TYPE|ERROR_CODE|FILE|LINE|COLUMN|LENGTH|MESSAGE

    Example:
    ERROR|COMPILE_TIME_ERROR|UNDEFINED_CLASS|lib/main.dart|5|10|8|Undefined class 'MyWidget'.
    WARNING|STATIC_WARNING|UNUSED_IMPORT|lib/utils.dart|1|8|25|Unused import: 'dart:async'.
    INFO|INFO|DEAD_CODE|lib/helpers.dart|20|5|15|Dead code.
    """

    # Regex for machine format
    MACHINE_PATTERN = re.compile(
        r'^(ERROR|WARNING|INFO)\|'  # Severity
        r'([^|]+)\|'                 # Type
        r'([^|]+)\|'                 # Error code
        r'([^|]+)\|'                 # File path
        r'(\d+)\|'                   # Line
        r'(\d+)\|'                   # Column
        r'(\d+)\|'                   # Length
        r'(.+)$'                     # Message
    )

    # Alternative human-readable format pattern
    # Example: lib/main.dart:5:10 - error: Undefined class 'MyWidget'. (undefined_class)
    HUMAN_PATTERN = re.compile(
        r'^([^:]+):(\d+):(\d+)\s*-\s*'  # file:line:column -
        r'(error|warning|info|hint):\s*'  # severity:
        r'(.+?)'                          # message
        r'(?:\s*\(([^)]+)\))?$'           # (error_code) - optional
    )

    @classmethod
    def parse(cls, output: str) -> tuple[list[ValidationError], list[ValidationError]]:
        """Parse dart analyze output.

        Args:
            output: Raw output from dart analyze

        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []

        for line in output.strip().split('\n'):
            line = line.strip()
            if not line:
                continue

            # Skip summary lines
            if line.startswith('Analyzing') or line.startswith('No issues found'):
                continue
            if 'issue' in line.lower() and ('found' in line.lower() or 'warning' in line.lower()):
                continue

            # Try machine format first
            match = cls.MACHINE_PATTERN.match(line)
            if match:
                severity, _, error_code, file_path, line_num, column, _, message = match.groups()

                error = ValidationError(
                    file_path=file_path,
                    line=int(line_num),
                    column=int(column),
                    message=message,
                    severity=severity.lower(),
                    code=error_code.lower(),
                )

                if severity == 'ERROR':
                    errors.append(error)
                else:
                    warnings.append(error)
                continue

            # Try human-readable format
            match = cls.HUMAN_PATTERN.match(line)
            if match:
                file_path, line_num, column, severity, message, error_code = match.groups()

                error = ValidationError(
                    file_path=file_path,
                    line=int(line_num),
                    column=int(column),
                    message=message.strip(),
                    severity=severity.lower(),
                    code=error_code.lower() if error_code else "unknown",
                )

                if severity.lower() == 'error':
                    errors.append(error)
                else:
                    warnings.append(error)

        return errors, warnings


def parse_dart_analyze_output(output: str) -> tuple[list[ValidationError], list[ValidationError]]:
    """Parse dart analyze output.

    Args:
        output: Raw output from dart analyze --format=machine

    Returns:
        Tuple of (errors, warnings)
    """
    return DartAnalyzeParser.parse(output)


def parse_pub_get_output(output: str) -> list[ValidationError]:
    """Parse flutter pub get output for errors.

    Common error patterns:
    - Package not found
    - Version conflicts
    - Invalid pubspec.yaml
    - SDK constraint issues

    Args:
        output: Raw output from flutter pub get

    Returns:
        List of ValidationError objects
    """
    errors = []

    # Pattern: Because X depends on Y which doesn't exist
    not_found_pattern = re.compile(
        r"Because (.+?) depends on (.+?) which doesn't exist"
    )

    # Pattern: pub get failed
    pub_failed_pattern = re.compile(
        r"pub get failed"
    )

    # Pattern: version solving failed
    version_pattern = re.compile(
        r"version solving failed|Could not find a version"
    )

    # Pattern: SDK constraint
    sdk_pattern = re.compile(
        r"sdk: ['\"]>=?(\d+\.\d+\.\d+)"
    )

    # Pattern: Invalid pubspec.yaml
    invalid_pubspec_pattern = re.compile(
        r"Error on line (\d+), column (\d+) of pubspec\.yaml"
    )

    # Pattern: dependency not found
    dep_not_found = re.compile(
        r"Could not find package ([a-z_]+)"
    )

    lines = output.split('\n')

    for i, line in enumerate(lines):
        line = line.strip()

        # Check for dependency not existing
        match = not_found_pattern.search(line)
        if match:
            errors.append(ValidationError(
                file_path="pubspec.yaml",
                line=0,
                column=0,
                message=f"Package '{match.group(2)}' doesn't exist",
                severity="error",
                code="package_not_found",
            ))
            continue

        # Check for invalid pubspec
        match = invalid_pubspec_pattern.search(line)
        if match:
            # Get the next line for the actual error message
            error_msg = lines[i + 1].strip() if i + 1 < len(lines) else "Invalid syntax"
            errors.append(ValidationError(
                file_path="pubspec.yaml",
                line=int(match.group(1)),
                column=int(match.group(2)),
                message=error_msg,
                severity="error",
                code="invalid_pubspec",
            ))
            continue

        # Check for version conflicts
        if version_pattern.search(line):
            errors.append(ValidationError(
                file_path="pubspec.yaml",
                line=0,
                column=0,
                message=line,
                severity="error",
                code="version_conflict",
            ))
            continue

        # Check for package not found
        match = dep_not_found.search(line)
        if match:
            errors.append(ValidationError(
                file_path="pubspec.yaml",
                line=0,
                column=0,
                message=f"Package '{match.group(1)}' not found on pub.dev",
                severity="error",
                code="package_not_found",
            ))
            continue

        # Generic pub get failure
        if pub_failed_pattern.search(line) and not errors:
            errors.append(ValidationError(
                file_path="pubspec.yaml",
                line=0,
                column=0,
                message="pub get failed - check dependencies",
                severity="error",
                code="pub_get_failed",
            ))

    return errors


def parse_build_runner_output(output: str) -> list[ValidationError]:
    """Parse dart run build_runner build output for errors.

    Common error patterns:
    - Annotation errors
    - Missing part directives
    - Generator failures

    Args:
        output: Raw output from dart run build_runner build

    Returns:
        List of ValidationError objects
    """
    errors = []

    # Pattern: error on line X column Y of file.dart
    error_pattern = re.compile(
        r"(?:Error|error) on line (\d+), column (\d+) of ([^:]+):\s*(.+)"
    )

    # Pattern: file.dart:line:column: Error: message
    dart_error_pattern = re.compile(
        r"([^:]+\.dart):(\d+):(\d+):\s*Error:\s*(.+)"
    )

    # Pattern: Could not generate for file
    gen_failed_pattern = re.compile(
        r"Could not generate (?:.*?) for ([^\.]+\.dart)"
    )

    # Pattern: Missing part directive
    missing_part_pattern = re.compile(
        r"Missing part directive for ([^\.]+\.g\.dart)"
    )

    # Pattern: Invalid annotation
    invalid_annotation_pattern = re.compile(
        r"(?:Invalid|Unsupported) annotation on (?:class|method|field) '([^']+)'"
    )

    lines = output.split('\n')

    for line in lines:
        line = line.strip()

        # Check for error with line/column
        match = error_pattern.search(line)
        if match:
            errors.append(ValidationError(
                file_path=match.group(3),
                line=int(match.group(1)),
                column=int(match.group(2)),
                message=match.group(4),
                severity="error",
                code="build_runner_error",
            ))
            continue

        # Check for Dart-style errors
        match = dart_error_pattern.search(line)
        if match:
            errors.append(ValidationError(
                file_path=match.group(1),
                line=int(match.group(2)),
                column=int(match.group(3)),
                message=match.group(4),
                severity="error",
                code="dart_error",
            ))
            continue

        # Check for generation failures
        match = gen_failed_pattern.search(line)
        if match:
            errors.append(ValidationError(
                file_path=match.group(1),
                line=0,
                column=0,
                message=f"Code generation failed for {match.group(1)}",
                severity="error",
                code="generation_failed",
            ))
            continue

        # Check for missing part directive
        match = missing_part_pattern.search(line)
        if match:
            # Extract the source file from the .g.dart filename
            source_file = match.group(1).replace('.g.dart', '.dart')
            errors.append(ValidationError(
                file_path=source_file,
                line=0,
                column=0,
                message=f"Missing 'part' directive for {match.group(1)}",
                severity="error",
                code="missing_part",
            ))
            continue

        # Check for invalid annotations
        match = invalid_annotation_pattern.search(line)
        if match:
            errors.append(ValidationError(
                file_path="",
                line=0,
                column=0,
                message=f"Invalid annotation on '{match.group(1)}'",
                severity="error",
                code="invalid_annotation",
            ))

    return errors


def format_errors_for_llm(errors: list[ValidationError]) -> str:
    """Format validation errors into a string suitable for LLM context.

    Args:
        errors: List of ValidationError objects

    Returns:
        Formatted string describing all errors
    """
    if not errors:
        return "No errors found."

    lines = [f"Found {len(errors)} error(s):\n"]

    # Group errors by file
    errors_by_file: dict[str, list[ValidationError]] = {}
    for error in errors:
        file_path = error.file_path or "unknown"
        if file_path not in errors_by_file:
            errors_by_file[file_path] = []
        errors_by_file[file_path].append(error)

    for file_path, file_errors in sorted(errors_by_file.items()):
        lines.append(f"\n📄 {file_path}:")
        for error in sorted(file_errors, key=lambda e: e.line):
            location = f"Line {error.line}" if error.line > 0 else ""
            if error.column > 0:
                location += f":{error.column}"

            lines.append(f"  [{error.severity.upper()}] {location}")
            lines.append(f"    {error.message}")
            if error.code != "unknown":
                lines.append(f"    Code: {error.code}")

    return "\n".join(lines)
