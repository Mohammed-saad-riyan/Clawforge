"""Pubspec.yaml dependency fixer.

Scans Dart code for used packages and ensures they're in pubspec.yaml.
Similar to how v0 completes missing dependencies in package.json.
"""

import re
from dataclasses import dataclass, field
from typing import Any
import yaml


@dataclass
class PubspecFixResult:
    """Result of pubspec fixing."""

    original_content: str
    fixed_content: str
    dependencies_added: list[str] = field(default_factory=list)
    dev_dependencies_added: list[str] = field(default_factory=list)
    success: bool = True
    errors: list[str] = field(default_factory=list)


# Map of import packages to pubspec dependencies with versions
PACKAGE_VERSIONS = {
    # Core Flutter
    "flutter": {"flutter": {"sdk": "flutter"}},

    # State Management
    "flutter_riverpod": {"flutter_riverpod": "^2.5.1"},
    "riverpod_annotation": {"riverpod_annotation": "^2.3.5"},
    "hooks_riverpod": {"hooks_riverpod": "^2.5.1"},

    # Navigation
    "go_router": {"go_router": "^14.2.0"},
    "auto_route": {"auto_route": "^8.1.0"},

    # Networking
    "dio": {"dio": "^5.4.0"},
    "http": {"http": "^1.2.0"},
    "retrofit": {"retrofit": "^4.1.0"},

    # Data/Serialization
    "freezed_annotation": {"freezed_annotation": "^2.4.1"},
    "json_annotation": {"json_annotation": "^4.8.1"},

    # Local Storage
    "drift": {"drift": "^2.16.0"},
    "shared_preferences": {"shared_preferences": "^2.2.2"},
    "hive": {"hive": "^2.2.3"},
    "hive_flutter": {"hive_flutter": "^1.1.0"},
    "isar": {"isar": "^3.1.0+1"},
    "sqflite": {"sqflite": "^2.3.2"},

    # UI Components
    "flutter_hooks": {"flutter_hooks": "^0.20.5"},
    "cached_network_image": {"cached_network_image": "^3.3.1"},
    "flutter_svg": {"flutter_svg": "^2.0.9"},
    "shimmer": {"shimmer": "^3.0.0"},
    "flutter_spinkit": {"flutter_spinkit": "^5.2.0"},
    "lottie": {"lottie": "^3.1.0"},
    "animations": {"animations": "^2.0.11"},

    # Forms & Validation
    "flutter_form_builder": {"flutter_form_builder": "^9.2.1"},
    "form_builder_validators": {"form_builder_validators": "^9.1.0"},
    "reactive_forms": {"reactive_forms": "^17.0.1"},

    # Utilities
    "intl": {"intl": "^0.19.0"},
    "url_launcher": {"url_launcher": "^6.2.4"},
    "path_provider": {"path_provider": "^2.1.2"},
    "image_picker": {"image_picker": "^1.0.7"},
    "permission_handler": {"permission_handler": "^11.3.0"},
    "connectivity_plus": {"connectivity_plus": "^6.0.1"},
    "package_info_plus": {"package_info_plus": "^5.0.1"},
    "device_info_plus": {"device_info_plus": "^10.1.0"},

    # Firebase
    "firebase_core": {"firebase_core": "^2.25.4"},
    "firebase_auth": {"firebase_auth": "^4.17.4"},
    "cloud_firestore": {"cloud_firestore": "^4.15.4"},
    "firebase_storage": {"firebase_storage": "^11.6.5"},
    "firebase_messaging": {"firebase_messaging": "^14.7.15"},

    # Authentication
    "google_sign_in": {"google_sign_in": "^6.2.1"},
    "sign_in_with_apple": {"sign_in_with_apple": "^6.1.0"},
    "flutter_facebook_auth": {"flutter_facebook_auth": "^6.1.1"},

    # Icons
    "font_awesome_flutter": {"font_awesome_flutter": "^10.7.0"},
    "flutter_vector_icons": {"flutter_vector_icons": "^2.0.0"},
}

# Dev dependencies
DEV_PACKAGE_VERSIONS = {
    # Code generation
    "build_runner": {"build_runner": "^2.4.8"},
    "freezed": {"freezed": "^2.4.7"},
    "json_serializable": {"json_serializable": "^6.7.1"},
    "riverpod_generator": {"riverpod_generator": "^2.4.0"},
    "retrofit_generator": {"retrofit_generator": "^8.1.0"},
    "auto_route_generator": {"auto_route_generator": "^8.0.0"},
    "drift_dev": {"drift_dev": "^2.16.0"},
    "isar_generator": {"isar_generator": "^3.1.0+1"},
    "hive_generator": {"hive_generator": "^2.0.1"},

    # Testing
    "flutter_test": {"flutter_test": {"sdk": "flutter"}},
    "mockito": {"mockito": "^5.4.4"},
    "mocktail": {"mocktail": "^1.0.3"},
    "bloc_test": {"bloc_test": "^9.1.6"},

    # Linting
    "flutter_lints": {"flutter_lints": "^3.0.1"},
    "very_good_analysis": {"very_good_analysis": "^5.1.0"},
}


class PubspecFixer:
    """Fixer for pubspec.yaml dependencies."""

    def fix(
        self,
        pubspec_content: str,
        dart_files: list[dict[str, str]],
    ) -> PubspecFixResult:
        """Fix pubspec.yaml by adding missing dependencies.

        Args:
            pubspec_content: Current pubspec.yaml content
            dart_files: List of Dart files to scan for imports

        Returns:
            PubspecFixResult with fixed content
        """
        try:
            # Parse existing pubspec
            pubspec = yaml.safe_load(pubspec_content) or {}

            existing_deps = pubspec.get("dependencies", {}) or {}
            existing_dev_deps = pubspec.get("dev_dependencies", {}) or {}

            # Scan all Dart files for imports
            used_packages = self._scan_imports(dart_files)

            # Find missing dependencies
            deps_to_add = {}
            dev_deps_to_add = {}

            for package in used_packages:
                # Check if it's a regular dependency
                if package in PACKAGE_VERSIONS:
                    if package not in existing_deps:
                        deps_to_add.update(PACKAGE_VERSIONS[package])

                # Check if related dev dependency is needed
                if package in DEV_PACKAGE_VERSIONS:
                    if package not in existing_dev_deps:
                        dev_deps_to_add.update(DEV_PACKAGE_VERSIONS[package])

            # Check for code generation needs
            code_gen_triggers = {
                "freezed_annotation": ["freezed", "build_runner"],
                "json_annotation": ["json_serializable", "build_runner"],
                "riverpod_annotation": ["riverpod_generator", "build_runner"],
                "retrofit": ["retrofit_generator", "build_runner"],
                "drift": ["drift_dev", "build_runner"],
                "auto_route": ["auto_route_generator", "build_runner"],
            }

            for trigger, dev_deps in code_gen_triggers.items():
                if trigger in used_packages or trigger in existing_deps:
                    for dev_dep in dev_deps:
                        if dev_dep not in existing_dev_deps and dev_dep not in dev_deps_to_add:
                            if dev_dep in DEV_PACKAGE_VERSIONS:
                                dev_deps_to_add.update(DEV_PACKAGE_VERSIONS[dev_dep])

            # Update pubspec
            if deps_to_add:
                if "dependencies" not in pubspec:
                    pubspec["dependencies"] = {}
                pubspec["dependencies"].update(deps_to_add)

            if dev_deps_to_add:
                if "dev_dependencies" not in pubspec:
                    pubspec["dev_dependencies"] = {}
                pubspec["dev_dependencies"].update(dev_deps_to_add)

            # Generate new YAML content
            fixed_content = self._generate_pubspec_yaml(pubspec)

            return PubspecFixResult(
                original_content=pubspec_content,
                fixed_content=fixed_content,
                dependencies_added=list(deps_to_add.keys()),
                dev_dependencies_added=list(dev_deps_to_add.keys()),
                success=True,
            )

        except Exception as e:
            return PubspecFixResult(
                original_content=pubspec_content,
                fixed_content=pubspec_content,
                success=False,
                errors=[str(e)],
            )

    def _scan_imports(self, dart_files: list[dict[str, str]]) -> set[str]:
        """Scan Dart files for imported packages."""
        packages = set()

        for file_info in dart_files:
            content = file_info.get("content", "")

            # Find all package imports: import 'package:xxx/...';
            import_pattern = r"import\s+'package:([^/]+)/[^']*';"
            matches = re.findall(import_pattern, content)
            packages.update(matches)

            # Also check for annotations that require packages
            annotation_packages = {
                "@freezed": "freezed_annotation",
                "@Freezed": "freezed_annotation",
                "@riverpod": "riverpod_annotation",
                "@Riverpod": "riverpod_annotation",
                "@JsonSerializable": "json_annotation",
                "@RestApi": "retrofit",
                "@DriftDatabase": "drift",
                "@HiveType": "hive",
            }

            for annotation, package in annotation_packages.items():
                if annotation in content:
                    packages.add(package)

        return packages

    def _generate_pubspec_yaml(self, pubspec: dict) -> str:
        """Generate properly formatted pubspec.yaml content."""
        # Custom YAML dumping to maintain proper Flutter pubspec format
        lines = []

        # Name and description first
        if "name" in pubspec:
            lines.append(f"name: {pubspec['name']}")
        if "description" in pubspec:
            lines.append(f"description: {pubspec['description']}")
        if "version" in pubspec:
            lines.append(f"version: {pubspec['version']}")
        if "publish_to" in pubspec:
            lines.append(f"publish_to: '{pubspec['publish_to']}'")

        lines.append("")

        # Environment
        if "environment" in pubspec:
            lines.append("environment:")
            env = pubspec["environment"]
            if "sdk" in env:
                lines.append(f"  sdk: '{env['sdk']}'")
            if "flutter" in env:
                lines.append(f"  flutter: '{env['flutter']}'")

        lines.append("")

        # Dependencies
        if "dependencies" in pubspec:
            lines.append("dependencies:")
            for name, version in sorted(pubspec["dependencies"].items()):
                if isinstance(version, dict):
                    lines.append(f"  {name}:")
                    for k, v in version.items():
                        lines.append(f"    {k}: {v}")
                else:
                    lines.append(f"  {name}: {version}")

        lines.append("")

        # Dev dependencies
        if "dev_dependencies" in pubspec:
            lines.append("dev_dependencies:")
            for name, version in sorted(pubspec["dev_dependencies"].items()):
                if isinstance(version, dict):
                    lines.append(f"  {name}:")
                    for k, v in version.items():
                        lines.append(f"    {k}: {v}")
                else:
                    lines.append(f"  {name}: {version}")

        lines.append("")

        # Flutter section
        if "flutter" in pubspec:
            lines.append("flutter:")
            flutter_config = pubspec["flutter"]
            if "uses-material-design" in flutter_config:
                lines.append(f"  uses-material-design: {str(flutter_config['uses-material-design']).lower()}")
            if "assets" in flutter_config:
                lines.append("  assets:")
                for asset in flutter_config["assets"]:
                    lines.append(f"    - {asset}")
            if "fonts" in flutter_config:
                lines.append("  fonts:")
                for font in flutter_config["fonts"]:
                    lines.append(f"    - family: {font.get('family', '')}")
                    if "fonts" in font:
                        lines.append("      fonts:")
                        for f in font["fonts"]:
                            lines.append(f"        - asset: {f.get('asset', '')}")

        return "\n".join(lines) + "\n"


def fix_pubspec_dependencies(
    files: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[str]]:
    """Fix pubspec.yaml in a file list.

    Args:
        files: List of {"path": "...", "content": "..."} dictionaries

    Returns:
        Tuple of (fixed_files, fixes_applied)
    """
    fixer = PubspecFixer()
    fixes = []

    # Find pubspec.yaml
    pubspec_file = None
    pubspec_index = -1
    dart_files = []

    for i, f in enumerate(files):
        if f["path"] == "pubspec.yaml":
            pubspec_file = f
            pubspec_index = i
        elif f["path"].endswith(".dart"):
            dart_files.append(f)

    if not pubspec_file:
        return files, ["No pubspec.yaml found"]

    # Fix pubspec
    result = fixer.fix(pubspec_file["content"], dart_files)

    if result.success and (result.dependencies_added or result.dev_dependencies_added):
        # Update the file list
        fixed_files = list(files)
        fixed_files[pubspec_index] = {
            "path": "pubspec.yaml",
            "content": result.fixed_content,
        }

        if result.dependencies_added:
            fixes.append(f"Added dependencies: {', '.join(result.dependencies_added)}")
        if result.dev_dependencies_added:
            fixes.append(f"Added dev_dependencies: {', '.join(result.dev_dependencies_added)}")

        return fixed_files, fixes

    return files, fixes
