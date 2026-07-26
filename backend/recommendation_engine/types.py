"""Internal typed contracts shared by recommendation components."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ScoreResult:
    score: float
    confidence: float
    reason: str
    evidence: tuple[str, ...] = ()
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def bounded_score(value: float) -> float:
    return max(-1.0, min(1.0, float(value)))


def bounded_confidence(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
