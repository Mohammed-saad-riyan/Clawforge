"""Deterministic Dart code fixer.

Fixes common Dart/Flutter issues that don't require LLM:
- Missing common imports (material, riverpod, go_router)
- Incomplete class definitions
- Missing semicolons
- Bracket mismatches
"""

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AutoFixResult:
    """Result of auto-fixing code."""

    original_content: str
    fixed_content: str
    fixes_applied: list[str] = field(default_factory=list)
    success: bool = True
    errors: list[str] = field(default_factory=list)


# Common Flutter/Dart imports that are often missing
COMMON_IMPORTS = {
    # Widget indicators
    "StatelessWidget": "import 'package:flutter/material.dart';",
    "StatefulWidget": "import 'package:flutter/material.dart';",
    "Widget": "import 'package:flutter/material.dart';",
    "BuildContext": "import 'package:flutter/material.dart';",
    "Scaffold": "import 'package:flutter/material.dart';",
    "AppBar": "import 'package:flutter/material.dart';",
    "MaterialApp": "import 'package:flutter/material.dart';",
    "Text": "import 'package:flutter/material.dart';",
    "Container": "import 'package:flutter/material.dart';",
    "Column": "import 'package:flutter/material.dart';",
    "Row": "import 'package:flutter/material.dart';",
    "Center": "import 'package:flutter/material.dart';",
    "Padding": "import 'package:flutter/material.dart';",
    "SizedBox": "import 'package:flutter/material.dart';",
    "ListView": "import 'package:flutter/material.dart';",
    "CircularProgressIndicator": "import 'package:flutter/material.dart';",
    "ElevatedButton": "import 'package:flutter/material.dart';",
    "TextButton": "import 'package:flutter/material.dart';",
    "IconButton": "import 'package:flutter/material.dart';",
    "TextField": "import 'package:flutter/material.dart';",
    "Card": "import 'package:flutter/material.dart';",
    "Icon": "import 'package:flutter/material.dart';",
    "Icons": "import 'package:flutter/material.dart';",
    "Colors": "import 'package:flutter/material.dart';",
    "Theme": "import 'package:flutter/material.dart';",
    "ThemeData": "import 'package:flutter/material.dart';",
    "ColorScheme": "import 'package:flutter/material.dart';",
    "EdgeInsets": "import 'package:flutter/material.dart';",
    "TextStyle": "import 'package:flutter/material.dart';",
    "FontWeight": "import 'package:flutter/material.dart';",

    # Riverpod
    "ConsumerWidget": "import 'package:flutter_riverpod/flutter_riverpod.dart';",
    "ConsumerStatefulWidget": "import 'package:flutter_riverpod/flutter_riverpod.dart';",
    "WidgetRef": "import 'package:flutter_riverpod/flutter_riverpod.dart';",
    "ProviderScope": "import 'package:flutter_riverpod/flutter_riverpod.dart';",
    "Provider": "import 'package:flutter_riverpod/flutter_riverpod.dart';",
    "StateProvider": "import 'package:flutter_riverpod/flutter_riverpod.dart';",
    "FutureProvider": "import 'package:flutter_riverpod/flutter_riverpod.dart';",
    "StreamProvider": "import 'package:flutter_riverpod/flutter_riverpod.dart';",
    "NotifierProvider": "import 'package:flutter_riverpod/flutter_riverpod.dart';",
    "AsyncNotifierProvider": "import 'package:flutter_riverpod/flutter_riverpod.dart';",
    "AsyncValue": "import 'package:flutter_riverpod/flutter_riverpod.dart';",
    "@riverpod": "import 'package:riverpod_annotation/riverpod_annotation.dart';",

    # GoRouter
    "GoRouter": "import 'package:go_router/go_router.dart';",
    "GoRoute": "import 'package:go_router/go_router.dart';",
    "GoRouterState": "import 'package:go_router/go_router.dart';",
    "context.go": "import 'package:go_router/go_router.dart';",
    "context.push": "import 'package:go_router/go_router.dart';",
    "context.pop": "import 'package:go_router/go_router.dart';",

    # Freezed
    "@freezed": "import 'package:freezed_annotation/freezed_annotation.dart';",
    "@Freezed": "import 'package:freezed_annotation/freezed_annotation.dart';",

    # JSON serialization
    "@JsonSerializable": "import 'package:json_annotation/json_annotation.dart';",
    "fromJson": "import 'package:json_annotation/json_annotation.dart';",

    # Dio
    "Dio": "import 'package:dio/dio.dart';",
    "Response": "import 'package:dio/dio.dart';",
    "DioException": "import 'package:dio/dio.dart';",
}


class DartAutoFixer:
    """Deterministic fixer for Dart code issues."""

    def __init__(self, package_name: str = "my_app"):
        self.package_name = package_name

    def fix(self, content: str, file_path: str = "") -> AutoFixResult:
        """Apply all deterministic fixes to Dart code.

        Args:
            content: The Dart source code
            file_path: Path of the file (for context)

        Returns:
            AutoFixResult with fixed content and applied fixes
        """
        fixes_applied = []
        errors = []
        fixed_content = content

        # 1. Fix missing common imports
        fixed_content, import_fixes = self._fix_missing_imports(fixed_content, file_path)
        fixes_applied.extend(import_fixes)

        # 2. Fix relative imports to package imports
        fixed_content, rel_fixes = self._fix_relative_imports(fixed_content)
        fixes_applied.extend(rel_fixes)

        # 3. Fix missing part directives for generated files
        fixed_content, part_fixes = self._fix_part_directives(fixed_content, file_path)
        fixes_applied.extend(part_fixes)

        # 4. Fix common syntax issues
        fixed_content, syntax_fixes = self._fix_common_syntax(fixed_content)
        fixes_applied.extend(syntax_fixes)

        # 5. Fix bracket/brace mismatches
        fixed_content, bracket_fixes = self._fix_brackets(fixed_content)
        fixes_applied.extend(bracket_fixes)

        # 6. Deduplicate imports
        fixed_content, dedup_fixes = self._deduplicate_imports(fixed_content)
        fixes_applied.extend(dedup_fixes)

        return AutoFixResult(
            original_content=content,
            fixed_content=fixed_content,
            fixes_applied=fixes_applied,
            success=len(errors) == 0,
            errors=errors,
        )

    def _fix_missing_imports(self, content: str, file_path: str) -> tuple[str, list[str]]:
        """Add missing common imports based on code usage."""
        fixes = []
        existing_imports = set(re.findall(r"import\s+'[^']+';", content))

        imports_to_add = set()

        for keyword, import_stmt in COMMON_IMPORTS.items():
            # Check if keyword is used in code
            if keyword in content:
                # Check if import already exists
                import_already_exists = any(
                    import_stmt.replace("import '", "").replace("';", "") in imp
                    for imp in existing_imports
                )

                if not import_already_exists:
                    imports_to_add.add(import_stmt)

        if imports_to_add:
            # Find where to insert imports (after existing imports or at start)
            import_section_match = re.search(r"((?:import\s+'[^']+';?\n?)+)", content)

            if import_section_match:
                # Insert after existing imports
                import_section_end = import_section_match.end()
                new_imports = "\n".join(sorted(imports_to_add)) + "\n"
                content = content[:import_section_end] + new_imports + content[import_section_end:]
            else:
                # Insert at the beginning (after any library directive)
                library_match = re.match(r"(library\s+[^;]+;\n*)?", content)
                insert_pos = library_match.end() if library_match else 0
                new_imports = "\n".join(sorted(imports_to_add)) + "\n\n"
                content = content[:insert_pos] + new_imports + content[insert_pos:]

            fixes.append(f"Added {len(imports_to_add)} missing import(s)")

        return content, fixes

    def _fix_relative_imports(self, content: str) -> tuple[str, list[str]]:
        """Convert relative imports to package imports."""
        fixes = []

        # Pattern for relative imports: import '../...'
        relative_pattern = r"import\s+'(\.\.?/[^']+)';"
        matches = re.findall(relative_pattern, content)

        for rel_path in matches:
            # Convert to package import
            # This is a simplified conversion - real implementation would need file system context
            if rel_path.startswith("../"):
                # Count the number of ../
                depth = rel_path.count("../")
                remaining_path = rel_path.replace("../", "")

                # Convert to package import
                package_import = f"import 'package:{self.package_name}/{remaining_path}';"
                old_import = f"import '{rel_path}';"

                content = content.replace(old_import, package_import)
                fixes.append(f"Converted relative import: {rel_path}")

        return content, fixes

    def _fix_part_directives(self, content: str, file_path: str) -> tuple[str, list[str]]:
        """Add missing part directives for generated code files."""
        fixes = []

        # If file uses @freezed or @riverpod, it needs part directives
        needs_freezed_part = "@freezed" in content.lower() or "@Freezed" in content
        needs_riverpod_part = "@riverpod" in content.lower() or "@Riverpod" in content

        if not file_path:
            return content, fixes

        # Extract filename without extension
        file_name = file_path.split("/")[-1].replace(".dart", "")

        if needs_freezed_part:
            freezed_part = f"part '{file_name}.freezed.dart';"
            g_part = f"part '{file_name}.g.dart';"

            if freezed_part not in content:
                # Insert after imports
                content = self._insert_after_imports(content, freezed_part)
                fixes.append(f"Added part directive: {freezed_part}")

            if g_part not in content:
                content = self._insert_after_imports(content, g_part)
                fixes.append(f"Added part directive: {g_part}")

        elif needs_riverpod_part:
            g_part = f"part '{file_name}.g.dart';"

            if g_part not in content:
                content = self._insert_after_imports(content, g_part)
                fixes.append(f"Added part directive: {g_part}")

        return content, fixes

    def _fix_common_syntax(self, content: str) -> tuple[str, list[str]]:
        """Fix common syntax issues."""
        fixes = []

        # Fix missing semicolons at end of statements (simple cases)
        # This is tricky - only fix obvious cases

        # Fix double semicolons
        if ";;" in content:
            content = content.replace(";;", ";")
            fixes.append("Removed double semicolons")

        # Fix missing commas in lists/constructors (trailing comma style)
        # Pattern: ) followed by newline and ) without comma
        content = re.sub(r"(\))\n(\s*\))", r"),\n\2", content)

        return content, fixes

    def _fix_brackets(self, content: str) -> tuple[str, list[str]]:
        """Fix bracket/brace mismatches."""
        fixes = []

        # Count brackets
        open_parens = content.count("(")
        close_parens = content.count(")")
        open_braces = content.count("{")
        close_braces = content.count("}")
        open_brackets = content.count("[")
        close_brackets = content.count("]")

        # Add missing closing brackets at end of file
        if open_parens > close_parens:
            diff = open_parens - close_parens
            content = content.rstrip() + ")" * diff + "\n"
            fixes.append(f"Added {diff} missing closing parenthesis")

        if open_braces > close_braces:
            diff = open_braces - close_braces
            content = content.rstrip() + "}" * diff + "\n"
            fixes.append(f"Added {diff} missing closing brace")

        if open_brackets > close_brackets:
            diff = open_brackets - close_brackets
            content = content.rstrip() + "]" * diff + "\n"
            fixes.append(f"Added {diff} missing closing bracket")

        return content, fixes

    def _deduplicate_imports(self, content: str) -> tuple[str, list[str]]:
        """Remove duplicate imports."""
        fixes = []
        lines = content.split("\n")
        seen_imports = set()
        new_lines = []
        duplicates_removed = 0

        for line in lines:
            if line.strip().startswith("import "):
                if line.strip() in seen_imports:
                    duplicates_removed += 1
                    continue
                seen_imports.add(line.strip())
            new_lines.append(line)

        if duplicates_removed > 0:
            fixes.append(f"Removed {duplicates_removed} duplicate import(s)")

        return "\n".join(new_lines), fixes

    def _insert_after_imports(self, content: str, line_to_insert: str) -> str:
        """Insert a line after the import section."""
        # Find the last import statement
        import_matches = list(re.finditer(r"import\s+'[^']+';", content))

        if import_matches:
            last_import_end = import_matches[-1].end()
            return content[:last_import_end] + "\n" + line_to_insert + content[last_import_end:]
        else:
            # No imports, insert at beginning
            return line_to_insert + "\n" + content


def fix_dart_files(
    files: list[dict[str, str]],
    package_name: str = "my_app",
) -> tuple[list[dict[str, str]], list[str]]:
    """Fix all Dart files in a list.

    Args:
        files: List of {"path": "...", "content": "..."} dictionaries
        package_name: The package name for import fixes

    Returns:
        Tuple of (fixed_files, all_fixes_applied)
    """
    fixer = DartAutoFixer(package_name=package_name)
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
            # Non-Dart file, keep as is
            fixed_files.append(file_info)

    return fixed_files, all_fixes


def fix_single_file(content: str, file_path: str = "", package_name: str = "my_app") -> AutoFixResult:
    """Fix a single Dart file.

    Args:
        content: Dart source code
        file_path: Path of the file
        package_name: Package name for imports

    Returns:
        AutoFixResult with fixed content
    """
    fixer = DartAutoFixer(package_name=package_name)
    return fixer.fix(content, file_path)
