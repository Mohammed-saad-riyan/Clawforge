"""Model-driven fixer for complex errors.

Uses a small, fast LLM to fix errors that can't be handled deterministically.
Inspired by v0's autofixer that uses a fine-tuned model for complex repairs.
"""

import re
from dataclasses import dataclass, field
from typing import Any

from clawforge.llm.client import get_llm_client


@dataclass
class ModelFixResult:
    """Result of model-driven fixing."""

    success: bool
    fixed_files: list[dict[str, str]] = field(default_factory=list)
    fixes_applied: list[str] = field(default_factory=list)
    cost_cents: int = 0
    tokens_used: int = 0
    errors: list[str] = field(default_factory=list)


class ModelDrivenFixer:
    """Uses LLM to fix complex errors that can't be handled deterministically."""

    SYSTEM_PROMPT = """You are a Flutter/Dart code repair expert. Your job is to fix errors in generated code.

Rules:
1. Only fix the specific error(s) mentioned
2. Make minimal changes to fix the issue
3. Keep the existing code style and structure
4. Output ONLY the fixed code, no explanations
5. If you can't fix an error, return the original code unchanged

Common fixes you should handle:
- Missing imports
- Type mismatches
- Missing required parameters
- Incorrect constructor calls
- Missing method implementations
- Async/await issues
- Null safety issues"""

    FIX_PROMPT = """Fix the following error(s) in this Dart file.

## File: {file_path}

## Error(s) to fix:
{errors}

## Current code:
```dart
{code}
```

## Available context (other files in project):
{context}

Output ONLY the complete fixed Dart code. No explanations, no markdown formatting."""

    def __init__(self, use_local_llm: bool = True):
        """Initialize the model fixer.

        Args:
            use_local_llm: Whether to use local LLM (faster/cheaper) or Claude
        """
        self.use_local_llm = use_local_llm

    async def fix(
        self,
        files: list[dict[str, str]],
        errors: list[dict[str, Any]],
        max_attempts: int = 3,
    ) -> ModelFixResult:
        """Fix errors in files using LLM.

        Args:
            files: List of {"path": "...", "content": "..."} dictionaries
            errors: List of error dictionaries with "file", "message", "line" keys
            max_attempts: Maximum number of fix attempts per file

        Returns:
            ModelFixResult with fixed files
        """
        # Group errors by file
        errors_by_file: dict[str, list[dict]] = {}
        for error in errors:
            file_path = error.get("file", "")
            if file_path:
                if file_path not in errors_by_file:
                    errors_by_file[file_path] = []
                errors_by_file[file_path].append(error)

        if not errors_by_file:
            return ModelFixResult(
                success=True,
                fixed_files=files,
                fixes_applied=[],
            )

        # Get LLM client
        client = get_llm_client(prefer_local=self.use_local_llm)

        fixed_files = list(files)
        all_fixes = []
        total_cost = 0
        total_tokens = 0
        all_errors = []

        # Build context from other files
        context = self._build_context(files)

        # Fix each file with errors
        for file_path, file_errors in errors_by_file.items():
            # Find the file in our list
            file_index = None
            file_content = None
            for i, f in enumerate(fixed_files):
                if f["path"] == file_path:
                    file_index = i
                    file_content = f["content"]
                    break

            if file_content is None:
                all_errors.append(f"File not found: {file_path}")
                continue

            # Format errors for the prompt
            error_text = "\n".join([
                f"- Line {e.get('line', '?')}: {e.get('message', 'Unknown error')}"
                for e in file_errors
            ])

            # Try to fix
            for attempt in range(max_attempts):
                prompt = self.FIX_PROMPT.format(
                    file_path=file_path,
                    errors=error_text,
                    code=file_content,
                    context=context,
                )

                try:
                    response = await client.complete(
                        prompt=prompt,
                        system=self.SYSTEM_PROMPT,
                        max_tokens=4000,
                    )

                    total_cost += response.cost_cents
                    total_tokens += response.tokens_used

                    # Extract fixed code
                    fixed_code = self._extract_code(response.text)

                    if fixed_code and fixed_code != file_content:
                        # Validate the fix is reasonable (not empty, has similar structure)
                        if self._validate_fix(file_content, fixed_code):
                            fixed_files[file_index] = {
                                "path": file_path,
                                "content": fixed_code,
                            }
                            all_fixes.append(f"{file_path}: Fixed {len(file_errors)} error(s)")
                            break
                        else:
                            all_errors.append(f"{file_path}: Fix validation failed on attempt {attempt + 1}")
                    else:
                        all_errors.append(f"{file_path}: No changes produced on attempt {attempt + 1}")

                except Exception as e:
                    all_errors.append(f"{file_path}: Fix attempt {attempt + 1} failed: {str(e)}")

        return ModelFixResult(
            success=len(all_fixes) > 0 or len(all_errors) == 0,
            fixed_files=fixed_files,
            fixes_applied=all_fixes,
            cost_cents=total_cost,
            tokens_used=total_tokens,
            errors=all_errors,
        )

    def _build_context(self, files: list[dict[str, str]], max_files: int = 5) -> str:
        """Build context from other files for the LLM."""
        # Include key files for context
        priority_patterns = [
            "pubspec.yaml",
            "lib/main.dart",
            "lib/app/app.dart",
            "lib/core/router",
            "lib/core/theme",
        ]

        context_files = []
        remaining_files = []

        for f in files:
            path = f["path"]
            is_priority = any(p in path for p in priority_patterns)

            if is_priority:
                context_files.append(f)
            else:
                remaining_files.append(f)

        # Add remaining files up to max
        for f in remaining_files:
            if len(context_files) >= max_files:
                break
            if f["path"].endswith(".dart"):
                context_files.append(f)

        # Format context
        context_parts = []
        for f in context_files[:max_files]:
            content = f["content"][:1000]  # Truncate long files
            if len(f["content"]) > 1000:
                content += "\n... (truncated)"
            context_parts.append(f"### {f['path']}\n```dart\n{content}\n```")

        return "\n\n".join(context_parts)

    def _extract_code(self, response: str) -> str:
        """Extract Dart code from LLM response."""
        # Try to find code block
        code_match = re.search(r"```dart\n?(.*?)```", response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()

        # Try generic code block
        code_match = re.search(r"```\n?(.*?)```", response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()

        # Assume the whole response is code
        return response.strip()

    def _validate_fix(self, original: str, fixed: str) -> bool:
        """Validate that the fix is reasonable."""
        # Check it's not empty
        if not fixed or len(fixed) < 10:
            return False

        # Check it's not drastically different in size (2x or 0.5x)
        original_len = len(original)
        fixed_len = len(fixed)

        if fixed_len > original_len * 2 or fixed_len < original_len * 0.3:
            return False

        # Check it still looks like Dart code
        dart_indicators = ["import ", "class ", "void ", "Widget ", "return ", ";"]
        has_dart_code = any(indicator in fixed for indicator in dart_indicators)

        if not has_dart_code:
            return False

        return True


async def fix_with_llm(
    files: list[dict[str, str]],
    errors: list[dict[str, Any]],
    use_local_llm: bool = True,
) -> ModelFixResult:
    """Fix errors in files using LLM.

    This is a convenience function that creates a ModelDrivenFixer and runs it.

    Args:
        files: List of {"path": "...", "content": "..."} dictionaries
        errors: List of error dictionaries with "file", "message", "line" keys
        use_local_llm: Whether to use local LLM (faster/cheaper) or Claude

    Returns:
        ModelFixResult with fixed files
    """
    fixer = ModelDrivenFixer(use_local_llm=use_local_llm)
    return await fixer.fix(files, errors)
