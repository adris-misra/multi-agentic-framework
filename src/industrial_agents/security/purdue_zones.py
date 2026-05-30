"""Purdue Enterprise Reference Architecture zone enforcement."""

from __future__ import annotations

from dataclasses import dataclass

import structlog

log = structlog.get_logger(__name__)

# Zone definitions matching config/purdue_zones.yaml
ZONE_NAMES: dict[int, str] = {
    0: "Field Devices",
    1: "Control Systems",
    2: "Supervisory",
    3: "Manufacturing Operations",
    4: "Site Business",
    5: "Enterprise / Cloud",
}

# Cross-zone communication rules (from_zone → allowed_to_zones)
# Agents always run at zone 3 or higher; they may READ from lower zones
# but WRITE access below zone 2 is blocked without HITL approval.
_READ_ALLOWED: dict[int, set[int]] = {
    4: {3, 4, 5},
    3: {2, 3, 4, 5},
    2: {1, 2, 3, 4},
    1: {0, 1, 2},
    0: {0},
    5: {3, 4, 5},
}

_WRITE_ALLOWED: dict[int, set[int]] = {
    4: {4, 5},
    3: {3, 4},
    2: {2, 3},
    1: {1, 2},
    0: set(),
    5: {4, 5},
}


@dataclass
class ZoneViolation:
    from_zone: int
    to_zone: int
    operation: str
    message: str


class PurdueZoneEnforcer:
    def __init__(self, write_gate_threshold: int = 2) -> None:
        self._write_gate = write_gate_threshold

    def check_read(self, from_zone: int, to_zone: int) -> ZoneViolation | None:
        allowed = _READ_ALLOWED.get(from_zone, set())
        if to_zone not in allowed:
            v = ZoneViolation(
                from_zone=from_zone,
                to_zone=to_zone,
                operation="read",
                message=(
                    f"Zone {from_zone} ({ZONE_NAMES.get(from_zone)}) "
                    f"cannot read from zone {to_zone} ({ZONE_NAMES.get(to_zone)})"
                ),
            )
            log.warning("purdue_read_violation", **vars(v))
            return v
        return None

    def check_write(self, from_zone: int, to_zone: int) -> ZoneViolation | None:
        if to_zone <= self._write_gate:
            v = ZoneViolation(
                from_zone=from_zone,
                to_zone=to_zone,
                operation="write",
                message=(
                    f"Write to zone {to_zone} ({ZONE_NAMES.get(to_zone)}) "
                    f"blocked — at or below write gate threshold {self._write_gate}"
                ),
            )
            log.error("purdue_write_violation_gate", **vars(v))
            return v

        allowed = _WRITE_ALLOWED.get(from_zone, set())
        if to_zone not in allowed:
            v = ZoneViolation(
                from_zone=from_zone,
                to_zone=to_zone,
                operation="write",
                message=(
                    f"Zone {from_zone} ({ZONE_NAMES.get(from_zone)}) "
                    f"cannot write to zone {to_zone} ({ZONE_NAMES.get(to_zone)})"
                ),
            )
            log.error("purdue_write_violation", **vars(v))
            return v
        return None

    def zone_name(self, zone: int) -> str:
        return ZONE_NAMES.get(zone, f"Unknown Zone {zone}")
