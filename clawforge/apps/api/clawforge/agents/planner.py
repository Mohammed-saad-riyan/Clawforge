"""Planner agent - Gathers and structures requirements into a full specification.

The PlannerAgent:
1. Takes user inputs (app idea, users, features, UI style)
2. Consolidates them into a structured specification
3. Creates screen layouts, navigation flows, and data models
4. Uses local LLM (Ollama) when available for cost efficiency
"""

from typing import Any
import json

from clawforge.agents.base import AgentResult, BaseAgent
from clawforge.llm.client import get_llm_client


class PlannerAgent(BaseAgent):
    """Creates comprehensive app specifications from user inputs."""

    name = "planner"
    description = "Consolidates user inputs into detailed app specifications"

    SYSTEM_PROMPT = """You are a senior mobile app architect specializing in Flutter applications.
Your role is to transform vague app ideas into detailed, actionable specifications.

You always:
- Think about user experience first
- Consider edge cases and error states
- Design for scalability
- Follow Flutter/Material Design best practices

Output valid JSON only. No markdown, no explanations outside JSON."""

    FINALIZE_SPEC_PROMPT = """Create a comprehensive Flutter app specification from these inputs:

## App Idea
{app_idea}

## Target Users
{target_users}

## Features
{features}

## UI Style
{ui_style}

## Architecture Preferences
- State Management: {state_management}
- Navigation: {navigation}
- Database: {database}

## App Name
{app_name}

---

Generate a detailed JSON specification with this exact structure:

{{
    "app_name": "snake_case_name",
    "display_name": "Display Name",
    "description": "One paragraph description",
    "screens": [
        {{
            "name": "screen_name",
            "route": "/route",
            "purpose": "What this screen does",
            "components": ["widget1", "widget2"],
            "state": ["stateVar1", "stateVar2"]
        }}
    ],
    "navigation": {{
        "type": "bottom_nav | drawer | tabs",
        "routes": ["/home", "/settings"]
    }},
    "data_models": [
        {{
            "name": "ModelName",
            "fields": [
                {{"name": "fieldName", "type": "String", "nullable": false}}
            ]
        }}
    ],
    "providers": [
        {{
            "name": "providerName",
            "type": "StateNotifier | AsyncNotifier | FutureProvider",
            "purpose": "What it manages"
        }}
    ],
    "theme": {{
        "primary_color": "#hex",
        "secondary_color": "#hex",
        "style": "material3",
        "brightness": "light | dark | system"
    }},
    "features_mvp": ["feature1", "feature2"],
    "features_future": ["feature3"]
}}

Return ONLY the JSON, no other text."""

    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """Execute planning task."""
        action = input_data.get("action", "")

        if action == "finalize_spec":
            return await self._finalize_spec(input_data)
        elif action == "validate_input":
            return await self._validate_input(input_data)
        else:
            return AgentResult(
                success=False,
                output=None,
                error=f"Unknown action: {action}"
            )

    async def _finalize_spec(self, input_data: dict[str, Any]) -> AgentResult:
        """Consolidate all inputs into a comprehensive specification."""
        basic = input_data.get("basic", {})
        advanced = input_data.get("advanced", {})
        app_name = input_data.get("app_name", "My App")

        # Get LLM client (prefer local for cost efficiency)
        client = get_llm_client(prefer_local=True)

        try:
            prompt = self.FINALIZE_SPEC_PROMPT.format(
                app_idea=basic.get("app_idea", ""),
                target_users=basic.get("target_users", ""),
                features=basic.get("features", ""),
                ui_style=basic.get("ui_design", "Modern"),
                state_management=advanced.get("architecture", {}).get("state", "riverpod"),
                navigation=advanced.get("architecture", {}).get("nav", "go_router"),
                database=advanced.get("architecture", {}).get("db", "drift"),
                app_name=app_name,
            )

            response = await client.complete(
                prompt=prompt,
                system=self.SYSTEM_PROMPT,
                max_tokens=4000,
            )

            # Parse JSON response
            spec = self._parse_json_response(response.text)

            if spec:
                return AgentResult(
                    success=True,
                    output=spec,
                    cost_cents=response.cost_cents,
                    tokens_used=response.tokens_used,
                )
            else:
                # Return a default spec if parsing fails
                return AgentResult(
                    success=True,
                    output=self._create_default_spec(app_name, basic),
                    cost_cents=response.cost_cents,
                    tokens_used=response.tokens_used,
                )

        except Exception as e:
            # Return default spec on error
            return AgentResult(
                success=True,
                output=self._create_default_spec(app_name, basic),
                error=f"Using default spec due to: {str(e)}",
                cost_cents=0,
                tokens_used=0,
            )

    async def _validate_input(self, input_data: dict[str, Any]) -> AgentResult:
        """Validate a single node input."""
        node = input_data.get("node", "")
        user_input = input_data.get("input", "")

        # Simple validation - ensure input is not empty
        if not user_input or len(user_input.strip()) < 3:
            return AgentResult(
                success=False,
                output=None,
                error="Input is too short. Please provide more detail."
            )

        return AgentResult(
            success=True,
            output={"validated": True, "input": user_input},
            cost_cents=0,
            tokens_used=0,
        )

    def _parse_json_response(self, text: str) -> dict | None:
        """Parse JSON from LLM response."""
        # Try to extract JSON from the response
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
            # Try to find JSON in the text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            return None

    def _create_default_spec(self, app_name: str, basic: dict) -> dict:
        """Create a default specification when LLM fails."""
        snake_name = app_name.lower().replace(" ", "_").replace("-", "_")

        return {
            "app_name": snake_name,
            "display_name": app_name,
            "description": basic.get("app_idea", "A Flutter application")[:200],
            "screens": [
                {
                    "name": "home",
                    "route": "/",
                    "purpose": "Main screen of the app",
                    "components": ["AppBar", "ListView", "FloatingActionButton"],
                    "state": ["items"]
                },
                {
                    "name": "settings",
                    "route": "/settings",
                    "purpose": "App settings",
                    "components": ["AppBar", "SwitchListTile", "ListTile"],
                    "state": ["theme", "notifications"]
                },
            ],
            "navigation": {
                "type": "bottom_nav",
                "routes": ["/", "/settings"]
            },
            "data_models": [
                {
                    "name": "Item",
                    "fields": [
                        {"name": "id", "type": "int", "nullable": False},
                        {"name": "title", "type": "String", "nullable": False},
                        {"name": "description", "type": "String", "nullable": True},
                        {"name": "createdAt", "type": "DateTime", "nullable": False},
                    ]
                }
            ],
            "providers": [
                {
                    "name": "itemsProvider",
                    "type": "AsyncNotifier",
                    "purpose": "Manages the list of items"
                },
                {
                    "name": "settingsProvider",
                    "type": "StateNotifier",
                    "purpose": "Manages app settings"
                }
            ],
            "theme": {
                "primary_color": "#6750A4",
                "secondary_color": "#625B71",
                "style": "material3",
                "brightness": "system"
            },
            "features_mvp": basic.get("features", "Basic functionality").split("\n")[:5],
            "features_future": []
        }
