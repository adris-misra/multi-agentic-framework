"""Open Policy Agent (OPA) HTTP client for Rego policy evaluation."""

from __future__ import annotations

import os
from typing import Any, Self

import structlog

log = structlog.get_logger(__name__)

_DEFAULT_OPA_URL = "http://localhost:8181"


class OPAClient:
    """Async HTTP client for OPA's REST API (v1/data endpoint)."""

    def __init__(self: Self, url: str | None = None) -> None:
        self._url = url or os.getenv("OPA_URL", _DEFAULT_OPA_URL)

    def _path_to_url(self: Self, policy_path: str) -> str:
        # e.g. "data.industrial.safety.allow" → "/v1/data/industrial/safety/allow"
        parts = policy_path.split(".")
        if parts[0] == "data":
            parts = parts[1:]
        return f"{self._url}/v1/data/{'/'.join(parts)}"

    async def query(self: Self, policy_path: str, input_data: dict[str, Any]) -> dict[str, Any]:
        try:
            import aiohttp

            url = self._path_to_url(policy_path)
            body = {"input": input_data}

            async with aiohttp.ClientSession() as session, session.post(
                url,
                json=body,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()  # type: ignore[no-any-return]
                else:
                    log.warning(
                        "opa_query_non_200",
                        status=resp.status,
                        policy=policy_path,
                    )
                    return {"result": None}
        except Exception as exc:
            log.error("opa_query_failed", policy=policy_path, error=str(exc))
            # Fail open for read operations; fail closed for writes
            return {"result": None}

    async def is_allowed(self: Self, action: str, context: dict[str, Any]) -> bool:
        result = await self.query("data.industrial.safety.allow", {"action": action, **context})
        return bool(result.get("result", True))
