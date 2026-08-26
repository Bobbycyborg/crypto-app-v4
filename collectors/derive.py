"""Named derivation ops only. No eval. No partial inputs."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from collectors.extract import ExtractError


ALLOWED_OPS = frozenset({"ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "RATIO", "PERCENT_CHANGE", "SUM", "MEAN"})


def derive(op: str, inputs: list[Decimal], version: str) -> Decimal:
    if op not in ALLOWED_OPS:
        raise ExtractError("VALUE_INVALID", f"undeclared derivation op {op}")
    if not version:
        raise ExtractError("VALUE_INVALID", "missing calculation_version")
    if op in {"ADD", "SUM"}:
        return sum(inputs, Decimal("0"))
    if op == "MEAN":
        if not inputs:
            raise ExtractError("VALUE_INVALID", "MEAN empty")
        return sum(inputs, Decimal("0")) / Decimal(len(inputs))
    if op == "SUBTRACT":
        if len(inputs) != 2:
            raise ExtractError("VALUE_INVALID", "SUBTRACT needs 2 inputs")
        return inputs[0] - inputs[1]
    if op == "MULTIPLY":
        if len(inputs) != 2:
            raise ExtractError("VALUE_INVALID", "MULTIPLY needs 2 inputs")
        return inputs[0] * inputs[1]
    if op in {"DIVIDE", "RATIO"}:
        if len(inputs) != 2:
            raise ExtractError("VALUE_INVALID", f"{op} needs 2 inputs")
        if inputs[1] == 0:
            raise ExtractError("VALUE_INVALID", "division by zero")
        return inputs[0] / inputs[1]
    if op == "PERCENT_CHANGE":
        if len(inputs) != 2:
            raise ExtractError("VALUE_INVALID", "PERCENT_CHANGE needs 2 inputs")
        if inputs[1] == 0:
            raise ExtractError("VALUE_INVALID", "division by zero")
        return (inputs[0] - inputs[1]) / inputs[1] * Decimal("100")
    raise ExtractError("VALUE_INVALID", f"unhandled op {op}")
