"""Anthropic Claude provider adapter."""

from __future__ import annotations

import os
from typing import Any

import structlog

log = structlog.get_logger(__name__)

_DEFAULT_MODEL = "claude-sonnet-4-6"


class AnthropicProvider:
    def __init__(self, api_key: str | None = None) -> None:
        import anthropic

        self._client = anthropic.AsyncAnthropic(
            api_key=api_key or os.environ["ANTHROPIC_API_KEY"]
        )

    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": model or _DEFAULT_MODEL,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        log.debug("anthropic_complete", model=kwargs["model"])
        response = await self._client.messages.create(**kwargs)

        content_blocks = []
        for block in response.content:
            if hasattr(block, "text"):
                content_blocks.append({"type": "text", "text": block.text})
            elif hasattr(block, "type") and block.type == "tool_use":
                content_blocks.append(
                    {
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    }
                )

        return {
            "content": content_blocks,
            "model": response.model,
            "stop_reason": response.stop_reason,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        }
