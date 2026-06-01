"""Secrets vault — reads secrets from env vars, .secrets/ directory, or HashiCorp Vault."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Self
from urllib.parse import urlsplit

import structlog

log = structlog.get_logger(__name__)

_SECRETS_DIR = Path(os.getenv("SECRETS_DIR", ".secrets"))


class SecretsVault:
    """Unified secrets accessor.

    Priority: environment variable → .secrets/<key> file → Vault (if configured).
    Never logs secret values; logs key names only.
    """

    def __init__(self: Self, vault_url: str | None = None, vault_token: str | None = None) -> None:
        self._vault_url = vault_url or os.getenv("VAULT_ADDR")
        self._vault_token = vault_token or os.getenv("VAULT_TOKEN")

    def get(self: Self, key: str, default: str | None = None) -> str | None:
        # 1. Environment variable
        value = os.getenv(key)
        if value:
            log.debug("secret_from_env", key=key)
            return value

        # 2. .secrets/<key> file
        secret_file = _SECRETS_DIR / key
        if secret_file.exists():
            value = secret_file.read_text().strip()
            if value:
                log.debug("secret_from_file", key=key)
                return value

        # 3. Vault (synchronous; use only at startup)
        if self._vault_url and self._vault_token:
            vault_value = self._from_vault(key)
            if vault_value:
                return vault_value

        log.debug("secret_not_found", key=key)
        return default

    def require(self: Self, key: str) -> str:
        value = self.get(key)
        if value is None:
            raise RuntimeError(
                f"Required secret {key!r} not found. "
                f"Set it as an environment variable or place it in {_SECRETS_DIR / key}"
            )
        return value

    def _from_vault(self: Self, key: str) -> str | None:
        try:
            import json
            import urllib.request

            path = key.lower().replace("_", "/")
            url = f"{self._vault_url}/v1/secret/data/industrial-agents/{path}"

            parsed = urlsplit(url)
            if parsed.scheme not in ("http", "https"):
                raise ValueError(
                    f"Vault URL must use http or https scheme, got: {parsed.scheme!r}"
                )

            req = urllib.request.Request(
                url,
                headers={"X-Vault-Token": self._vault_token or ""},
            )
            with urllib.request.urlopen(req, timeout=3) as resp:  # nosec B310 — scheme validated above
                data = json.loads(resp.read())
                value = data.get("data", {}).get("data", {}).get("value")
                if value:
                    log.debug("secret_from_vault", key=key)
                    return str(value)
        except Exception as exc:
            log.warning("vault_lookup_failed", key=key, error=str(exc))
        return None
