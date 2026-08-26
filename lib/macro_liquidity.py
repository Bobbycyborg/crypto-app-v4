"""Macro liquidity via FRED public CSV export — no API key."""

from __future__ import annotations

import subprocess
from datetime import date, datetime, timedelta, timezone
from typing import Any

from lib.data_integrity import freshness_status
from lib.fetchers.http import get_text

_FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv"
_FRED_HOME = "https://fred.stlouisfed.org/"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_csv(text: str) -> list[tuple[date, float]]:
    rows: list[tuple[date, float]] = []
    for line in text.strip().splitlines()[1:]:
        if not line.strip():
            continue
        parts = line.split(",", 1)
        if len(parts) != 2:
            continue
        try:
            rows.append((date.fromisoformat(parts[0].strip()), float(parts[1].strip())))
        except ValueError:
            continue
    rows.sort(key=lambda x: x[0])
    return rows


_FRED_SERIES = ("WALCL", "WDTGAL", "RRPONTSYD", "M2SL", "NFCI", "ECBASSETSW", "JPNASSETS")


def _fetch_series(series_id: str) -> tuple[str, list[tuple[date, float]], str | None]:
    url = f"{_FRED_CSV}?id={series_id}"
    try:
        proc = subprocess.run(
            ["curl", "-fsSL", "--max-time", "15", url],
            capture_output=True,
            text=True,
            timeout=18,
            check=True,
        )
        rows = _parse_csv(proc.stdout)
        if not rows:
            raise ValueError(f"{series_id}: empty series")
        return series_id, rows, None
    except Exception as curl_exc:
        try:
            text = get_text(url, timeout=12, retries=2)
            rows = _parse_csv(text)
            if not rows:
                raise ValueError(f"{series_id}: empty series")
            return series_id, rows, None
        except Exception as req_exc:
            return series_id, [], f"curl: {curl_exc}; requests: {req_exc}"


def _fetch_all_series() -> dict[str, tuple[list[tuple[date, float]], str | None]]:
    out: dict[str, tuple[list[tuple[date, float]], str | None]] = {}
    for sid in _FRED_SERIES:
        _, rows, err = _fetch_series(sid)
        out[sid] = (rows, err)
    return out


def _closest_on_or_before(series: list[tuple[date, float]], target: date) -> tuple[date, float] | None:
    candidates = [r for r in series if r[0] <= target]
    return candidates[-1] if candidates else None


def _pct_change(current: float, past: float) -> float | None:
    if past == 0:
        return None
    return round((current - past) / past * 100, 2)


def _change_over_days(series: list[tuple[date, float]], days: int) -> float | None:
    if not series:
        return None
    d, v = series[-1]
    past = _closest_on_or_before(series, d - timedelta(days=days))
    if not past:
        return None
    return _pct_change(v, past[1])


def _yoy_pct(series: list[tuple[date, float]]) -> tuple[float | None, str | None]:
    if not series:
        return None, None
    d, v = series[-1]
    past = _closest_on_or_before(series, d - timedelta(days=365))
    if not past:
        return None, d.isoformat()
    return _pct_change(v, past[1]), d.isoformat()


def _build_net_liquidity_series(
    walcl: list[tuple[date, float]],
    wdtgal: list[tuple[date, float]],
    rrp: list[tuple[date, float]],
) -> list[tuple[date, float]]:
    out: list[tuple[date, float]] = []
    for d, wal in walcl:
        tga_pt = _closest_on_or_before(wdtgal, d)
        rrp_pt = _closest_on_or_before(rrp, d)
        if not tga_pt or not rrp_pt:
            continue
        net_m = wal - tga_pt[1] - (rrp_pt[1] * 1000)
        out.append((d, net_m))
    return out


def fetch_global_liquidity() -> dict[str, Any]:
    """US/EU/JP liquidity pulses, global composite, M2, NFCI — FRED CSV."""
    fetched_at = _now_iso()
    series = _fetch_all_series()
    walcl, wal_err = series["WALCL"]
    wdtgal, tga_err = series["WDTGAL"]
    rrp, rrp_err = series["RRPONTSYD"]
    m2, m2_err = series["M2SL"]
    nfci, nfci_err = series["NFCI"]
    ecb, ecb_err = series["ECBASSETSW"]
    boj, boj_err = series["JPNASSETS"]

    errors = [e for e in (wal_err, tga_err, rrp_err, m2_err, nfci_err, ecb_err, boj_err) if e]
    net_series = _build_net_liquidity_series(walcl, wdtgal, rrp) if walcl and wdtgal and rrp else []

    net_m: float | None = None
    net_90d_pct: float | None = None
    net_yoy_pct: float | None = None
    net_as_of: str | None = None
    if net_series:
        net_d, net_m = net_series[-1]
        net_as_of = net_d.isoformat()
        net_90d_pct = _change_over_days(net_series, 90)
        net_yoy_pct = _change_over_days(net_series, 365)

    ecb_yoy, ecb_as_of = _yoy_pct(ecb)
    boj_yoy, boj_as_of = _yoy_pct(boj)

    regional: list[dict[str, Any]] = []
    pulse_values: list[float] = []
    if net_yoy_pct is not None:
        regional.append({"region": "us", "label": "US net liq", "yoy_pct": net_yoy_pct})
        pulse_values.append(net_yoy_pct)
    if ecb_yoy is not None:
        regional.append({"region": "eu", "label": "ECB assets", "yoy_pct": ecb_yoy})
        pulse_values.append(ecb_yoy)
    if boj_yoy is not None:
        regional.append({"region": "jp", "label": "BoJ assets", "yoy_pct": boj_yoy})
        pulse_values.append(boj_yoy)

    global_pulse_yoy = (
        round(sum(pulse_values) / len(pulse_values), 2) if pulse_values else None
    )

    m2_b: float | None = None
    m2_yoy_pct: float | None = None
    m2_as_of: str | None = None
    if m2:
        m2_d, m2_val = m2[-1]
        m2_b = round(m2_val, 1)
        m2_as_of = m2_d.isoformat()
        m2_yoy_pct, _ = _yoy_pct(m2)

    nfci_latest: float | None = None
    nfci_as_of: str | None = None
    if nfci:
        nfci_d, nfci_latest = nfci[-1]
        nfci_as_of = nfci_d.isoformat()

    core_ok = global_pulse_yoy is not None and len(pulse_values) >= 2
    partial_ok = bool(pulse_values) or m2_b is not None or nfci_latest is not None

    as_of = net_as_of or ecb_as_of or boj_as_of or m2_as_of or nfci_as_of

    return {
        "ok": core_ok,
        "partial_ok": partial_ok,
        "global_pulse_yoy": global_pulse_yoy,
        "global_pulse_regions": len(pulse_values),
        "global_pulse_note": "Equal-weight mean YoY of US net liq, ECB assets, BoJ assets. China/UK not wired.",
        "regional_pulses": regional,
        "net_liquidity_usd_m": round(net_m, 1) if net_m is not None else None,
        "net_liquidity_usd_b": round(net_m / 1000, 2) if net_m is not None else None,
        "net_liquidity_90d_pct": net_90d_pct,
        "net_liquidity_yoy_pct": net_yoy_pct,
        "net_liquidity_as_of": net_as_of,
        "ecb_assets_yoy_pct": ecb_yoy,
        "ecb_assets_as_of": ecb_as_of,
        "boj_assets_yoy_pct": boj_yoy,
        "boj_assets_as_of": boj_as_of,
        "m2_usd_b": m2_b,
        "m2_yoy_pct": m2_yoy_pct,
        "m2_as_of": m2_as_of,
        "nfci_latest": round(nfci_latest, 3) if nfci_latest is not None else None,
        "nfci_as_of": nfci_as_of,
        "as_of": as_of,
        "fetched_at": fetched_at,
        "source": "fred",
        "source_url": _FRED_HOME,
        "series_urls": {
            "walcl": f"{_FRED_HOME}series/WALCL",
            "wdtgal": f"{_FRED_HOME}series/WDTGAL",
            "rrp": f"{_FRED_HOME}series/RRPONTSYD",
            "m2sl": f"{_FRED_HOME}series/M2SL",
            "nfci": f"{_FRED_HOME}series/NFCI",
            "ecb": f"{_FRED_HOME}series/ECBASSETSW",
            "boj": f"{_FRED_HOME}series/JPNASSETS",
        },
        "freshness": freshness_status(fetched_at),
        "errors": errors,
        "error": "; ".join(errors) if errors and not partial_ok else None,
    }
