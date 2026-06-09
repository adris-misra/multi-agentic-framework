"""MQTT Sparkplug B v3 subscriber — UNS-aware, read-only telemetry ingest."""

from __future__ import annotations

import asyncio
import json
import os
from collections import deque
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Protocol, Self

import structlog

if TYPE_CHECKING:
    import paho.mqtt.client as mqtt

log = structlog.get_logger(__name__)

# Sparkplug B topic structure: spBv1.0/<group_id>/<message_type>/<edge_node_id>[/<device_id>]
_SPARKPLUG_TOPIC_PREFIX = "spBv1.0"
_MAX_BUFFER = 1000


class _MQTTMessage(Protocol):
    topic: str
    payload: bytes


class SparkplugMessage:
    __slots__ = (
        "topic",
        "group_id",
        "message_type",
        "edge_node_id",
        "device_id",
        "payload",
        "timestamp",
    )

    def __init__(
        self: Self,
        topic: str,
        payload: dict[str, Any],
    ) -> None:
        self.topic = topic
        parts = topic.split("/")
        self.group_id = parts[1] if len(parts) > 1 else ""
        self.message_type = parts[2] if len(parts) > 2 else ""
        self.edge_node_id = parts[3] if len(parts) > 3 else ""
        self.device_id = parts[4] if len(parts) > 4 else ""
        self.payload = payload

        import datetime

        self.timestamp = datetime.datetime.now(datetime.UTC).isoformat()

    def to_dict(self: Self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "group_id": self.group_id,
            "message_type": self.message_type,
            "edge_node_id": self.edge_node_id,
            "device_id": self.device_id,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


class SparkplugClient:
    """Async MQTT Sparkplug B subscriber.

    Subscribes to the UNS topic hierarchy and buffers incoming messages.
    Publishes are intentionally limited to NCMD/DCMD topics and require
    explicit zone validation before any message is sent.
    """

    def __init__(
        self: Self,
        broker_host: str | None = None,
        broker_port: int = 1883,
        client_id: str = "industrial-agents",
        subscribe_groups: list[str] | None = None,
    ) -> None:
        # Use explicit None-check so mypy infers str (not str|None) for self._host
        self._host: str = (
            broker_host if broker_host is not None else os.getenv("MQTT_BROKER", "localhost")
        )
        self._port = int(os.getenv("MQTT_PORT", str(broker_port)))
        self._client_id = client_id
        self._groups = subscribe_groups or ["#"]
        self._buffer: deque[SparkplugMessage] = deque(maxlen=_MAX_BUFFER)
        self._client: mqtt.Client | None = None
        self._callbacks: list[Callable[[SparkplugMessage], None]] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    def on_message(self: Self, callback: Callable[[SparkplugMessage], None]) -> None:
        self._callbacks.append(callback)

    def _on_paho_message(
        self: Self,
        _client: object,
        _userdata: object,
        msg: _MQTTMessage,
    ) -> None:
        try:
            try:
                payload_data = json.loads(msg.payload.decode())
            except Exception:
                payload_data = {"raw": msg.payload.hex()}

            spk_msg = SparkplugMessage(topic=msg.topic, payload=payload_data)
            self._buffer.append(spk_msg)

            for cb in self._callbacks:
                try:
                    cb(spk_msg)
                except Exception as exc:
                    log.warning("sparkplug_callback_error", error=str(exc))

            log.debug(
                "sparkplug_message_received",
                topic=msg.topic,
                group=spk_msg.group_id,
                msg_type=spk_msg.message_type,
            )
        except Exception as exc:
            log.error("sparkplug_message_parse_error", error=str(exc))

    async def connect(self: Self) -> None:
        import paho.mqtt.client as mqtt_mod

        self._client = mqtt_mod.Client(client_id=self._client_id, protocol=mqtt_mod.MQTTv5)
        self._client.on_message = self._on_paho_message

        def on_connect(
            client: mqtt.Client,
            _userdata: object,
            _flags: object,
            rc: int,
            _props: object = None,
        ) -> None:
            if rc == 0:
                log.info("sparkplug_connected", host=self._host, port=self._port)
                for group in self._groups:
                    topic = f"{_SPARKPLUG_TOPIC_PREFIX}/{group}"
                    client.subscribe(topic, qos=1)
                    log.debug("sparkplug_subscribed", topic=topic)
            else:
                log.error("sparkplug_connect_failed", rc=rc)

        self._client.on_connect = on_connect
        self._client.connect(self._host, self._port, keepalive=60)
        self._client.loop_start()

    def disconnect(self: Self) -> None:
        if self._client is not None:
            self._client.loop_stop()
            self._client.disconnect()
            log.info("sparkplug_disconnected")

    def get_buffered_messages(self: Self, limit: int | None = None) -> list[SparkplugMessage]:
        msgs = list(self._buffer)
        if limit is not None:
            return msgs[-limit:]
        return msgs

    def clear_buffer(self: Self) -> None:
        self._buffer.clear()

    async def __aenter__(self: Self) -> SparkplugClient:
        await self.connect()
        return self

    async def __aexit__(self: Self, *_args: object) -> None:
        self.disconnect()
