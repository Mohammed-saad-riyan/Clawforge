"""Router agent - decides which agent handles each task."""

from typing import Any, Literal

from clawforge.agents.base import AgentResult, BaseAgent
from clawforge.llm.client import get_llm_client


class RouterAgent(BaseAgent):
    """Routes tasks to appropriate agents based on complexity.

    Uses local LLM (Qwen) when available, falls back to Claude Haiku.
    """

    name = "router"
    description = "Routes tasks to the appropriate specialized agent"

    ROUTING_PROMPT = """You are a task router for an AI app development system.

Given a task description, determine which agent should handle it:
- "github": Repository creation, pushing code, creating branches/PRs
- "planner": Gathering requirements, creating feature lists, UI specs
- "coder": Writing actual Flutter/Dart code (requires Claude)
- "claws": Evaluating code quality, suggesting improvements

Task: {task}

Respond with ONLY the agent name (github, planner, coder, or claws):"""

    async def execute(self, input_data: dict[str, Any]) -> AgentResult:
        """Route the task to the appropriate agent."""
        task = input_data.get("task", "")
        if not task:
            return AgentResult(success=False, output=None, error="No task provided")

        # Get LLM client (prefers local, falls back to Claude Haiku)
        client = get_llm_client(prefer_local=True)

        try:
            response = await client.complete(
                prompt=self.ROUTING_PROMPT.format(task=task),
                max_tokens=10,
            )

            route = response.text.strip().lower()
            valid_routes: list[str] = ["github", "planner", "coder", "claws"]

            if route not in valid_routes:
                # Default to planner for unclear tasks
                route = "planner"

            return AgentResult(
                success=True,
                output={"route": route, "task": task},
                cost_cents=response.cost_cents,
                tokens_used=response.tokens_used,
            )
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))
