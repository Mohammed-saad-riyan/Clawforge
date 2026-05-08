"""Claws agent - evaluates and improves generated code.

The ClawsAgent:
1. Evaluates all generated files for quality
2. Identifies issues and fixable problems
3. Applies fixes using Claude for complex issues
4. Returns an overall quality score
"""

from typing import Any
import json

from clawforge.agents.base import AgentResult, BaseAgent
from clawforge.llm.client import get_llm_client


class ClawsAgent(BaseAgent):
    """Evaluates code quality and applies fixes.

    The self-evolution layer that continuously improves outputs.
    Uses hybrid approach: local LLM for evaluation, Claude for fixes.
    """

    name = "claws"
    description = "Evaluates code quality and applies fixes"

    SYSTEM_PROMPT = """You are a senior Flutter code reviewer. Your job is to:
1. Identify issues in Flutter/Dart code
2. Evaluate code quality objectively
3. Suggest specific, actionable improvements

Be constructive but thorough. Focus on:
- Correctness: Does the code work?
- Dart idioms: Is it clean, idiomatic Dart?
- Flutter patterns: Does it use Riverpod/go_router correctly?
- Error handling: Are edge cases covered?
- Accessibility: Is the UI accessible?

Output valid JSON only."""

    EVALUATION_PROMPT = """Evaluate this Flutter application for quality and completeness.

## App Specification
{spec_json}

## Generated Files
{files_summary}

## Sample Code (key files)
{sample_code}

## Evaluation Criteria
Score each category (1-10):
1. **Completeness**: Are all screens and features implemented?
2. **Code Quality**: Is it clean, idiomatic Dart?
3. **Architecture**: Does it follow Riverpod/go_router best practices?
4. **Error Handling**: Are loading/error states handled?
5. **UI Polish**: Is the UI complete with proper Material 3 styling?

Respond with this exact JSON structure:
{{
    "scores": {{
        "completeness": 8,
        "code_quality": 7,
        "architecture": 8,
        "error_handling": 6,
        "ui_polish": 7
    }},
    "overall_score": 7.2,
    "passed": true,
    "issues": [
        {{"file": "lib/main.dart", "issue": "Missing error boundary", "severity": "medium", "fixable": true}},
        {{"file": "lib/features/home/screens/home_screen.dart", "issue": "No loading state", "severity": "high", "fixable": true}}
    ],
    "fixable_issues": [
        {{"file": "lib/main.dart", "issue": "Missing error boundary", "fix_hint": "Wrap MaterialApp with ErrorBoundary widget"}}
    ],
    "suggestions": [
        "Consider adding animations for better UX",
        "Add unit tests for providers"
    ]
}}"""

    FIX_PROMPT = """Fix the following issues in these Flutter files.

## Issues to Fix
{issues_json}

## Current Files
{files_json}

## Instructions
1. Fix each issue identified
2. Maintain the existing code structure
3. Only modify what's necessary to fix issues
4. Keep all imports and dependencies

Return the corrected files in this format:
```dart:path/to/file.dart
// corrected file contents
```

Only include files that were changed."""

    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """Evaluate or fix code."""
        action = input_data.get("action", "evaluate")

        try:
            if action == "evaluate":
                return await self._evaluate_files(input_data)
            elif action == "fix":
                return await self._fix_files(input_data)
            else:
                return AgentResult(
                    success=False, output=None, error=f"Unknown action: {action}"
                )
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))

    async def _evaluate_files(self, input_data: dict[str, Any]) -> AgentResult:
        """Evaluate all generated files for quality."""
        files = input_data.get("files", [])
        spec = input_data.get("spec", {})
        quality_settings = input_data.get("quality_settings", {})

        if not files:
            return AgentResult(
                success=False, output=None, error="No files to evaluate"
            )

        # Create summary of files
        files_summary = self._create_files_summary(files)

        # Get sample of key files (main.dart, router, screens)
        sample_code = self._get_sample_code(files)

        # Use local LLM for evaluation (cost efficient)
        client = get_llm_client(prefer_local=True)

        prompt = self.EVALUATION_PROMPT.format(
            spec_json=json.dumps(spec, indent=2)[:2000],  # Truncate to save tokens
            files_summary=files_summary,
            sample_code=sample_code,
        )

        response = await client.complete(
            prompt=prompt,
            system=self.SYSTEM_PROMPT,
            max_tokens=2000,
        )

        # Parse JSON response
        evaluation = self._parse_evaluation(response.text)

        # Check if quality meets threshold
        min_score = quality_settings.get("min_score", 6.0)
        evaluation["meets_threshold"] = evaluation.get("overall_score", 0) >= min_score

        return AgentResult(
            success=True,
            output={
                "score": evaluation.get("overall_score", 0),
                "scores": evaluation.get("scores", {}),
                "passed": evaluation.get("passed", False),
                "issues": evaluation.get("issues", []),
                "fixable_issues": evaluation.get("fixable_issues", []),
                "suggestions": evaluation.get("suggestions", []),
                "meets_threshold": evaluation.get("meets_threshold", False),
            },
            cost_cents=response.cost_cents,
            tokens_used=response.tokens_used,
        )

    async def _fix_files(self, input_data: dict[str, Any]) -> AgentResult:
        """Fix identified issues in files."""
        files = input_data.get("files", [])
        issues = input_data.get("issues", [])

        if not issues:
            return AgentResult(
                success=True,
                output={"files": files, "fixes_applied": 0},
                cost_cents=0,
                tokens_used=0,
            )

        # Filter to only fixable issues
        fixable = [i for i in issues if i.get("fixable", True)]

        if not fixable:
            return AgentResult(
                success=True,
                output={"files": files, "fixes_applied": 0},
                cost_cents=0,
                tokens_used=0,
            )

        # Get files that need fixing
        files_to_fix = self._get_files_to_fix(files, fixable)

        # Use Claude for fixing (needs high quality)
        client = get_llm_client(prefer_local=False, force_coding_model=True)

        prompt = self.FIX_PROMPT.format(
            issues_json=json.dumps(fixable, indent=2),
            files_json=json.dumps(files_to_fix, indent=2),
        )

        response = await client.complete(
            prompt=prompt,
            system=self.SYSTEM_PROMPT,
            max_tokens=8000,
        )

        # Parse fixed files
        fixed_files = self._parse_code_blocks(response.text)

        # Merge fixed files back into original list
        merged_files = self._merge_files(files, fixed_files)

        return AgentResult(
            success=True,
            output={
                "files": merged_files,
                "fixes_applied": len(fixed_files),
                "fixed_paths": [f["path"] for f in fixed_files],
            },
            cost_cents=response.cost_cents,
            tokens_used=response.tokens_used,
        )

    def _create_files_summary(self, files: list[dict]) -> str:
        """Create a summary of all files."""
        lines = []
        for f in files:
            path = f.get("path", "unknown")
            size = len(f.get("content", ""))
            lines.append(f"- {path} ({size} chars)")
        return "\n".join(lines)

    def _get_sample_code(self, files: list[dict], max_chars: int = 6000) -> str:
        """Get sample of key files for evaluation."""
        # Priority files to include
        priority_patterns = [
            "main.dart",
            "app.dart",
            "router",
            "_screen.dart",
            "_provider.dart",
        ]

        samples = []
        total_chars = 0

        # Sort files by priority
        def priority(f: dict) -> int:
            path = f.get("path", "").lower()
            for i, pattern in enumerate(priority_patterns):
                if pattern in path:
                    return i
            return 100

        sorted_files = sorted(files, key=priority)

        for f in sorted_files:
            content = f.get("content", "")
            path = f.get("path", "unknown")

            # Skip non-dart files for evaluation
            if not path.endswith(".dart"):
                continue

            if total_chars + len(content) > max_chars:
                # Truncate this file if needed
                remaining = max_chars - total_chars
                if remaining > 500:
                    samples.append(f"### {path}\n```dart\n{content[:remaining]}...\n```")
                break

            samples.append(f"### {path}\n```dart\n{content}\n```")
            total_chars += len(content)

        return "\n\n".join(samples)

    def _get_files_to_fix(self, files: list[dict], issues: list[dict]) -> list[dict]:
        """Get only the files that need fixing."""
        issue_files = set(i.get("file", "") for i in issues)

        return [f for f in files if f.get("path", "") in issue_files]

    def _parse_evaluation(self, text: str) -> dict:
        """Parse evaluation JSON from response."""
        text = text.strip()

        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON in text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass

            # Return default evaluation on failure
            return {
                "scores": {},
                "overall_score": 5.0,
                "passed": True,
                "issues": [],
                "fixable_issues": [],
                "suggestions": ["Could not parse evaluation - manual review recommended"],
            }

    def _parse_code_blocks(self, text: str) -> list[dict[str, str]]:
        """Parse code blocks from LLM response."""
        import re

        pattern = r"```dart:(.+?)\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)

        files = []
        for path, content in matches:
            files.append({
                "path": path.strip(),
                "content": content.strip(),
            })

        return files

    def _merge_files(
        self, original: list[dict], fixed: list[dict]
    ) -> list[dict]:
        """Merge fixed files back into original list."""
        fixed_by_path = {f["path"]: f for f in fixed}

        merged = []
        for f in original:
            path = f.get("path", "")
            if path in fixed_by_path:
                merged.append(fixed_by_path[path])
            else:
                merged.append(f)

        return merged
