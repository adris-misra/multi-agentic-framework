"""OpenAI provider adapter."""

from __future__ import annotations

import os
from typing import Any, Self

import structlog

log = structlog.get_logger(__name__)

_DEFAULT_MODEL = "gpt-4o"


class OpenAIProvider:
    def __init__(self: Self, api_key: str | None = None) -> None:
        import openai

        self._client = openai.AsyncOpenAI(api_key=api_key or os.environ["OPENAI_API_KEY"])

    async def complete(
        self: Self,
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
            kwargs["tools"] = [{"type": "function", "function": t} for t in tools]

        log.debug("openai_complete", model=kwargs["model"])
        response = await self._client.chat.completions.create(**kwargs)

        choice = response.choices[0]
        msg = choice.message

        content_blocks: list[dict[str, Any]] = []
        if msg.content:
            content_blocks.append({"type": "text", "text": msg.content})
        if msg.tool_calls:
            for tc in msg.tool_calls:
                import json

                content_blocks.append(
                    {
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.function.name,
                        "input": json.loads(tc.function.arguments),
                    }
                )

        return {
            "content": content_blocks,
            "model": response.model,
            "stop_reason": choice.finish_reason,
            "usage": {
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
            },
        }
