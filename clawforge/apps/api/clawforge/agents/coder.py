"""Coder agent - generates Flutter/Dart code using Claude.

The CoderAgent:
1. Takes a full app specification from PlannerAgent
2. Generates complete Flutter project with platform files (android/, ios/, web/)
3. Generates all Flutter files in logical chunks
4. Uses RAG with Flutter examples for idiomatic code
5. Always uses Claude Sonnet for high-quality code generation
6. Runs autofixers to repair common issues (inspired by v0's LLM Suspense)
"""

from typing import Any
import json

from clawforge.agents.base import AgentResult, BaseAgent
from clawforge.llm.client import get_llm_client
from clawforge.rag.flutter_examples import get_flutter_examples
from clawforge.templates.scaffold import generate_scaffold_files
from clawforge.autofixer import (
    fix_dart_files,
    fix_pubspec_dependencies,
    fix_imports,
    detect_missing_files,
)


class CoderAgent(BaseAgent):
    """Generates complete Flutter/Dart applications.

    Always uses Claude Sonnet for code generation (never local LLM).
    Includes RAG with Flutter examples for better output.
    Generates code in chunks to stay within token limits.
    """

    name = "coder"
    description = "Generates production-ready Flutter/Dart code"

    SYSTEM_PROMPT = """You are a senior Flutter engineer known for writing robust, production-ready code.

## Tech Stack (ALWAYS use these)
- Riverpod 3.0 for state management (@riverpod annotation style)
- go_router for navigation
- Drift for local SQLite storage (when persistence needed)
- Dio for HTTP requests (when API calls needed)
- Material 3 design system
- very_good_cli project structure

## CRITICAL REQUIREMENTS - Every file MUST:
1. Include ALL necessary imports at the top (flutter, riverpod, models, etc.)
2. Import the correct package name (derived from pubspec.yaml name field)
3. Be syntactically complete and compilable
4. Have no TODO comments or placeholder code
5. Reference only files that exist or will be generated

## Import Rules
- Use package imports: `import 'package:app_name/features/...';`
- Never use relative imports like `import '../...'`
- Import flutter_riverpod, not riverpod directly
- Import go_router for navigation

## Code Quality
- Handle null/empty states gracefully with fallbacks
- Add proper loading states with CircularProgressIndicator
- Add error states with retry buttons
- Ensure responsive layouts using LayoutBuilder/MediaQuery
- Include Semantics widgets for accessibility
- Use const constructors where possible

Generate clean, idiomatic Dart code following official Flutter guidelines.
Output ONLY code blocks in the specified format - no explanations."""

    # Prompt for generating project structure and core files
    PROJECT_STRUCTURE_PROMPT = """Generate the Flutter project structure and core configuration files.

## App Specification
{spec_json}

## Generate these COMPLETE files:

### 1. `lib/main.dart` - App entry point
```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:{{package_name}}/app/app.dart';

void main() {{
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const ProviderScope(child: App()));
}}
```

### 2. `lib/app/app.dart` - Main App widget
- Import go_router from core/router
- Use MaterialApp.router with routerConfig

### 3. `lib/core/theme/app_theme.dart` - Material 3 theme
- Define ColorScheme based on spec colors
- Use useMaterial3: true

### 4. `lib/core/router/app_router.dart` - go_router configuration
- Define GoRouter with ALL screens from the spec
- Each screen must have a route path
- Use GoRoute with builder that returns the actual screen widget
- Import screen files using package imports

### 5. `analysis_options.yaml` - strict linting

## CRITICAL: The router MUST include routes for ALL screens in the spec:
{screens_list}

Use these Flutter patterns as reference:
{examples}

Respond with code files in this exact format:
```dart:path/to/file.dart
// file contents
```

For YAML files use:
```yaml:pubspec.yaml
# contents
```"""

    # Prompt for generating data models
    MODELS_PROMPT = """Generate Dart data models with Freezed.

## App: {app_name}

## Data Models to Generate:
{models_json}

## Requirements:
- Use freezed_annotation for immutable models
- Include fromJson/toJson for serialization
- Add copyWith method
- Use proper types (String, int, DateTime, etc.)
- Handle nullable fields correctly

Use this pattern:
```dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'model_name.freezed.dart';
part 'model_name.g.dart';

@freezed
class ModelName with _$ModelName {{
  const factory ModelName({{
    required String id,
    required String name,
    String? description,
  }}) = _ModelName;

  factory ModelName.fromJson(Map<String, dynamic> json) => _$ModelNameFromJson(json);
}}
```

Generate each model in `lib/features/[feature]/data/models/[model_name].dart`

Respond with code files in this exact format:
```dart:lib/features/shared/data/models/model_name.dart
// file contents
```"""

    # Prompt for generating providers
    PROVIDERS_PROMPT = """Generate Riverpod providers for state management.

## App: {app_name}

## Providers to Generate:
{providers_json}

## Data Models Available:
{models_json}

## Requirements:
- Use @riverpod annotation style (Riverpod 3.0)
- Include part directive for generated files
- Handle async states properly with AsyncValue
- Add error handling and loading states

Reference pattern:
{examples}

Generate each provider in `lib/features/[feature]/providers/[provider_name]_provider.dart`

Respond with code files in this exact format:
```dart:lib/features/home/providers/items_provider.dart
// file contents
```"""

    # Prompt for generating screens
    SCREENS_PROMPT = """Generate a COMPLETE, RUNNABLE Flutter screen widget.

## App: {app_name}
## Package name: {package_name}

## Screen to Generate:
{screen_json}

## Available Providers (use ref.watch to access):
{providers_json}

## Available Models (import from package:{package_name}/...):
{models_json}

## REQUIRED Structure for EVERY screen file:

```dart
// 1. ALL imports at top - DO NOT skip any
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
// Import providers and models using package imports:
// import 'package:{package_name}/features/.../providers/xxx_provider.dart';
// import 'package:{package_name}/features/.../models/xxx.dart';

// 2. Screen widget class
class XxxScreen extends ConsumerWidget {{
  const XxxScreen({{super.key}});

  @override
  Widget build(BuildContext context, WidgetRef ref) {{
    // 3. Watch providers
    final asyncData = ref.watch(someProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Screen Title'),
      ),
      body: asyncData.when(
        // 4. ALWAYS handle all three states
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('Error: $error'),
              ElevatedButton(
                onPressed: () => ref.invalidate(someProvider),
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
        data: (data) => _buildContent(context, data),
      ),
    );
  }}

  Widget _buildContent(BuildContext context, DataType data) {{
    // 5. Build actual UI with real data
  }}
}}
```

## CRITICAL CHECKLIST:
✅ All imports present (flutter, riverpod, router, models, providers)
✅ Package imports use: package:{package_name}/...
✅ ConsumerWidget or ConsumerStatefulWidget used
✅ Loading state with CircularProgressIndicator
✅ Error state with error message and retry button
✅ Data state with actual UI
✅ AppBar with title
✅ Semantics for accessibility
✅ No TODO comments or placeholder code

Reference patterns:
{examples}

Generate the screen in `lib/features/[feature]/presentation/screens/[screen_name]_screen.dart`
Also generate any reusable widgets in `lib/features/[feature]/presentation/widgets/`

Respond with code files in this exact format:
```dart:lib/features/home/presentation/screens/home_screen.dart
// COMPLETE file contents with ALL imports
```"""

    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """Generate complete Flutter application code."""
        app_name = input_data.get("app_name", "my_app")
        spec = input_data.get("spec", {})
        settings = input_data.get("settings", {})

        if not spec:
            return AgentResult(
                success=False, output=None, error="No specification provided"
            )

        all_files: list[dict[str, str]] = []
        total_cost = 0
        total_tokens = 0

        # Always use Claude for code generation
        client = get_llm_client(prefer_local=False, force_coding_model=True)

        try:
            # Step 0: Generate scaffold files (android/, ios/, web/, etc.)
            print("  🏗️ Generating project scaffold (platform files)...")
            scaffold_files = generate_scaffold_files(app_name, spec)
            # Store scaffold files - LLM-generated files will override if needed
            scaffold_dict = {f["path"]: f["content"] for f in scaffold_files}
            print(f"    Generated {len(scaffold_files)} scaffold files")

            # Step 1: Generate project structure and core files
            print("  📁 Generating project structure...")
            examples = await get_flutter_examples("theme navigation router provider")

            # Build screens list for router
            screens = spec.get("screens", [])
            screens_list = "\n".join([
                f"- {s.get('name', 'Unknown')}: /{s.get('route', s.get('name', '').lower())}"
                for s in screens
            ])

            prompt = self.PROJECT_STRUCTURE_PROMPT.format(
                spec_json=json.dumps(spec, indent=2),
                screens_list=screens_list if screens_list else "- HomeScreen: /",
                examples=examples,
            )

            response = await client.complete(
                prompt=prompt,
                system=self.SYSTEM_PROMPT,
                max_tokens=8000,
            )

            files = self._parse_code_blocks(response.text)
            all_files.extend(files)
            total_cost += response.cost_cents
            total_tokens += response.tokens_used
            print(f"    Generated {len(files)} core files")

            # Step 2: Generate data models
            if spec.get("data_models"):
                print("  📦 Generating data models...")
                prompt = self.MODELS_PROMPT.format(
                    app_name=app_name,
                    models_json=json.dumps(spec["data_models"], indent=2),
                )

                response = await client.complete(
                    prompt=prompt,
                    system=self.SYSTEM_PROMPT,
                    max_tokens=6000,
                )

                files = self._parse_code_blocks(response.text)
                all_files.extend(files)
                total_cost += response.cost_cents
                total_tokens += response.tokens_used
                print(f"    Generated {len(files)} model files")

            # Step 3: Generate providers
            if spec.get("providers"):
                print("  🔄 Generating providers...")
                examples = await get_flutter_examples("riverpod provider async state")

                prompt = self.PROVIDERS_PROMPT.format(
                    app_name=app_name,
                    providers_json=json.dumps(spec["providers"], indent=2),
                    models_json=json.dumps(spec.get("data_models", []), indent=2),
                    examples=examples,
                )

                response = await client.complete(
                    prompt=prompt,
                    system=self.SYSTEM_PROMPT,
                    max_tokens=6000,
                )

                files = self._parse_code_blocks(response.text)
                all_files.extend(files)
                total_cost += response.cost_cents
                total_tokens += response.tokens_used
                print(f"    Generated {len(files)} provider files")

            # Step 4: Generate screens (one at a time to get detail)
            if spec.get("screens"):
                print("  🖼️ Generating screens...")
                examples = await get_flutter_examples("loading error async widget")

                # Convert app_name to snake_case package name
                package_name = app_name.lower().replace(" ", "_").replace("-", "_")

                for screen in spec["screens"]:
                    print(f"    Generating {screen.get('name', 'unknown')} screen...")

                    prompt = self.SCREENS_PROMPT.format(
                        app_name=app_name,
                        package_name=package_name,
                        screen_json=json.dumps(screen, indent=2),
                        providers_json=json.dumps(spec.get("providers", []), indent=2),
                        models_json=json.dumps(spec.get("data_models", []), indent=2),
                        examples=examples,
                    )

                    response = await client.complete(
                        prompt=prompt,
                        system=self.SYSTEM_PROMPT,
                        max_tokens=6000,
                    )

                    files = self._parse_code_blocks(response.text)
                    all_files.extend(files)
                    total_cost += response.cost_cents
                    total_tokens += response.tokens_used

                print(f"    Generated {len(spec['screens'])} screens")

            # Step 5: Add build runner script
            all_files.append({
                "path": "build.sh",
                "content": self._generate_build_script(app_name),
            })

            # Step 6: Add README
            all_files.append({
                "path": "README.md",
                "content": self._generate_readme(app_name, spec),
            })

            # Step 7: Merge scaffold files with LLM-generated files
            # LLM files take priority (override scaffold for conflicts like pubspec.yaml)
            print("  🔗 Merging scaffold with generated code...")
            llm_dict = {f["path"]: f["content"] for f in all_files}

            # Start with scaffold, then override with LLM
            merged_dict = {**scaffold_dict, **llm_dict}
            merged_files = [{"path": p, "content": c} for p, c in merged_dict.items()]

            print(f"    Merged: {len(merged_files)} files")

            # Step 8: Run autofixers (v0-inspired "LLM Suspense" pattern)
            print("  🔧 Running autofixers...")
            package_name = app_name.lower().replace(" ", "_").replace("-", "_")
            all_autofix_messages = []

            # 8.1: Fix common Dart issues (missing imports, brackets, etc.)
            merged_files, dart_fixes = fix_dart_files(merged_files, package_name)
            if dart_fixes:
                all_autofix_messages.extend(dart_fixes)
                print(f"    ✅ Dart fixer: {len(dart_fixes)} fixes")

            # 8.2: Fix pubspec.yaml dependencies
            merged_files, pubspec_fixes = fix_pubspec_dependencies(merged_files)
            if pubspec_fixes:
                all_autofix_messages.extend(pubspec_fixes)
                print(f"    ✅ Pubspec fixer: {len(pubspec_fixes)} fixes")

            # 8.3: Fix imports (relative -> package, missing imports)
            merged_files, import_fixes = fix_imports(merged_files, package_name)
            if import_fixes:
                all_autofix_messages.extend(import_fixes)
                print(f"    ✅ Import fixer: {len(import_fixes)} fixes")

            if all_autofix_messages:
                print(f"    Total autofixes applied: {len(all_autofix_messages)}")
            else:
                print(f"    No autofixes needed")

            # Step 9: Detect and generate missing files
            print("  🔍 Checking for missing files...")
            missing_report = detect_missing_files(merged_files, package_name)

            missing_files_generated = []
            if missing_report.missing_files:
                print(f"    Found {len(missing_report.missing_files)} missing files")
                for missing_file in missing_report.missing_files[:10]:  # Limit to 10
                    print(f"    - {missing_file}")

                # Try to generate missing files
                generated, gen_cost, gen_tokens = await self._generate_missing_files(
                    client=client,
                    missing_files=missing_report.missing_files,
                    package_name=package_name,
                    spec=spec,
                )
                if generated:
                    merged_files.extend(generated)
                    missing_files_generated = [f["path"] for f in generated]
                    total_cost += gen_cost
                    total_tokens += gen_tokens
                    print(f"    ✅ Generated {len(generated)} missing files")
            else:
                print(f"    No missing files detected")

            print(f"    Final project: {len(merged_files)} files")
            print(f"    - Scaffold files: {len(scaffold_files)}")
            print(f"    - LLM-generated files: {len(all_files)}")
            print(f"    - Platform files included: android/, web/")

            return AgentResult(
                success=True,
                output={
                    "files": merged_files,
                    "file_count": len(merged_files),
                    "scaffold_count": len(scaffold_files),
                    "llm_generated_count": len(all_files),
                    "screens_count": len(spec.get("screens", [])),
                    "models_count": len(spec.get("data_models", [])),
                    "providers_count": len(spec.get("providers", [])),
                    "autofixes_applied": all_autofix_messages,
                    "autofix_count": len(all_autofix_messages),
                    "missing_files_detected": missing_report.missing_files,
                    "missing_files_generated": missing_files_generated,
                },
                cost_cents=total_cost,
                tokens_used=total_tokens,
            )

        except Exception as e:
            # Even on error, return scaffold + any partial LLM files with autofixes
            llm_dict = {f["path"]: f["content"] for f in all_files}
            merged_dict = {**scaffold_dict, **llm_dict}
            merged_files = [{"path": p, "content": c} for p, c in merged_dict.items()]

            # Try to run autofixers even on error (best effort)
            try:
                package_name = app_name.lower().replace(" ", "_").replace("-", "_")
                merged_files, _ = fix_dart_files(merged_files, package_name)
                merged_files, _ = fix_pubspec_dependencies(merged_files)
                merged_files, _ = fix_imports(merged_files, package_name)
            except Exception:
                pass  # Ignore autofix errors on already-failed generation

            return AgentResult(
                success=False,
                output={"files": merged_files},  # Return scaffold + partial files + autofixes
                error=str(e),
                cost_cents=total_cost,
                tokens_used=total_tokens,
            )

    # Prompt for generating missing files
    MISSING_FILES_PROMPT = """Generate the following missing Flutter files.

## Package name: {package_name}

## Missing files to generate:
{missing_files_list}

## App context:
- App name: {app_name}
- Features: {features}

## Requirements:
- Each file must be COMPLETE and RUNNABLE
- Include ALL necessary imports using package:{package_name}/...
- Use Riverpod 3.0 for state management (@riverpod annotation)
- Use proper Flutter patterns
- NO placeholder code or TODOs

Generate each missing file with proper structure based on its type:
- Providers: Use @riverpod annotation, include part directive
- Widgets: Use StatelessWidget or ConsumerWidget
- Screens: Use ConsumerWidget with Scaffold
- Models: Use @freezed annotation

Respond with code files in this exact format:
```dart:path/to/file.dart
// COMPLETE file contents with ALL imports
```"""

    async def _generate_missing_files(
        self,
        client: Any,
        missing_files: list[str],
        package_name: str,
        spec: dict,
    ) -> tuple[list[dict[str, str]], int, int]:
        """Generate missing files detected by the validator.

        Args:
            client: LLM client
            missing_files: List of missing file paths
            package_name: The package name
            spec: App specification

        Returns:
            Tuple of (generated_files, cost_cents, tokens_used)
        """
        if not missing_files:
            return [], 0, 0

        # Format missing files for the prompt
        missing_files_list = "\n".join(f"- {f}" for f in missing_files[:10])

        prompt = self.MISSING_FILES_PROMPT.format(
            package_name=package_name,
            missing_files_list=missing_files_list,
            app_name=spec.get("display_name", "My App"),
            features=", ".join(spec.get("features_mvp", [])[:5]),
        )

        try:
            response = await client.complete(
                prompt=prompt,
                system=self.SYSTEM_PROMPT,
                max_tokens=6000,
            )

            files = self._parse_code_blocks(response.text)
            return files, response.cost_cents, response.tokens_used

        except Exception as e:
            print(f"    ⚠️ Failed to generate missing files: {e}")
            return [], 0, 0

    def _parse_code_blocks(self, text: str) -> list[dict[str, str]]:
        """Parse code blocks from LLM response."""
        import re

        # Match both dart and yaml code blocks
        pattern = r"```(?:dart|yaml):(.+?)\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)

        files = []
        for path, content in matches:
            files.append({
                "path": path.strip(),
                "content": content.strip(),
            })

        return files

    def _generate_build_script(self, app_name: str) -> str:
        """Generate shell script for building the project."""
        return f'''#!/bin/bash
# Build script for {app_name}
# Run this after cloning to generate code and build

set -e

echo "📦 Getting dependencies..."
flutter pub get

echo "🔨 Running build_runner..."
dart run build_runner build --delete-conflicting-outputs

echo "✅ Build complete! Run with: flutter run"
'''

    def _generate_readme(self, app_name: str, spec: dict) -> str:
        """Generate README for the project."""
        display_name = spec.get("display_name", app_name)
        description = spec.get("description", "A Flutter application")
        features = spec.get("features_mvp", [])

        features_list = "\n".join(f"- {f}" for f in features) if features else "- Core functionality"

        return f'''# {display_name}

{description}

## Features

{features_list}

## Getting Started

1. Ensure Flutter is installed: `flutter doctor`
2. Get dependencies: `flutter pub get`
3. Generate code: `dart run build_runner build --delete-conflicting-outputs`
4. Run the app: `flutter run`

## Architecture

This app uses:
- **Riverpod 3.0** for state management
- **go_router** for navigation
- **Drift** for local storage
- **Material 3** design system

## Project Structure

```
lib/
├── app/              # App widget and configuration
├── core/
│   ├── router/       # Navigation configuration
│   └── theme/        # App theming
└── features/
    └── [feature]/
        ├── data/
        │   └── models/
        ├── providers/
        └── presentation/
            ├── screens/
            └── widgets/
```

---
*Generated by ClawForge AI*
'''
