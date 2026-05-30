"""Reproducible synthetic UNS time-series dataset generator.

Generates:
- Multi-asset telemetry (OPC UA nodes, Sparkplug B topics)
- Injected anomalies at known timestamps (for IABENCH evaluation)
- Synthetic SOPs and work-order text for RAG seeding
"""

from __future__ import annotations

import datetime
import json
import math
import random
from pathlib import Path
from typing import Any

import structlog

log = structlog.get_logger(__name__)

# Asset definitions matching config/uns_topic_taxonomy.yaml
_ASSETS = [
    {"id": "motor_01", "class": "motor", "line": "line1", "cell": "cell1"},
    {"id": "motor_02", "class": "motor", "line": "line1", "cell": "cell2"},
    {"id": "press_01", "class": "injection_mold", "line": "line2", "cell": "cell1"},
    {"id": "press_02", "class": "injection_mold", "line": "line2", "cell": "cell2"},
    {"id": "hydraulic_01", "class": "hydraulic", "line": "line3", "cell": "cell1"},
]

_SIGNALS: dict[str, dict[str, Any]] = {
    "motor": {
        "vibration_rms": {"baseline": 1.2, "sigma": 0.15, "units": "mm/s"},
        "temperature_c": {"baseline": 65.0, "sigma": 2.0, "units": "C"},
        "current_a": {"baseline": 12.5, "sigma": 0.5, "units": "A"},
        "speed_rpm": {"baseline": 1450.0, "sigma": 10.0, "units": "rpm"},
    },
    "injection_mold": {
        "clamp_pressure_bar": {"baseline": 180.0, "sigma": 5.0, "units": "bar"},
        "cycle_time_s": {"baseline": 28.5, "sigma": 0.8, "units": "s"},
        "melt_temperature_c": {"baseline": 230.0, "sigma": 3.0, "units": "C"},
        "shot_weight_g": {"baseline": 142.0, "sigma": 0.5, "units": "g"},
    },
    "hydraulic": {
        "pressure_bar": {"baseline": 200.0, "sigma": 8.0, "units": "bar"},
        "flow_lpm": {"baseline": 45.0, "sigma": 2.0, "units": "L/min"},
        "oil_temperature_c": {"baseline": 45.0, "sigma": 3.0, "units": "C"},
        "filter_dp_bar": {"baseline": 1.5, "sigma": 0.2, "units": "bar"},
    },
}


class AnomalyProfile:
    __slots__ = ("asset_id", "signal", "start_ts", "duration_minutes", "magnitude", "anomaly_type")

    def __init__(
        self,
        asset_id: str,
        signal: str,
        start_ts: datetime.datetime,
        duration_minutes: int,
        magnitude: float,
        anomaly_type: str,
    ) -> None:
        self.asset_id = asset_id
        self.signal = signal
        self.start_ts = start_ts
        self.duration_minutes = duration_minutes
        self.magnitude = magnitude
        self.anomaly_type = anomaly_type


class UNSDataGenerator:
    def __init__(
        self,
        seed: int = 42,
        enterprise: str = "acme",
        site: str = "chicago",
    ) -> None:
        self._rng = random.Random(seed)
        self._enterprise = enterprise
        self._site = site

    def _uns_path(self, asset: dict[str, Any], signal: str) -> str:
        return (
            f"{self._enterprise}/{self._site}/{asset['line']}/{asset['cell']}/"
            f"{asset['id']}/{signal}"
        )

    def _sparkplug_topic(self, asset: dict[str, Any], signal: str) -> str:
        return f"spBv1.0/{self._enterprise}/NDATA/{asset['line']}/{asset['id']}"

    def _normal(self, baseline: float, sigma: float) -> float:
        return self._rng.gauss(baseline, sigma)

    def _generate_signal_series(
        self,
        asset: dict[str, Any],
        signal: str,
        config: dict[str, Any],
        start: datetime.datetime,
        n_points: int,
        interval_seconds: int,
        anomaly: AnomalyProfile | None = None,
    ) -> list[dict[str, Any]]:
        rows = []
        for i in range(n_points):
            ts = start + datetime.timedelta(seconds=i * interval_seconds)
            value = self._normal(config["baseline"], config["sigma"])

            if anomaly and anomaly.asset_id == asset["id"] and anomaly.signal == signal:
                elapsed = (ts - anomaly.start_ts).total_seconds() / 60.0
                if 0 <= elapsed <= anomaly.duration_minutes:
                    # Ramp up, hold, ramp down
                    ramp = min(elapsed, anomaly.duration_minutes - elapsed, 1.0)
                    value += anomaly.magnitude * config["baseline"] * ramp

            rows.append(
                {
                    "timestamp_utc": ts.isoformat() + "Z",
                    "uns_path": self._uns_path(asset, signal),
                    "sparkplug_topic": self._sparkplug_topic(asset, signal),
                    "asset_id": asset["id"],
                    "asset_class": asset["class"],
                    "signal": signal,
                    "value": round(value, 4),
                    "units": config["units"],
                    "quality": "good",
                }
            )
        return rows

    def generate(
        self,
        n_hours: int = 24,
        interval_seconds: int = 60,
        inject_anomalies: bool = True,
    ) -> dict[str, Any]:
        start = datetime.datetime(2026, 5, 1, 6, 0, 0, tzinfo=datetime.timezone.utc)
        n_points = (n_hours * 3600) // interval_seconds
        all_rows: list[dict[str, Any]] = []

        # Inject known anomalies for IABENCH
        anomalies: list[AnomalyProfile] = []
        if inject_anomalies:
            anomalies = [
                AnomalyProfile(
                    asset_id="motor_01",
                    signal="vibration_rms",
                    start_ts=start + datetime.timedelta(hours=4),
                    duration_minutes=45,
                    magnitude=3.5,
                    anomaly_type="bearing_wear",
                ),
                AnomalyProfile(
                    asset_id="press_01",
                    signal="clamp_pressure_bar",
                    start_ts=start + datetime.timedelta(hours=10),
                    duration_minutes=20,
                    magnitude=-0.3,
                    anomaly_type="hydraulic_leak",
                ),
                AnomalyProfile(
                    asset_id="hydraulic_01",
                    signal="filter_dp_bar",
                    start_ts=start + datetime.timedelta(hours=18),
                    duration_minutes=120,
                    magnitude=2.0,
                    anomaly_type="filter_clog",
                ),
            ]

        for asset in _ASSETS:
            signals = _SIGNALS.get(asset["class"], {})
            asset_anomalies = [a for a in anomalies if a.asset_id == asset["id"]]
            for signal, config in signals.items():
                anomaly = next((a for a in asset_anomalies if a.signal == signal), None)
                rows = self._generate_signal_series(
                    asset=asset,
                    signal=signal,
                    config=config,
                    start=start,
                    n_points=n_points,
                    interval_seconds=interval_seconds,
                    anomaly=anomaly,
                )
                all_rows.extend(rows)

        log.info(
            "synthetic_generated",
            rows=len(all_rows),
            assets=len(_ASSETS),
            n_hours=n_hours,
            anomalies=len(anomalies),
        )

        return {
            "rows": all_rows,
            "metadata": {
                "enterprise": self._enterprise,
                "site": self._site,
                "start_utc": start.isoformat(),
                "n_hours": n_hours,
                "interval_seconds": interval_seconds,
                "n_rows": len(all_rows),
                "n_assets": len(_ASSETS),
                "anomalies": [
                    {
                        "asset_id": a.asset_id,
                        "signal": a.signal,
                        "start_utc": a.start_ts.isoformat(),
                        "duration_minutes": a.duration_minutes,
                        "anomaly_type": a.anomaly_type,
                    }
                    for a in anomalies
                ],
            },
        }

    def save_jsonl(self, data: dict[str, Any], path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            for row in data["rows"]:
                f.write(json.dumps(row) + "\n")
        meta_path = path.with_suffix(".meta.json")
        with open(meta_path, "w") as f:
            json.dump(data["metadata"], f, indent=2)
        log.info("synthetic_saved", path=str(path), meta=str(meta_path))

    def save_parquet(self, data: dict[str, Any], path: Path) -> None:
        try:
            import pandas as pd

            df = pd.DataFrame(data["rows"])
            path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(path, index=False)
            log.info("synthetic_parquet_saved", path=str(path), rows=len(df))
        except ImportError:
            log.warning("pandas_not_installed_falling_back_to_jsonl")
            self.save_jsonl(data, path.with_suffix(".jsonl"))
