"""OpenTelemetry tracing configuration."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import opentelemetry.trace as _otel_trace


def configure_tracing(
    service_name: str = "industrial-agents",
    otlp_endpoint: str | None = None,
) -> None:
    """Configure OpenTelemetry with OTLP exporter (Jaeger-compatible)."""
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)

        endpoint = otlp_endpoint or os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"
        )
        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))

        trace.set_tracer_provider(provider)
    except ImportError:
        import structlog

        structlog.get_logger(__name__).warning(
            "opentelemetry_not_installed",
            hint="pip install opentelemetry-sdk opentelemetry-exporter-otlp",
        )


def get_tracer(name: str = "industrial-agents") -> _otel_trace.Tracer:
    from opentelemetry import trace

    return trace.get_tracer(name)
