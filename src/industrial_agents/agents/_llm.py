"""LLM provider Protocol and factory."""

from __future__ import annotations

import os
from typing import Any, Protocol, Self, runtime_checkable

import structlog

log = structlog.get_logger(__name__)


@runtime_checkable
class LLMProvider(Protocol):
    async def complete(
        self: Self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]: ...


def get_llm_provider(provider: str | None = None) -> LLMProvider:
    """Return an LLMProvider instance based on env config or explicit name."""
    resolved: str = provider or os.getenv("LLM_PROVIDER", "anthropic")
    log.debug("llm_provider_selected", provider=resolved)

    match resolved.lower():
        case "anthropic":
            from industrial_agents.agents._llm_providers.anthropic import AnthropicProvider

            return AnthropicProvider()
        case "openai":
            from industrial_agents.agents._llm_providers.openai import OpenAIProvider

            return OpenAIProvider()
        case "bedrock":
            from industrial_agents.agents._llm_providers.bedrock import BedrockProvider

            return BedrockProvider()
        case "ollama":
            from industrial_agents.agents._llm_providers.ollama import OllamaProvider

            return OllamaProvider()
        case _:
            raise ValueError(f"Unknown LLM provider: {resolved!r}")
