"""OPC UA async read-only client with Purdue zone-enforcement wrapper."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Self

import structlog

if TYPE_CHECKING:
    from asyncua import Client as _AsyncUAClient

log = structlog.get_logger(__name__)

_DEFAULT_ENDPOINT = "opc.tcp://localhost:4840"


class OPCUAReading:
    __slots__ = ("node_id", "value", "quality", "source_timestamp", "server_timestamp")

    def __init__(
        self: Self,
        node_id: str,
        value: object,
        quality: str,
        source_timestamp: str,
        server_timestamp: str,
    ) -> None:
        self.node_id = node_id
        self.value = value
        self.quality = quality
        self.source_timestamp = source_timestamp
        self.server_timestamp = server_timestamp

    def to_dict(self: Self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "value": self.value,
            "quality": self.quality,
            "source_timestamp": self.source_timestamp,
            "server_timestamp": self.server_timestamp,
        }


class OPCUAClient:
    """Async read-only OPC UA client.

    Writes are intentionally blocked — all write attempts raise PermissionError.
    This enforces the Purdue zone model: agent logic runs at zone 3/4,
    OPC UA servers live at zone 2/1 and must never receive unsupervised writes.
    """

    def __init__(
        self: Self,
        endpoint: str | None = None,
        username: str | None = None,
        password: str | None = None,
        purdue_zone: int = 2,
    ) -> None:
        self._endpoint: str = (
            endpoint if endpoint is not None else os.getenv("OPCUA_ENDPOINT", _DEFAULT_ENDPOINT)
        )
        self._username = username
        self._password = password
        self._purdue_zone = purdue_zone
        self._client: _AsyncUAClient | None = None

    async def connect(self: Self) -> None:
        try:
            from asyncua import Client

            self._client = Client(url=self._endpoint)
            if self._username:
                self._client.set_user(self._username)
                self._client.set_password(self._password or "")
            await self._client.connect()
            log.info("opcua_connected", endpoint=self._endpoint)
        except Exception as exc:
            log.error("opcua_connect_failed", endpoint=self._endpoint, error=str(exc))
            raise

    async def disconnect(self: Self) -> None:
        if self._client is not None:
            try:
                await self._client.disconnect()
                log.info("opcua_disconnected")
            except Exception as exc:
                log.warning("opcua_disconnect_error", error=str(exc))
            finally:
                self._client = None

    async def read_node(self: Self, node_id: str) -> OPCUAReading:
        if self._client is None:
            raise RuntimeError("OPCUAClient not connected; call connect() first")

        import datetime

        log.debug("opcua_read", node_id=node_id)
        try:
            node = self._client.get_node(node_id)
            dv = await node.read_data_value()
            quality = "good" if dv.StatusCode is not None and dv.StatusCode.is_good() else "bad"
            ts = dv.SourceTimestamp or datetime.datetime.now(datetime.UTC)
            return OPCUAReading(
                node_id=node_id,
                value=dv.Value.Value if dv.Value else None,
                quality=quality,
                source_timestamp=ts.isoformat(),
                server_timestamp=(dv.ServerTimestamp or ts).isoformat(),
            )
        except Exception as exc:
            log.error("opcua_read_failed", node_id=node_id, error=str(exc))
            raise

    async def read_nodes(self: Self, node_ids: list[str]) -> list[OPCUAReading]:
        results = []
        for nid in node_ids:
            reading = await self.read_node(nid)
            results.append(reading)
        return results

    def write_node(self: Self, *_args: object, **_kwargs: object) -> None:
        raise PermissionError(
            "OPCUAClient is read-only. Write operations must go through the "
            "SafetyGuardrailAgent and WorkOrderMESAgent with HITL approval."
        )

    async def __aenter__(self: Self) -> OPCUAClient:
        await self.connect()
        return self

    async def __aexit__(self: Self, *_args: object) -> None:
        await self.disconnect()
