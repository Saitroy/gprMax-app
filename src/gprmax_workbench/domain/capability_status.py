from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CapabilityLevel(str, Enum):
    READY = "ready"
    OPTIONAL = "optional"
    UNAVAILABLE = "unavailable"


@dataclass(slots=True)
class CapabilityStatus:
    code: str
    level: CapabilityLevel
    detail: str = ""

