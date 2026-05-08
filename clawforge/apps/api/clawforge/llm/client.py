"""Unified LLM client with support for Ollama and Claude."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx
from anthropic import AsyncAnthropic

from clawforge.config import get_settings


@dataclass
class LLMResponse:
    """Response from LLM completion."""

    text: str
    cost_cents: int
    tokens_used: int
    model: str


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Generate a completion."""
        pass


class OllamaClient(BaseLLMClient):
    """Client for Ollama (local LLM)."""

    def __init__(self, model: str, base_url: str) -> None:
        self.model = model
        self.base_url = base_url

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Generate completion using Ollama."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {"num_predict": max_tokens},
                },
            )
            response.raise_for_status()
            data = response.json()

            return LLMResponse(
                text=data["message"]["content"],
                cost_cents=0,  # Local LLM is free
                tokens_used=data.get("eval_count", 0),
                model=self.model,
            )


class ClaudeClient(BaseLLMClient):
    """Client for Claude API."""

    # Pricing per million tokens (April 2026)
    PRICING = {
        "claude-3-5-haiku-latest": {"input": 0.25, "output": 1.25},
        "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
        "claude-opus-4-5-20251101": {"input": 15.0, "output": 75.0},
    }

    def __init__(self, model: str) -> None:
        settings = get_settings()
        self.model = model
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Generate completion using Claude."""
        kwargs: dict = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }

        if system:
            kwargs["system"] = system

        response = await self.client.messages.create(**kwargs)

        # Calculate cost
        pricing = self.PRICING.get(
            self.model, {"input": 3.0, "output": 15.0}
        )
        input_cost = (response.usage.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (response.usage.output_tokens / 1_000_000) * pricing["output"]
        total_cost_cents = int((input_cost + output_cost) * 100)

        return LLMResponse(
            text=response.content[0].text,
            cost_cents=total_cost_cents,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            model=self.model,
        )


def get_llm_client(
    prefer_local: bool = True,
    force_coding_model: bool = False,
) -> BaseLLMClient:
    """Get appropriate LLM client based on settings and preference.

    Args:
        prefer_local: Try to use local Ollama if available
        force_coding_model: Use Claude for code generation (Sonnet or Opus)

    Returns:
        LLM client instance
    """
    settings = get_settings()

    # Force coding model = use Claude Sonnet or Opus
    if force_coding_model:
        if settings.use_opus_for_coding:
            return ClaudeClient(model="claude-opus-4-5-20251101")
        return ClaudeClient(model=settings.claude_model_coding)

    # Try local LLM if preferred and enabled
    if prefer_local and settings.use_local_llm:
        return OllamaClient(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
        )

    # Fall back to Claude Haiku for routing/simple tasks
    return ClaudeClient(model=settings.claude_model_routing)
