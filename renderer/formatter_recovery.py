"""Deterministic numeric-token formatter recovery for Job 3 bindings."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

from renderer.formatters import _dec, format_value, infer_formatter

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


class FormatterRecoveryError(Exception):
    pass


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


def select_binding_raw(
    reg: dict[str, Any],
    metric_id: str,
    occurrence_id: str,
) -> tuple[Any | None, str | None]:
    row = reg.get(metric_id)
    if not row:
        return None, None
    for ev in row.get("evidence_variants", []):
        if ev.get("occurrence_id") == occurrence_id:
            raw = ev.get("raw_value")
            if raw is None or raw == "UNKNOWN":
                return None, "OCCURRENCE"
            if isinstance(raw, str) and not is_numeric_raw(raw):
                return None, "OCCURRENCE"
            return raw, "OCCURRENCE"
    raw = row.get("raw_value")
    if raw is None or raw == "UNKNOWN":
        return None, None
    if isinstance(raw, str) and not is_numeric_raw(raw):
        return None, None
    return raw, "METRIC_FALLBACK"


def _is_token(tok: str) -> bool:
    if not tok or not _TOKEN_RE.fullmatch(tok):
        return False
    return infer_formatter(tok).get("type") == "numeric"


def _token_display_coeff(token: str) -> Decimal | None:
    t = token.strip()
    if t.startswith("~"):
        t = t[1:]
    if t.startswith("+"):
        t = t[1:]
    if t.startswith("$"):
        t = t[1:]
    for sfx in ("pp", "%", "×", "x", "M", "k", "K", "B", "b", "T", "t"):
        if t.endswith(sfx):
            t = t[: -len(sfx)]
            break
    for sfx in ("/wk", "/day", "/d", "/yr"):
        if t.endswith(sfx):
            t = t[: -len(sfx)]
            break
    t = t.replace(",", "").replace("−", "-")
    if not t or t in {"-", "+"}:
        return None
    try:
        return Decimal(t)
    except Exception:
        return None


def _token_formatter(fmt: dict[str, Any]) -> dict[str, Any]:
    out = dict(fmt)
    out.pop("literal_prefix", None)
    out.pop("literal_suffix", None)
    return out


def _token_numeric_affinity(raw_value: Any, token: str) -> bool:
    display = _token_display_coeff(token)
    if display is None:
        return False
    raw = abs(_dec(raw_value))
    shown = abs(display)
    if raw == 0 or shown == 0:
        return raw == shown
    ratio = shown / raw if raw != 0 else Decimal("999")
    if ratio == 1:
        return True
    if Decimal("0.9") <= ratio <= Decimal("1.1"):
        return True
    inv = Decimal("1") / ratio
    return Decimal("0.9") <= inv <= Decimal("1.1")


def _calibrated_formatter(raw_value: Any, fmt: dict[str, Any], token: str, expected: str) -> dict[str, Any] | None:
    base = dict(fmt)
    base.pop("coefficient_override", None)
    if format_value(raw_value, base) == expected:
        return base
    if not _token_numeric_affinity(raw_value, token):
        return None
    token_fmt = _token_formatter(base)
    if format_value(raw_value, token_fmt) == token:
        return base
    display_coeff = _token_display_coeff(token)
    if display_coeff is None:
        return None
    r = _dec(raw_value)
    if r == 0:
        return None
    scale = Decimal(str(fmt.get("scale", 1)))
    trial = dict(base)
    trial["coefficient_override"] = str((display_coeff * scale) / r)
    token_trial = _token_formatter(trial)
    if format_value(raw_value, token_trial) != token:
        return None
    if format_value(raw_value, trial) == expected:
        return trial
    return None


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
    for t_start, t_end, ptok in enumerate_numeric_tokens(plain_rest):
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

    matches: list[tuple[int, int, dict[str, Any], bool]] = []
    for body, extra_suffix in _body_variants(source_literal):
        for start, end, token in enumerate_numeric_tokens(body):
            fmt = _build_formatter(body, start, end, token, extra_suffix, manifest_lit, anchor_after)
            if format_value(raw_value, fmt) == source_literal:
                matches.append((start, end, fmt, False))
                continue
            calibrated = _calibrated_formatter(raw_value, fmt, token, source_literal)
            if calibrated is not None:
                matches.append((start, end, calibrated, True))

    if not matches:
        raise FormatterRecoveryError(f"FORMATTER_RECOVERY_BLOCKER:{source_literal!r}")

    natural = [m for m in matches if not m[3]]
    pool = natural if natural else [m for m in matches]

    if not matches:
        raise FormatterRecoveryError(f"FORMATTER_RECOVERY_BLOCKER:{source_literal!r}")

    by_start: dict[int, tuple[int, dict[str, Any]]] = {}
    for start, end, fmt, _cal in pool:
        if start not in by_start or (end - start) > (by_start[start][0] - start):
            by_start[start] = (end, fmt)

    if not by_start:
        raise FormatterRecoveryError(f"FORMATTER_RECOVERY_BLOCKER:{source_literal!r}")

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
    from decimal import Decimal

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
