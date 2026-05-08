"""Autofixer module for ClawForge.

Inspired by v0's "LLM Suspense" pattern - fixes common Flutter/Dart issues
both during streaming and after code generation.
"""

from clawforge.autofixer.dart_fixer import (
    DartAutoFixer,
    AutoFixResult,
    fix_dart_files,
    fix_single_file,
)
from clawforge.autofixer.pubspec_fixer import (
    PubspecFixer,
    fix_pubspec_dependencies,
)
from clawforge.autofixer.import_fixer import (
    ImportFixer,
    fix_imports,
)
from clawforge.autofixer.model_fixer import (
    ModelDrivenFixer,
    fix_with_llm,
)
from clawforge.autofixer.missing_file_detector import (
    MissingFileDetector,
    MissingFileReport,
    detect_missing_files,
)

__all__ = [
    "DartAutoFixer",
    "AutoFixResult",
    "fix_dart_files",
    "fix_single_file",
    "PubspecFixer",
    "fix_pubspec_dependencies",
    "ImportFixer",
    "fix_imports",
    "ModelDrivenFixer",
    "fix_with_llm",
    "MissingFileDetector",
    "MissingFileReport",
    "detect_missing_files",
]
