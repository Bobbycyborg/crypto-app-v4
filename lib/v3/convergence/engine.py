"""Frozen Convergence V1 synthesis — gate, labels, polarity. No scores."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DIM_FUNDAMENTALS_SUPPLY = "Fundamentals / Supply"

DIMENSIONS = (
    "Price + RS",
    "Spot / Capital",
    "Whales / Players",
    "Attention",
    DIM_FUNDAMENTALS_SUPPLY,
)

POLARITY: dict[str, str] = {
    "STRONG": "POSITIVE",
    "NEUTRAL": "NEUTRAL",
    "WEAK": "NEGATIVE",
    "UNKNOWN": "NONE",
    "SPOT_LED": "POSITIVE",
    "LEVERAGE_LED": "NEGATIVE",
    "MIXED": "NEUTRAL",
    "ACCUMULATING": "POSITIVE",
    "DISTRIBUTING": "NEGATIVE",
    "OPAQUE": "NONE",
    "EXPANDING": "POSITIVE",
    "STABLE": "NEUTRAL",
    "FADING": "NEGATIVE",
    "SUPPORTIVE": "POSITIVE",
    "STRESSED": "NEGATIVE",
}

WEAK_STATUSES = frozenset({"PARTIAL", "INSUFFICIENT"})


@dataclass(frozen=True)
class Row:
    dimension: str
    state: str
    evidence_status: str

    def to_dict(self) -> dict[str, str]:
        return {
            "dimension": self.dimension,
            "state": self.state,
            "evidence_status": self.evidence_status,
        }


@dataclass(frozen=True)
class ConvergenceResult:
    convergence: str
    aligned_direction: str | None
    weak_count: int
    complete_count: int
    directional_votes: dict[str, list[str]]
    rows: tuple[Row, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "convergence": self.convergence,
            "aligned_direction": self.aligned_direction,
            "weak_count": self.weak_count,
            "complete_count": self.complete_count,
            "directional_votes_complete_only": self.directional_votes,
            "rows": [r.to_dict() for r in self.rows],
        }


def weak_count(rows: list[Row] | tuple[Row, ...]) -> int:
    return sum(1 for r in rows if r.evidence_status in WEAK_STATUSES)


def _polarity(state: str) -> str:
    return POLARITY.get(state.upper(), "NONE")


def _directional_votes(rows: list[Row] | tuple[Row, ...]) -> dict[str, list[str]]:
    pos: list[str] = []
    neg: list[str] = []
    neu: list[str] = []
    none: list[str] = []
    for r in rows:
        if r.evidence_status != "COMPLETE":
            none.append(r.dimension)
            continue
        p = _polarity(r.state)
        if p == "POSITIVE":
            pos.append(r.dimension)
        elif p == "NEGATIVE":
            neg.append(r.dimension)
        elif p == "NEUTRAL":
            neu.append(r.dimension)
        else:
            none.append(r.dimension)
    return {"positive": pos, "negative": neg, "neutral": neu, "none": none}


def evaluate_convergence(rows: list[Row] | tuple[Row, ...]) -> ConvergenceResult:
    """Precedence: INSUFFICIENT → DIVERGING → ALIGNED → MIXED."""
    rows_t = tuple(rows)
    wc = weak_count(rows_t)
    complete_count = sum(1 for r in rows_t if r.evidence_status == "COMPLETE")
    votes = _directional_votes(rows_t)
    pos = votes["positive"]
    neg = votes["negative"]

    if wc >= 2 or complete_count < 2:
        return ConvergenceResult(
            convergence="INSUFFICIENT",
            aligned_direction=None,
            weak_count=wc,
            complete_count=complete_count,
            directional_votes=votes,
            rows=rows_t,
        )

    if pos and neg:
        return ConvergenceResult(
            convergence="DIVERGING",
            aligned_direction=None,
            weak_count=wc,
            complete_count=complete_count,
            directional_votes=votes,
            rows=rows_t,
        )

    if len(pos) >= 2 and not neg:
        return ConvergenceResult(
            convergence="ALIGNED",
            aligned_direction="POSITIVE",
            weak_count=wc,
            complete_count=complete_count,
            directional_votes=votes,
            rows=rows_t,
        )

    if len(neg) >= 2 and not pos:
        return ConvergenceResult(
            convergence="ALIGNED",
            aligned_direction="NEGATIVE",
            weak_count=wc,
            complete_count=complete_count,
            directional_votes=votes,
            rows=rows_t,
        )

    return ConvergenceResult(
        convergence="MIXED",
        aligned_direction=None,
        weak_count=wc,
        complete_count=complete_count,
        directional_votes=votes,
        rows=rows_t,
    )


def rows_from_grid(grid: list[dict[str, str]]) -> list[Row]:
    return [Row(g["dimension"], g["state"], g["evidence_status"]) for g in grid]
