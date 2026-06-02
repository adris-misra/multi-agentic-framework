"""Ollama local LLM provider adapter."""

from __future__ import annotations

import os
from typing import Any, Self

import structlog

log = structlog.get_logger(__name__)

_DEFAULT_MODEL = "llama3.1:8b"
_DEFAULT_HOST = "http://localhost:11434"


class OllamaProvider:
    def __init__(self: Self, host: str | None = None) -> None:
        import ollama

        self._host = host or os.getenv("OLLAMA_HOST", _DEFAULT_HOST)
        self._client = ollama.AsyncClient(host=self._host)

    async def complete(
        self: Self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        resolved_model = model or os.getenv("OLLAMA_MODEL", _DEFAULT_MODEL)

        kwargs: dict[str, Any] = {
            "model": resolved_model,
            "messages": messages,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if tools:
            kwargs["tools"] = tools

        log.debug("ollama_complete", model=resolved_model, host=self._host)
        response = await self._client.chat(**kwargs)

        msg = response["message"]
        content_blocks: list[dict[str, Any]] = []
        if msg.get("content"):
            content_blocks.append({"type": "text", "text": msg["content"]})
        for tc in msg.get("tool_calls") or []:
            content_blocks.append(
                {
                    "type": "tool_use",
                    "id": "",
                    "name": tc["function"]["name"],
                    "input": tc["function"]["arguments"],
                }
            )

        return {
            "content": content_blocks,
            "model": resolved_model,
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": response.get("prompt_eval_count", 0),
                "output_tokens": response.get("eval_count", 0),
            },
        }
