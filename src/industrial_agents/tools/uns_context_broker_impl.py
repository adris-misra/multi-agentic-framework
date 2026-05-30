"""Utility functions for UNS topic validation (extracted for testability)."""

from __future__ import annotations

import re

_SPARKPLUG_PATTERN = re.compile(
    r"^spBv1\.0/[^/]+/(NBIRTH|NDEATH|DBIRTH|DDEATH|NDATA|DDATA|NCMD|DCMD|STATE)/[^/]+(/[^/]+)?$"
)


def validate_sparkplug_topic(topic: str) -> bool:
    return bool(_SPARKPLUG_PATTERN.match(topic))
