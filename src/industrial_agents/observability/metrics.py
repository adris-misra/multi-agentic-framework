"""Prometheus metrics for industrial agent telemetry."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from prometheus_client import Counter, Histogram


class IndustrialMetrics:
    """Lazily initializes Prometheus counters/histograms on first use.

    Designed so that tests and environments without prometheus-client installed
    can import this module without error.
    """

    _instance: IndustrialMetrics | None = None

    def __init__(self) -> None:
        self._initialized = False
        self._agent_requests: Counter | None = None
        self._agent_errors: Counter | None = None
        self._decision_latency: Histogram | None = None
        self._hitl_escalations: Counter | None = None
        self._anomalies_detected: Counter | None = None

    @classmethod
    def get(cls) -> IndustrialMetrics:
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        try:
            from prometheus_client import Counter, Histogram

            self._agent_requests = Counter(
                "industrial_agent_requests_total",
                "Total agent handle() invocations",
                ["agent", "intent"],
            )
            self._agent_errors = Counter(
                "industrial_agent_errors_total",
                "Total agent handle() errors",
                ["agent", "error_type"],
            )
            self._decision_latency = Histogram(
                "industrial_agent_decision_seconds",
                "Latency of agent decision emission",
                ["agent", "reversibility"],
                buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 30.0],
            )
            self._hitl_escalations = Counter(
                "industrial_hitl_escalations_total",
                "Total HITL escalation events",
                ["reason"],
            )
            self._anomalies_detected = Counter(
                "industrial_anomalies_detected_total",
                "Total anomalies detected by AnomalyRootCauseAgent",
                ["severity"],
            )
            self._initialized = True
        except ImportError:
            pass

    def inc_requests(self, agent: str, intent: str) -> None:
        if self._initialized and self._agent_requests is not None:
            self._agent_requests.labels(agent=agent, intent=intent).inc()

    def inc_errors(self, agent: str, error_type: str) -> None:
        if self._initialized and self._agent_errors is not None:
            self._agent_errors.labels(agent=agent, error_type=error_type).inc()

    def observe_latency(self, agent: str, reversibility: str, seconds: float) -> None:
        if self._initialized and self._decision_latency is not None:
            self._decision_latency.labels(agent=agent, reversibility=reversibility).observe(seconds)

    def inc_hitl(self, reason: str) -> None:
        if self._initialized and self._hitl_escalations is not None:
            self._hitl_escalations.labels(reason=reason).inc()

    def inc_anomaly(self, severity: str) -> None:
        if self._initialized and self._anomalies_detected is not None:
            self._anomalies_detected.labels(severity=severity).inc()
