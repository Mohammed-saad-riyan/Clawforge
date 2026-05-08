"""Refiner agent - handles iterative code improvements.

The RefinerAgent:
1. Takes user feedback/requests about generated code
2. Identifies which files need to change
3. Generates updated code
4. Returns a diff of changes
5. Auto-fixes validation errors from dart analyze
"""

import json
import re
from typing import Any

from clawforge.agents.base import AgentResult, BaseAgent
from clawforge.llm.client import get_llm_client


class RefinerAgent(BaseAgent):
    """Refines generated Flutter code based on user feedback.

    Uses Claude to understand user requests and generate targeted code changes.
    Also handles auto-fixing validation errors from dart analyze.
    """

    name = "refiner"
    description = "Iteratively refines Flutter code based on user feedback"

    SYSTEM_PROMPT = """You are a senior Flutter engineer helping to refine an existing app.

The user has already generated a Flutter app and wants to make changes.
You will receive:
1. The user's request for changes
2. The current project files
3. The original app specification

Your job is to:
1. Understand what the user wants to change
2. Identify which files need to be modified or created
3. Generate the updated code

## Response Format
Respond with:
1. A brief explanation of what you're changing (2-3 sentences max)
2. The modified/new files in code blocks

Use this exact format for code:
```dart:path/to/file.dart
// complete file contents
```

## Rules
- Only include files that are being changed or created
- Include the COMPLETE file contents, not just the changed parts
- Maintain existing code style and patterns
- Ensure all imports are present
- Don't break existing functionality unless explicitly asked
- If the request is unclear, make reasonable assumptions"""

    AUTO_FIX_SYSTEM_PROMPT = """You are a senior Flutter engineer fixing validation errors.

You are receiving output from `dart analyze` and `flutter pub get` that shows errors in generated code.
Your job is to fix ALL errors systematically.

## Common Error Types and Fixes

### Missing Imports
- Add the correct import statement at the top of the file
- Use package imports for your own code: `import 'package:app_name/path/to/file.dart';`

### Undefined Class/Function
- Check if the class exists in another file - add import
- If class doesn't exist, create the file with a minimal implementation
- For providers (Riverpod), ensure @riverpod annotation and part directive

### Type Errors
- Fix type mismatches in parameters/return types
- Add proper null handling (? or !)
- Ensure generic types match

### Missing Part Directive
- Add `part 'filename.g.dart';` below imports for files using code generation

### Pubspec Issues
- Ensure package names are correct
- Fix version constraints if needed

## Response Format
Respond with the modified/new files in code blocks:

```dart:path/to/file.dart
// complete file contents
```

Include ONLY files that need to be changed or created.
Include the COMPLETE file contents, not just the changed parts."""

    AUTO_FIX_PROMPT = """## Validation Errors to Fix
{error_summary}

## Current Files
{files_summary}

## App Specification
{spec_summary}

## Instructions
Fix ALL the validation errors listed above. For each error:
1. Identify the root cause
2. Determine the minimal fix
3. Generate complete updated file

If an error references a missing file/class, create it.
Ensure all imports are correct and complete."""

    REFINEMENT_PROMPT = """## User Request
{user_request}

## Current App Specification
{spec_summary}

## Current Files
{files_summary}

## Instructions
Based on the user's request, generate the necessary code changes.
Remember to include COMPLETE file contents for any file you modify."""

    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """Refine code based on user feedback or validation errors.

        Input data can contain:
        - user_request: User's refinement request
        - files: Current project files
        - spec: App specification
        - conversation_history: Previous chat messages
        - validation_errors: List of ValidationError objects (for auto-fix)
        - auto_fix_mode: Boolean to enable auto-fix mode
        """
        user_request = input_data.get("user_request", "")
        files = input_data.get("files", [])
        spec = input_data.get("spec", {})
        conversation_history = input_data.get("conversation_history", [])
        validation_errors = input_data.get("validation_errors", [])
        auto_fix_mode = input_data.get("auto_fix_mode", False)

        # Auto-fix mode: fix validation errors
        if auto_fix_mode and validation_errors:
            return await self._auto_fix(files, spec, validation_errors)

        # Normal refinement mode
        if not user_request:
            return AgentResult(
                success=False,
                output=None,
                error="No refinement request provided"
            )

        # Build context for the LLM
        spec_summary = self._summarize_spec(spec)
        files_summary = self._summarize_files(files)

        # Build prompt with conversation context
        prompt = self.REFINEMENT_PROMPT.format(
            user_request=user_request,
            spec_summary=spec_summary,
            files_summary=files_summary,
        )

        # Add conversation history if available
        if conversation_history:
            history_text = "\n\n## Previous Conversation\n"
            for msg in conversation_history[-5:]:  # Last 5 messages
                role = "User" if msg.get("role") == "user" else "Assistant"
                content = msg.get("content", "")[:500]  # Truncate long messages
                history_text += f"{role}: {content}\n"
            prompt = history_text + "\n" + prompt

        # Add validation errors context if present (but not in auto-fix mode)
        if validation_errors:
            error_context = self._format_validation_errors(validation_errors)
            prompt = f"## Current Validation Errors (FYI)\n{error_context}\n\n" + prompt

        # Use Claude for refinement
        client = get_llm_client(prefer_local=False, force_coding_model=True)

        try:
            response = await client.complete(
                prompt=prompt,
                system=self.SYSTEM_PROMPT,
                max_tokens=8000,
            )

            # Parse the response
            explanation, updated_files = self._parse_response(response.text)

            # Merge updated files with existing files
            merged_files = self._merge_files(files, updated_files)

            return AgentResult(
                success=True,
                output={
                    "explanation": explanation,
                    "updated_files": updated_files,
                    "merged_files": merged_files,
                    "files_changed": [f["path"] for f in updated_files],
                },
                cost_cents=response.cost_cents,
                tokens_used=response.tokens_used,
            )

        except Exception as e:
            return AgentResult(
                success=False,
                output=None,
                error=str(e),
            )

    async def _auto_fix(
        self,
        files: list[dict],
        spec: dict,
        validation_errors: list,
    ) -> AgentResult:
        """Auto-fix validation errors from dart analyze.

        Args:
            files: Current project files
            spec: App specification
            validation_errors: List of ValidationError objects

        Returns:
            AgentResult with fixed files
        """
        # Format errors for the prompt
        error_summary = self._format_validation_errors(validation_errors)
        spec_summary = self._summarize_spec(spec)
        files_summary = self._summarize_files_for_autofix(files, validation_errors)

        prompt = self.AUTO_FIX_PROMPT.format(
            error_summary=error_summary,
            files_summary=files_summary,
            spec_summary=spec_summary,
        )

        # Use Claude for auto-fix
        client = get_llm_client(prefer_local=False, force_coding_model=True)

        try:
            response = await client.complete(
                prompt=prompt,
                system=self.AUTO_FIX_SYSTEM_PROMPT,
                max_tokens=12000,  # More tokens for auto-fix
            )

            # Parse the response
            explanation, updated_files = self._parse_response(response.text)

            if not updated_files:
                return AgentResult(
                    success=False,
                    output=None,
                    error="Auto-fix generated no file changes",
                )

            # Merge updated files with existing files
            merged_files = self._merge_files(files, updated_files)

            # Track which errors we attempted to address
            addressed_files = set(f["path"] for f in updated_files)
            error_files = set(e.file_path for e in validation_errors if hasattr(e, 'file_path'))

            return AgentResult(
                success=True,
                output={
                    "mode": "auto_fix",
                    "explanation": explanation or f"Fixed {len(updated_files)} file(s)",
                    "updated_files": updated_files,
                    "merged_files": merged_files,
                    "files_changed": list(addressed_files),
                    "errors_addressed": len(validation_errors),
                    "error_files_fixed": list(addressed_files & error_files),
                },
                cost_cents=response.cost_cents,
                tokens_used=response.tokens_used,
            )

        except Exception as e:
            return AgentResult(
                success=False,
                output=None,
                error=f"Auto-fix failed: {str(e)}",
            )

    def _format_validation_errors(self, errors: list) -> str:
        """Format validation errors for the LLM prompt.

        Args:
            errors: List of ValidationError objects

        Returns:
            Formatted string
        """
        if not errors:
            return "No errors"

        lines = []
        # Group by file
        errors_by_file: dict[str, list] = {}

        for error in errors:
            file_path = getattr(error, 'file_path', '') or 'unknown'
            if file_path not in errors_by_file:
                errors_by_file[file_path] = []
            errors_by_file[file_path].append(error)

        for file_path, file_errors in sorted(errors_by_file.items()):
            lines.append(f"\n### {file_path}")
            for err in sorted(file_errors, key=lambda e: getattr(e, 'line', 0)):
                line = getattr(err, 'line', 0)
                col = getattr(err, 'column', 0)
                msg = getattr(err, 'message', str(err))
                severity = getattr(err, 'severity', 'error').upper()
                code = getattr(err, 'code', '')

                location = f"Line {line}" if line > 0 else ""
                if col > 0:
                    location += f":{col}"

                lines.append(f"- [{severity}] {location}: {msg}")
                if code:
                    lines.append(f"  Code: {code}")

        return "\n".join(lines)

    def _summarize_files_for_autofix(
        self,
        files: list[dict],
        errors: list,
    ) -> str:
        """Summarize files, prioritizing error-containing files.

        Args:
            files: All project files
            errors: Validation errors (to prioritize those files)

        Returns:
            Formatted summary
        """
        if not files:
            return "No files available"

        # Get files with errors
        error_files = set()
        for err in errors:
            file_path = getattr(err, 'file_path', '')
            if file_path:
                error_files.add(file_path)

        # Build summary
        lines = ["### Files with Errors (FULL CONTENT)"]

        for file in files:
            path = file["path"]
            content = file["content"]

            if path in error_files:
                lines.append(f"\n#### {path}")
                lines.append(f"```dart\n{content}\n```")

        # Add structure for other files
        other_files = [f for f in files if f["path"] not in error_files]
        if other_files:
            lines.append("\n### Other Files (for reference)")
            for f in sorted(other_files, key=lambda x: x["path"])[:20]:
                lines.append(f"- {f['path']}")

            # Include key files content
            key_patterns = ["main.dart", "pubspec.yaml", "app_router.dart"]
            for file in other_files:
                if any(p in file["path"] for p in key_patterns):
                    content = file["content"]
                    if len(content) > 1500:
                        content = content[:1500] + "\n... (truncated)"
                    lines.append(f"\n#### {file['path']}")
                    lines.append(f"```dart\n{content}\n```")

        return "\n".join(lines)

    def _summarize_spec(self, spec: dict) -> str:
        """Create a summary of the app specification."""
        if not spec:
            return "No specification available"

        summary = f"""App: {spec.get('app_name', 'Unknown')}
Description: {spec.get('description', 'N/A')}

Screens: {', '.join(s.get('name', '?') for s in spec.get('screens', []))}

Data Models: {', '.join(m.get('name', '?') for m in spec.get('data_models', []))}

Features: {spec.get('features_mvp', [])}"""

        return summary

    def _summarize_files(self, files: list[dict]) -> str:
        """Create a summary of current files.

        For efficiency, only include file paths and key files' content.
        """
        if not files:
            return "No files generated yet"

        # Group files by directory
        file_paths = sorted(f["path"] for f in files)
        summary = "### File Structure\n"
        summary += "\n".join(f"- {p}" for p in file_paths)

        # Include content of key files
        key_patterns = [
            "main.dart",
            "app_router.dart",
            "app_theme.dart",
            "pubspec.yaml",
        ]

        summary += "\n\n### Key File Contents\n"
        for file in files:
            path = file["path"]
            if any(pattern in path for pattern in key_patterns):
                content = file["content"]
                # Truncate if too long
                if len(content) > 2000:
                    content = content[:2000] + "\n... (truncated)"
                summary += f"\n#### {path}\n```dart\n{content}\n```\n"

        return summary

    def _parse_response(self, text: str) -> tuple[str, list[dict]]:
        """Parse LLM response into explanation and files."""
        # Extract explanation (text before first code block)
        code_start = text.find("```")
        if code_start > 0:
            explanation = text[:code_start].strip()
        else:
            explanation = ""

        # Extract code blocks
        pattern = r"```(?:dart|yaml|json|swift|kotlin|xml):(.+?)\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)

        files = []
        for path, content in matches:
            files.append({
                "path": path.strip(),
                "content": content.strip(),
            })

        return explanation, files

    def _merge_files(
        self,
        existing_files: list[dict],
        updated_files: list[dict]
    ) -> list[dict]:
        """Merge updated files with existing files."""
        # Create dict of existing files
        files_dict = {f["path"]: f["content"] for f in existing_files}

        # Update with new files
        for file in updated_files:
            files_dict[file["path"]] = file["content"]

        # Convert back to list
        return [
            {"path": path, "content": content}
            for path, content in files_dict.items()
        ]
