"""Import fixer for Flutter/Dart code.

Resolves and fixes import statements:
- Converts relative imports to package imports
- Fixes incorrect package paths
- Resolves cross-file references
"""

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ImportFixResult:
    """Result of import fixing."""

    original_content: str
    fixed_content: str
    fixes_applied: list[str] = field(default_factory=list)


class ImportFixer:
    """Fixes import statements in Dart files."""

    def __init__(self, package_name: str, all_files: list[dict[str, str]]):
        """Initialize the import fixer.

        Args:
            package_name: The package name from pubspec.yaml
            all_files: List of all files in the project for reference resolution
        """
        self.package_name = package_name

        # Build a map of class names to file paths
        self.class_to_file: dict[str, str] = {}
        self._build_class_map(all_files)

    def _build_class_map(self, files: list[dict[str, str]]) -> None:
        """Build a map of class/function names to their file paths."""
        for file_info in files:
            path = file_info["path"]
            content = file_info.get("content", "")

            if not path.endswith(".dart"):
                continue

            # Find class definitions
            class_pattern = r"class\s+(\w+)"
            classes = re.findall(class_pattern, content)
            for cls in classes:
                self.class_to_file[cls] = path

            # Find enum definitions
            enum_pattern = r"enum\s+(\w+)"
            enums = re.findall(enum_pattern, content)
            for enum in enums:
                self.class_to_file[enum] = path

            # Find top-level function definitions
            func_pattern = r"^(\w+)\s+(\w+)\s*\([^)]*\)\s*(?:async\s*)?(?:=>|\{)"
            funcs = re.findall(func_pattern, content, re.MULTILINE)
            for return_type, func_name in funcs:
                if func_name not in ["if", "for", "while", "switch", "catch"]:
                    self.class_to_file[func_name] = path

            # Find top-level constants/variables with @riverpod or provider
            provider_pattern = r"final\s+(\w+Provider)\s*="
            providers = re.findall(provider_pattern, content)
            for provider in providers:
                self.class_to_file[provider] = path

    def fix(self, content: str, file_path: str) -> ImportFixResult:
        """Fix imports in a Dart file.

        Args:
            content: The Dart source code
            file_path: Path of the file being fixed

        Returns:
            ImportFixResult with fixed content
        """
        fixes = []
        fixed_content = content

        # 1. Convert relative imports to package imports
        fixed_content, rel_fixes = self._fix_relative_imports(fixed_content, file_path)
        fixes.extend(rel_fixes)

        # 2. Fix incorrect package paths
        fixed_content, path_fixes = self._fix_package_paths(fixed_content)
        fixes.extend(path_fixes)

        # 3. Add missing imports for used classes
        fixed_content, missing_fixes = self._add_missing_imports(fixed_content, file_path)
        fixes.extend(missing_fixes)

        # 4. Sort and organize imports
        fixed_content, sort_fixes = self._organize_imports(fixed_content)
        fixes.extend(sort_fixes)

        return ImportFixResult(
            original_content=content,
            fixed_content=fixed_content,
            fixes_applied=fixes,
        )

    def _fix_relative_imports(self, content: str, current_file: str) -> tuple[str, list[str]]:
        """Convert relative imports to package imports."""
        fixes = []

        # Pattern for relative imports
        relative_pattern = r"import\s+'(\.\.?/[^']+)';"

        def replace_relative(match: re.Match) -> str:
            rel_path = match.group(1)

            # Calculate the absolute path from the relative import
            current_dir = "/".join(current_file.split("/")[:-1])
            if not current_dir:
                current_dir = "."

            # Resolve the relative path
            resolved = self._resolve_relative_path(current_dir, rel_path)

            # Convert to package import
            if resolved.startswith("lib/"):
                resolved = resolved[4:]  # Remove 'lib/' prefix

            package_import = f"import 'package:{self.package_name}/{resolved}';"
            fixes.append(f"Converted relative import: {rel_path}")
            return package_import

        fixed_content = re.sub(relative_pattern, replace_relative, content)
        return fixed_content, fixes

    def _resolve_relative_path(self, current_dir: str, rel_path: str) -> str:
        """Resolve a relative path from the current directory."""
        parts = current_dir.split("/")

        for segment in rel_path.split("/"):
            if segment == "..":
                if parts:
                    parts.pop()
            elif segment == ".":
                continue
            else:
                parts.append(segment)

        return "/".join(parts)

    def _fix_package_paths(self, content: str) -> tuple[str, list[str]]:
        """Fix incorrect package paths."""
        fixes = []

        # Check for wrong package name in imports
        wrong_package_pattern = rf"import\s+'package:(?!{re.escape(self.package_name)}/)([^/]+)/([^']+)';"

        # Find imports that might be internal but using wrong package name
        internal_imports = re.findall(r"import\s+'package:([^/]+)/([^']+)';", content)

        for pkg_name, path in internal_imports:
            # Check if this looks like it should be our package
            if pkg_name not in [
                "flutter", "flutter_riverpod", "go_router", "dio",
                "freezed_annotation", "json_annotation", "drift",
                "riverpod_annotation", "cached_network_image",
                # Add more known packages
            ]:
                # Check if the path exists in our file map
                full_path = f"lib/{path}"
                for cls, file_path in self.class_to_file.items():
                    if file_path == full_path or file_path.endswith(f"/{path}"):
                        old_import = f"import 'package:{pkg_name}/{path}';"
                        new_import = f"import 'package:{self.package_name}/{path}';"
                        content = content.replace(old_import, new_import)
                        fixes.append(f"Fixed package name: {pkg_name} -> {self.package_name}")
                        break

        return content, fixes

    def _add_missing_imports(self, content: str, current_file: str) -> tuple[str, list[str]]:
        """Add imports for used classes that aren't imported."""
        fixes = []

        # Get existing imports
        existing_imports = set(re.findall(r"import\s+'([^']+)';", content))

        # Find class usages in the file
        # Look for PascalCase identifiers that might be classes
        potential_classes = set(re.findall(r"\b([A-Z][a-zA-Z0-9]+)\b", content))

        # Exclude common keywords and types
        excluded = {
            "String", "int", "double", "bool", "List", "Map", "Set",
            "Future", "Stream", "Object", "Type", "Function", "Null",
            "DateTime", "Duration", "Iterable", "Iterator", "Symbol",
            "Exception", "Error", "Override", "Deprecated",
        }
        potential_classes -= excluded

        imports_to_add = []

        for cls in potential_classes:
            if cls in self.class_to_file:
                file_path = self.class_to_file[cls]

                # Don't import from self
                if file_path == current_file:
                    continue

                # Convert to import path
                if file_path.startswith("lib/"):
                    import_path = file_path[4:]
                else:
                    import_path = file_path

                full_import = f"package:{self.package_name}/{import_path}"

                # Check if already imported
                if not any(full_import in imp for imp in existing_imports):
                    import_stmt = f"import '{full_import}';"
                    if import_stmt not in imports_to_add:
                        imports_to_add.append(import_stmt)
                        fixes.append(f"Added import for {cls}")

        if imports_to_add:
            # Find where to insert imports
            import_section_match = re.search(r"((?:import\s+'[^']+';?\n?)+)", content)

            if import_section_match:
                insert_pos = import_section_match.end()
                new_imports = "\n".join(imports_to_add) + "\n"
                content = content[:insert_pos] + new_imports + content[insert_pos:]
            else:
                # Insert at beginning
                new_imports = "\n".join(imports_to_add) + "\n\n"
                content = new_imports + content

        return content, fixes

    def _organize_imports(self, content: str) -> tuple[str, list[str]]:
        """Sort and organize imports."""
        fixes = []

        # Extract all imports
        import_pattern = r"import\s+'[^']+';?"
        imports = re.findall(import_pattern, content)

        if not imports:
            return content, fixes

        # Remove imports from content temporarily
        content_without_imports = re.sub(import_pattern + r"\n?", "", content)

        # Sort imports into categories
        dart_imports = []
        flutter_imports = []
        package_imports = []
        local_imports = []

        for imp in imports:
            imp = imp.strip()
            if not imp.endswith(";"):
                imp += ";"

            if "dart:" in imp:
                dart_imports.append(imp)
            elif "package:flutter" in imp:
                flutter_imports.append(imp)
            elif f"package:{self.package_name}" in imp:
                local_imports.append(imp)
            elif "package:" in imp:
                package_imports.append(imp)
            else:
                local_imports.append(imp)

        # Sort each category
        dart_imports.sort()
        flutter_imports.sort()
        package_imports.sort()
        local_imports.sort()

        # Combine with blank lines between categories
        organized = []
        if dart_imports:
            organized.extend(dart_imports)
            organized.append("")
        if flutter_imports:
            organized.extend(flutter_imports)
            organized.append("")
        if package_imports:
            organized.extend(package_imports)
            organized.append("")
        if local_imports:
            organized.extend(local_imports)
            organized.append("")

        # Rebuild content
        import_section = "\n".join(organized)
        fixed_content = import_section + "\n" + content_without_imports.lstrip()

        if import_section != "\n".join(imports):
            fixes.append("Organized imports")

        return fixed_content, fixes


def fix_imports(
    files: list[dict[str, str]],
    package_name: str = "my_app",
) -> tuple[list[dict[str, str]], list[str]]:
    """Fix imports in all Dart files.

    Args:
        files: List of {"path": "...", "content": "..."} dictionaries
        package_name: The package name for imports

    Returns:
        Tuple of (fixed_files, all_fixes_applied)
    """
    fixer = ImportFixer(package_name=package_name, all_files=files)
    fixed_files = []
    all_fixes = []

    for file_info in files:
        path = file_info["path"]
        content = file_info["content"]

        if path.endswith(".dart"):
            result = fixer.fix(content, path)
            fixed_files.append({
                "path": path,
                "content": result.fixed_content,
            })

            if result.fixes_applied:
                all_fixes.extend([f"{path}: {fix}" for fix in result.fixes_applied])
        else:
            fixed_files.append(file_info)

    return fixed_files, all_fixes
