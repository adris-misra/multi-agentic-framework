"""Unit tests for protocol adapters and governance/security modules."""

from __future__ import annotations

import pytest

from industrial_agents.governance.pii_redactor import PIIRedactor, redact_dict, redact_string
from industrial_agents.security.purdue_zones import PurdueZoneEnforcer
from industrial_agents.tools.uns_context_broker_impl import validate_sparkplug_topic


class TestPIIRedactor:
    def test_redacts_email(self) -> None:
        r = PIIRedactor()
        result = r.redact("Contact john.doe@example.com for details")
        assert "@" not in result
        assert "[REDACTED]" in result

    def test_redacts_ssn(self) -> None:
        r = PIIRedactor()
        result = r.redact("SSN: 123-45-6789")
        assert "123-45-6789" not in result
        assert "[REDACTED]" in result

    def test_leaves_non_pii(self) -> None:
        r = PIIRedactor()
        text = "Motor vibration at 1.5 mm/s on asset motor_01"
        assert r.redact(text) == text

    def test_redacts_nested_dict(self) -> None:
        r = PIIRedactor()
        data = {"operator": "john.doe@factory.com", "value": 42.0, "notes": {"email": "x@y.com"}}
        result = r.redact_payload(data)
        assert "john.doe@factory.com" not in str(result)
        assert result["value"] == 42.0


class TestPurdueZoneEnforcer:
    def test_read_allowed_same_zone(self) -> None:
        e = PurdueZoneEnforcer()
        assert e.check_read(from_zone=3, to_zone=3) is None

    def test_read_allowed_down(self) -> None:
        e = PurdueZoneEnforcer()
        assert e.check_read(from_zone=3, to_zone=2) is None

    def test_write_blocked_below_threshold(self) -> None:
        e = PurdueZoneEnforcer(write_gate_threshold=2)
        v = e.check_write(from_zone=3, to_zone=1)
        assert v is not None
        assert v.operation == "write"

    def test_write_allowed_same_zone(self) -> None:
        e = PurdueZoneEnforcer()
        assert e.check_write(from_zone=3, to_zone=3) is None

    def test_write_blocked_cross_zone_upward(self) -> None:
        e = PurdueZoneEnforcer()
        v = e.check_write(from_zone=1, to_zone=3)
        assert v is not None

    def test_zone_name(self) -> None:
        e = PurdueZoneEnforcer()
        assert "Control" in e.zone_name(1)
        assert "Field" in e.zone_name(0)


class TestSparkplugValidation:
    def test_valid_sparkplug_topic(self) -> None:
        assert validate_sparkplug_topic("spBv1.0/Chicago/NDATA/line1/motor1") is True

    def test_invalid_prefix(self) -> None:
        assert validate_sparkplug_topic("mqtt/Chicago/NDATA/line1") is False

    def test_missing_message_type(self) -> None:
        assert validate_sparkplug_topic("spBv1.0/Chicago") is False

    def test_valid_without_device(self) -> None:
        assert validate_sparkplug_topic("spBv1.0/Chicago/NBIRTH/line1") is True
