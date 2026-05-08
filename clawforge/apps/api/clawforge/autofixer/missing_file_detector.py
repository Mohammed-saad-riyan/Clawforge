"""Missing file detector for Flutter/Dart projects.

Scans all Dart files for imports and references to files that don't exist.
Returns a list of missing files that need to be generated.
"""

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MissingFileReport:
    """Report of missing files detected."""

    missing_files: list[str] = field(default_factory=list)
    referenced_by: dict[str, list[str]] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)


class MissingFileDetector:
    """Detects files that are imported but don't exist."""

    def __init__(self, package_name: str, all_files: list[dict[str, str]]):
        """Initialize the detector.

        Args:
            package_name: The package name from pubspec.yaml
            all_files: List of all files in the project
        """
        self.package_name = package_name
        self.existing_files: set[str] = set()
        self.file_contents: dict[str, str] = {}

        for file_info in all_files:
            path = file_info["path"]
            self.existing_files.add(path)
            if path.endswith(".dart"):
                self.file_contents[path] = file_info.get("content", "")

    def detect(self) -> MissingFileReport:
        """Detect missing files.

        Returns:
            MissingFileReport with list of missing files
        """
        report = MissingFileReport()
        missing_map: dict[str, list[str]] = {}  # missing_file -> [referencing_files]

        for file_path, content in self.file_contents.items():
            missing = self._find_missing_imports(file_path, content)
            for missing_file in missing:
                if missing_file not in missing_map:
                    missing_map[missing_file] = []
                missing_map[missing_file].append(file_path)

        report.missing_files = list(missing_map.keys())
        report.referenced_by = missing_map

        # Generate suggestions for common patterns
        for missing_file in report.missing_files:
            suggestion = self._generate_suggestion(missing_file)
            if suggestion:
                report.suggestions.append(suggestion)

        return report

    def _find_missing_imports(self, file_path: str, content: str) -> list[str]:
        """Find imports in a file that reference non-existent files."""
        missing = []

        # Pattern for package imports from our package
        package_pattern = rf"import\s+'package:{re.escape(self.package_name)}/([^']+)';"
        matches = re.findall(package_pattern, content)

        for import_path in matches:
            full_path = f"lib/{import_path}"

            # Skip generated files (they'll be created by build_runner)
            if import_path.endswith(".g.dart") or import_path.endswith(".freezed.dart"):
                continue

            # Check if file exists
            if full_path not in self.existing_files:
                if full_path not in missing:
                    missing.append(full_path)

        # Also check for class references that might indicate missing files
        # This catches cases where a class is used but never imported
        missing.extend(self._find_undefined_references(file_path, content))

        return missing

    def _find_undefined_references(self, file_path: str, content: str) -> list[str]:
        """Find class references that might indicate missing files."""
        missing = []

        # Common Flutter naming patterns that suggest missing files
        patterns = [
            # Providers: SomeProvider -> some_provider.dart
            (r"\b(\w+Provider)\b", "providers"),
            # Screens: SomeScreen -> some_screen.dart
            (r"\b(\w+Screen)\b", "screens"),
            # Widgets: SomeWidget -> some_widget.dart
            (r"\b(\w+Widget)\b", "widgets"),
            # Controllers: SomeController -> some_controller.dart
            (r"\b(\w+Controller)\b", "controllers"),
        ]

        # Build a set of all defined classes in the project
        defined_classes: set[str] = set()
        for path, file_content in self.file_contents.items():
            classes = re.findall(r"class\s+(\w+)", file_content)
            defined_classes.update(classes)

        for pattern, folder_hint in patterns:
            matches = set(re.findall(pattern, content))

            for class_name in matches:
                # Skip if class is defined somewhere in the project
                if class_name in defined_classes:
                    continue

                # Skip common Flutter/Dart classes
                if class_name in {
                    "StatelessWidget", "StatefulWidget", "ConsumerWidget",
                    "Widget", "State", "BuildContext", "Key",
                    "ChangeNotifierProvider", "Provider", "FutureProvider",
                    "StreamProvider", "StateNotifierProvider",
                }:
                    continue

                # Suggest a file path based on the class name
                snake_name = self._to_snake_case(class_name)
                feature = self._extract_feature_from_path(file_path)

                if feature:
                    suggested_path = f"lib/features/{feature}/{folder_hint}/{snake_name}.dart"
                else:
                    suggested_path = f"lib/{folder_hint}/{snake_name}.dart"

                if suggested_path not in self.existing_files and suggested_path not in missing:
                    missing.append(suggested_path)

        return missing

    def _to_snake_case(self, name: str) -> str:
        """Convert PascalCase to snake_case."""
        # Insert underscore before uppercase letters and convert to lowercase
        s = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        return s

    def _extract_feature_from_path(self, file_path: str) -> str | None:
        """Extract the feature name from a file path."""
        match = re.search(r"lib/features/(\w+)/", file_path)
        if match:
            return match.group(1)
        return None

    def _generate_suggestion(self, missing_file: str) -> str:
        """Generate a suggestion for what to do about a missing file."""
        if "provider" in missing_file:
            return f"Generate Riverpod provider: {missing_file}"
        elif "widget" in missing_file:
            return f"Generate Flutter widget: {missing_file}"
        elif "screen" in missing_file:
            return f"Generate screen widget: {missing_file}"
        elif "model" in missing_file:
            return f"Generate Freezed model: {missing_file}"
        else:
            return f"Generate file: {missing_file}"


def detect_missing_files(
    files: list[dict[str, str]],
    package_name: str = "my_app",
) -> MissingFileReport:
    """Detect missing files in a Flutter project.

    Args:
        files: List of {"path": "...", "content": "..."} dictionaries
        package_name: The package name for imports

    Returns:
        MissingFileReport with missing files and suggestions
    """
    detector = MissingFileDetector(package_name=package_name, all_files=files)
    return detector.detect()
