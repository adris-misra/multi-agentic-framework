"""AWS Bedrock provider adapter (Claude via Converse API)."""

from __future__ import annotations

import os
from typing import Any

import structlog

log = structlog.get_logger(__name__)

_DEFAULT_MODEL = "anthropic.claude-3-5-sonnet-20241022-v2:0"


class BedrockProvider:
    def __init__(self) -> None:
        import boto3

        self._client = boto3.client(
            "bedrock-runtime",
            region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
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
        model_id = model or os.getenv("BEDROCK_MODEL_ID", _DEFAULT_MODEL)

        converse_messages = [
            {"role": m["role"], "content": [{"text": m["content"]}]}
            for m in messages
            if m.get("role") != "system"
        ]

        system_prompt = next((m["content"] for m in messages if m.get("role") == "system"), None)

        kwargs: dict[str, Any] = {
            "modelId": model_id,
            "messages": converse_messages,
            "inferenceConfig": {"maxTokens": max_tokens, "temperature": temperature},
        }
        if system_prompt:
            kwargs["system"] = [{"text": system_prompt}]
        if tools:
            kwargs["toolConfig"] = {
                "tools": [
                    {
                        "toolSpec": {
                            "name": t["name"],
                            "description": t.get("description", ""),
                            "inputSchema": {"json": t.get("parameters", {})},
                        }
                    }
                    for t in tools
                ]
            }

        log.debug("bedrock_complete", model=model_id)
        # boto3 is synchronous; run in executor in production
        import asyncio

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: self._client.converse(**kwargs))

        output = response.get("output", {}).get("message", {})
        content_blocks: list[dict[str, Any]] = []
        for block in output.get("content", []):
            if "text" in block:
                content_blocks.append({"type": "text", "text": block["text"]})
            elif "toolUse" in block:
                tu = block["toolUse"]
                content_blocks.append(
                    {
                        "type": "tool_use",
                        "id": tu.get("toolUseId", ""),
                        "name": tu["name"],
                        "input": tu.get("input", {}),
                    }
                )

        usage = response.get("usage", {})
        return {
            "content": content_blocks,
            "model": model_id,
            "stop_reason": response.get("stopReason", "end_turn"),
            "usage": {
                "input_tokens": usage.get("inputTokens", 0),
                "output_tokens": usage.get("outputTokens", 0),
            },
        }
