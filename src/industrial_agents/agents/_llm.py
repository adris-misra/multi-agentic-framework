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


class BoundModelProvider:
    """Wraps any LLMProvider and pins a default model to every complete() call.

    Fixes bug #14: the CLI's --model flag was stored in benchmark metadata but
    never forwarded to llm.complete() inside agent handle() methods, so agents
    always fell back to the provider's _DEFAULT_MODEL.  Wrap the provider with
    BoundModelProvider(llm, model) before passing to agents so the flag takes effect.
    An explicit model= override passed to complete() still wins (e.g. judge_model).
    """

    def __init__(self: Self, inner: LLMProvider, model: str) -> None:
        self._inner = inner
        self._model = model

    async def complete(
        self: Self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return await self._inner.complete(
            messages,
            model=model if model is not None else self._model,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
        )


def get_llm_provider(provider: str | None = None) -> LLMProvider:
    """Return an LLMProvider instance based on env config or explicit name."""
    resolved: str = provider if provider is not None else os.getenv("LLM_PROVIDER", "anthropic")
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
