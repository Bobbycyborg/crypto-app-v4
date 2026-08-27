"""Deterministic numeric-token formatter recovery for Job 3 bindings."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from renderer.formatters import format_value, infer_formatter

_TOKEN_RE = re.compile(
    r"""
    ~?
    (?:\+|[-−])?
    \$?
    (?:
      (?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?
      |\d+\.\d+
    )
    (?:[eE][+\-−]\d+)?
    [kKmMbBtT]?
    (?:%|pp)?
    (?:×|x)?
    (?:/(?:d|day|wk|yr))?
    """,
    re.VERBOSE,
)

_SCALE = {
    "k": 1000,
    "K": 1000,
    "m": 1_000_000,
    "M": 1_000_000,
    "b": 1_000_000_000,
    "B": 1_000_000_000,
    "t": 1_000_000_000_000,
    "T": 1_000_000_000_000,
}


class FormatterRecoveryError(Exception):
    pass


@dataclass(frozen=True)
class RawSelection:
    raw: Any
    source: str
    rejected_occurrence_raw: Any | None = None


def is_numeric_raw(raw: Any) -> bool:
    if raw is None or raw == "UNKNOWN":
        return False
    if isinstance(raw, str):
        try:
            float(raw)
            return True
        except ValueError:
            return False
    return True


def _absolute_from_metric_value(value: Any) -> Any | None:
    if value is None or value == "UNKNOWN":
        return None
    s = str(value).strip()
    if not s:
        return None
    s = s.replace("−", "-")
    m = re.search(
        r"([+\-]?\d{1,3}(?:,\d{3})+|[+\-]?\d+)(?:\.(\d+))?([kKmMbBtT%]|pp|×|x)?",
        s,
    )
    if not m:
        return None
    num = m.group(1).replace(",", "")
    dec = m.group(2) or ""
    sfx = (m.group(3) or "").replace("×", "x")
    if sfx in {"%", "pp", "x"}:
        try:
            return float(f"{num}.{dec}" if dec else num)
        except ValueError:
            return None
    scale = _SCALE.get(sfx, 1)
    try:
        return float(f"{num}.{dec}" if dec else num) * scale
    except ValueError:
        return None


def _metric_fallback_candidates(row: dict[str, Any], *, allow_value_parse: bool = False) -> list[Any]:
    out: list[Any] = []
    raw = row.get("raw_value")
    if raw is not None and raw != "UNKNOWN" and is_numeric_raw(raw):
        out.append(raw)
    if allow_value_parse:
        parsed = _absolute_from_metric_value(row.get("value"))
        if parsed is not None and parsed not in out:
            out.append(parsed)
    return out


def _occurrence_raw(row: dict[str, Any], occurrence_id: str) -> Any | None:
    for ev in row.get("evidence_variants", []):
        if ev.get("occurrence_id") == occurrence_id:
            return ev.get("raw_value")
    return None


def _try_recover(
    source_literal: str,
    raw_value: Any,
    *,
    manifest_lit: str = "",
    anchor_after: str = "",
) -> dict[str, Any] | None:
    if not is_numeric_raw(raw_value):
        return None
    try:
        return recover_formatter(
            source_literal=source_literal,
            raw_value=raw_value,
            manifest_lit=manifest_lit,
            anchor_after=anchor_after,
        )
    except FormatterRecoveryError:
        return None


def resolve_binding_raw(
    reg: dict[str, Any],
    metric_id: str,
    occurrence_id: str,
    *,
    source_literal: str = "",
    manifest_lit: str = "",
    anchor_after: str = "",
) -> RawSelection | None:
    row = reg.get(metric_id)
    if not row:
        return None

    occ_raw = _occurrence_raw(row, occurrence_id)
    kwargs = {
        "manifest_lit": manifest_lit,
        "anchor_after": anchor_after,
    }

    if occ_raw == "UNKNOWN" or (occ_raw is not None and not is_numeric_raw(occ_raw)):
        return None

    if occ_raw is not None:
        if not is_numeric_raw(occ_raw):
            return None
        if source_literal and _try_recover(source_literal, occ_raw, **kwargs):
            return RawSelection(occ_raw, "OCCURRENCE")
        for candidate in _metric_fallback_candidates(row, allow_value_parse=True):
            if _try_recover(source_literal, candidate, **kwargs):
                return RawSelection(
                    candidate,
                    "METRIC_FALLBACK_INVALID_OCCURRENCE_RAW",
                    occ_raw,
                )
        if source_literal:
            raise FormatterRecoveryError(
                f"FORMATTER_RAW_CONTRACT_BLOCKER:{metric_id}:{occurrence_id}"
            )
        return None

    for candidate in _metric_fallback_candidates(row, allow_value_parse=False):
        if not source_literal:
            if candidate is not None:
                return RawSelection(candidate, "METRIC_FALLBACK")
            continue
        if _try_recover(source_literal, candidate, **kwargs):
            return RawSelection(candidate, "METRIC_FALLBACK")
    return None


def select_binding_raw(
    reg: dict[str, Any],
    metric_id: str,
    occurrence_id: str,
    *,
    source_literal: str = "",
) -> tuple[Any | None, str | None]:
    row = reg.get(metric_id)
    if not row:
        return None, None
    occ_raw = _occurrence_raw(row, occurrence_id)
    if occ_raw == "UNKNOWN" or (occ_raw is not None and not is_numeric_raw(occ_raw)):
        return None, "OCCURRENCE" if occ_raw is not None else None
    if not source_literal:
        if occ_raw is not None and occ_raw != "UNKNOWN" and is_numeric_raw(occ_raw):
            return occ_raw, "OCCURRENCE"
        raw = row.get("raw_value")
        if raw is None or raw == "UNKNOWN" or not is_numeric_raw(raw):
            return None, None
        return raw, "METRIC_FALLBACK"
    try:
        sel = resolve_binding_raw(
            reg,
            metric_id,
            occurrence_id,
            source_literal=source_literal,
        )
    except FormatterRecoveryError:
        return None, None
    if sel is None:
        return None, None
    return sel.raw, sel.source


def select_binding_raw_for_binding(
    reg: dict[str, Any],
    binding: dict[str, Any],
) -> tuple[Any | None, str | None, Any | None]:
    fmt = binding.get("formatter") or {}
    rejected = fmt.get("rejected_occurrence_raw")
    raw, source = select_binding_raw(reg, binding["metric_id"], binding["job1_occurrence_id"])
    if raw is None:
        return None, None, rejected
    if fmt.get("formatter_raw_source"):
        source = fmt["formatter_raw_source"]
    return raw, source, rejected


def enumerate_numeric_tokens(text: str) -> list[tuple[int, int, str]]:
    n = len(text)
    by_start: dict[int, tuple[int, str]] = {}
    for i in range(n):
        for j in range(i + 1, n + 1):
            tok = text[i:j]
            if not _is_token(tok):
                continue
            if i not in by_start or (j - i) > (by_start[i][0] - i):
                by_start[i] = (j, tok)
    return [(i, end, tok) for i, (end, tok) in sorted(by_start.items())]


def _is_token(tok: str) -> bool:
    if not tok or not _TOKEN_RE.fullmatch(tok):
        return False
    return infer_formatter(tok).get("type") == "numeric"


def _body_variants(source_literal: str) -> list[tuple[str, str]]:
    if source_literal.endswith(".") and not source_literal.endswith(".."):
        return [(source_literal[:-1], "."), (source_literal, "")]
    return [(source_literal, "")]


def _manifest_token_hint(manifest_lit: str, body: str, start: int, token: str) -> str:
    plain = re.sub(r"<[^>]+>", "", manifest_lit or "")
    if not plain or plain == body:
        return token
    prefix = body[:start]
    if not plain.startswith(prefix):
        return token
    plain_rest = plain[len(prefix) :]
    best = token
    for t_start, _t_end, ptok in enumerate_numeric_tokens(plain_rest):
        if t_start == 0 and ptok.startswith(token) and len(ptok) > len(best):
            best = ptok
    return best


def _build_formatter(
    source_literal: str,
    start: int,
    end: int,
    token: str,
    extra_suffix: str,
    manifest_lit: str,
    anchor_after: str,
) -> dict[str, Any]:
    from renderer.formatters import adjust_formatter_for_binding

    hint = _manifest_token_hint(manifest_lit, source_literal, start, token)
    inner = infer_formatter(hint)
    if inner.get("type") != "numeric":
        raise FormatterRecoveryError(f"non-numeric token {token!r}")
    fmt = adjust_formatter_for_binding(inner, manifest_lit, token, anchor_after)
    fmt = dict(fmt)
    fmt["literal_prefix"] = source_literal[:start]
    fmt["literal_suffix"] = source_literal[end:] + extra_suffix
    return fmt


def recover_formatter(
    *,
    source_literal: str,
    raw_value: Any,
    manifest_lit: str = "",
    anchor_after: str = "",
) -> dict[str, Any]:
    if not is_numeric_raw(raw_value):
        raise FormatterRecoveryError("raw not numeric usable")

    matches: list[tuple[int, int, dict[str, Any]]] = []
    for body, extra_suffix in _body_variants(source_literal):
        for start, end, token in enumerate_numeric_tokens(body):
            fmt = _build_formatter(body, start, end, token, extra_suffix, manifest_lit, anchor_after)
            if format_value(raw_value, fmt) == source_literal:
                matches.append((start, end, fmt))

    if not matches:
        raise FormatterRecoveryError(f"FORMATTER_RECOVERY_BLOCKER:{source_literal!r}")

    by_start: dict[int, tuple[int, dict[str, Any]]] = {}
    for start, end, fmt in matches:
        if start not in by_start or (end - start) > (by_start[start][0] - start):
            by_start[start] = (end, fmt)

    best_len = max(end - start for start, (end, _fmt) in by_start.items())
    winners = [start for start, (end, _fmt) in by_start.items() if (end - start) == best_len]
    if len(winners) != 1:
        raise FormatterRecoveryError(
            f"FORMATTER_AMBIGUITY_BLOCKER:{source_literal!r} positions={sorted(by_start)}"
        )

    fmt = by_start[winners[0]][1]
    if fmt.get("type") == "string_exact":
        raise FormatterRecoveryError("numeric binding cannot use string_exact")
    fmt = dict(fmt)
    fmt["roundtrip_verified"] = True
    return fmt


def sentinel_raw(raw: Any) -> Any:
    d = Decimal(str(raw))
    if d == 0:
        return Decimal("1.234")
    return d * Decimal("1.23456789") + Decimal("0.001")


def check_dynamicity(source_literal: str, raw_value: Any, formatter: dict[str, Any]) -> bool:
    if not formatter.get("roundtrip_verified"):
        return False
    original = format_value(raw_value, formatter)
    if original != source_literal:
        return False
    sent = format_value(sentinel_raw(raw_value), formatter)
    if sent == source_literal:
        return False
    prefix = formatter.get("literal_prefix", "")
    suffix = formatter.get("literal_suffix", "")
    if prefix and not sent.startswith(prefix):
        return False
    if suffix and not sent.endswith(suffix):
        return False
    if prefix and not original.startswith(prefix):
        return False
    if suffix and not original.endswith(suffix):
        return False
    return True
