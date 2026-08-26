"""Live first-party pulls for AUTOJOB01. Never dated Stage-1 JSON as live."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import certifi
import requests

from lib.fetchers.http import get_json
from lib.fetchers.live_spot_price import now_iso

RENDER_MINT = "rndrizKT3MK1iimdxRdWabcF7Zg7AR5T4nud4EkHBof"
FOUNDATION = "https://infra.shikumi.cc"
HL_INFO = "https://api.hyperliquid.xyz/info"
HYPE_TOKEN = "0x0d01dc56dcaaca66ad901c959b4011ec"
AF_ADDR = "0xfefefefefefefefefefefefefefefefefefefefe"
HYPERLABS = "0x43e9abea1910387c4292bca4b94de81462f8a251"


def _fail(field: str, reason: str, **extra: Any) -> dict[str, Any]:
    return {"ok": False, "field": field, "failure_type": reason, "freshness": "MISSING", **extra}


def _foundation(path: str, data: bytes | None = None) -> Any:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "crypto-app-v3-autojob01/1.0",
        "Origin": "https://stats.renderfoundation.com",
        "Referer": "https://stats.renderfoundation.com/",
    }
    r = requests.request(
        "POST" if data is not None else "GET",
        FOUNDATION + path,
        data=data,
        headers=headers,
        timeout=45,
        verify=certifi.where(),
    )
    r.raise_for_status()
    return r.json()


def collect_render_live(cg_row: dict[str, Any] | None) -> dict[str, Any]:
    """Foundation supplyInfo + BME + CG circ. Conflict preserved. No average."""
    errors: list[str] = []
    out: dict[str, Any] = {"fetched_at": now_iso(), "source_policy": "show_all_no_average"}
    try:
        supply = _foundation("/api/v1/supplyInfo")
        if not isinstance(supply, dict):
            raise RuntimeError("supplyInfo malformed")
        out["foundation"] = {
            "ok": True,
            "circulating": supply.get("circulatingSupply"),
            "solana_supply": supply.get("solanaSupply") or supply.get("solana_supply"),
            "ethereum_rndr": supply.get("ethereumSupply") or supply.get("ethereum_rndr"),
            "raw": {k: supply.get(k) for k in list(supply)[:20]},
            "source": "https://infra.shikumi.cc/api/v1/supplyInfo",
        }
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Foundation supplyInfo: {exc}")
        out["foundation"] = _fail("RENDER.foundation_circ", "SOURCE_FAILURE", error=str(exc))

    try:
        burns = _foundation("/api/v1/epochBurnStats", json.dumps({"start": 0}).encode())
        rows = burns if isinstance(burns, list) else (burns.get("data") or burns.get("epochs") or [])
        ep = [
            e
            for e in (rows or [])
            if isinstance(e, dict) and isinstance(e.get("id"), int) and e["id"] < 10000
        ]
        ep.sort(key=lambda e: e["id"])
        last4 = ep[-4:] if len(ep) >= 4 else ep
        burned = sum(float(row.get("burnedRender") or row.get("burned") or 0) for row in last4)
        cum = sum(float(row.get("burnedRender") or row.get("burned") or 0) for row in ep)
        out["bme"] = {
            "ok": burned > 0,
            "last4_burned": burned,
            "last4_n": len(last4),
            "cumulative_burned": cum,
            "last4_epoch_ids": [e["id"] for e in last4],
            "source": "https://infra.shikumi.cc/api/v1/epochBurnStats",
        }
        if burned <= 0:
            raise RuntimeError("epochBurnStats last-4 burnedRender is 0")
    except Exception as ext:  # noqa: BLE001
        errors.append(f"Foundation BME: {ext}")
        out["bme"] = _fail("RENDER.bme", "SOURCE_FAILURE", error=str(ext))

    try:
        from collections import defaultdict

        liab = _foundation("/api/v1/liabilityEpochs")
        epochs = liab.get("epochs") if isinstance(liab, dict) else liab
        if not isinstance(epochs, list) or not epochs:
            raise RuntimeError("liabilityEpochs missing epochs[]")
        by_epoch: dict[Any, float] = defaultdict(float)
        for row in epochs:
            if not isinstance(row, dict):
                continue
            if row.get("channel") != "node_operator":
                continue
            eid = row.get("epochId")
            by_epoch[eid] += float(row.get("amountDue") or 0) / 1e8
        ids = (out.get("bme") or {}).get("last4_epoch_ids") or sorted(
            k for k in by_epoch if isinstance(k, int)
        )[-4:]
        emit = sum(by_epoch.get(i, 0.0) for i in ids)
        if emit <= 100:
            raise RuntimeError(f"node_operator last-4 emit parsed as {emit} — refusing 0/stale")
        out["bme_emit"] = {
            "ok": True,
            "last4_emit": emit,
            "last4_epoch_ids": list(ids),
            "source": "https://infra.shikumi.cc/api/v1/liabilityEpochs",
        }
    except Exception as ext:  # noqa: BLE001
        errors.append(f"Foundation liabilityEpochs: {ext}")
        out["bme_emit"] = _fail("RENDER.bme_emit", "SOURCE_FAILURE", error=str(ext))

    try:
        r = requests.get(
            "https://stats.renderfoundation.com/api/nodes_and_frames",
            timeout=45,
            verify=certifi.where(),
            headers={"Accept": "application/json", "User-Agent": "crypto-app-v3-autojob01/1.0"},
        )
        r.raise_for_status()
        nf = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        frames = None
        if isinstance(nf, dict):
            frames = nf.get("frames") or nf.get("total_frames") or nf.get("framesRendered")
        out["frames"] = {
            "ok": isinstance(frames, (int, float)) and frames > 0,
            "cumulative": frames,
            "source": "https://stats.renderfoundation.com/api/nodes_and_frames",
        }
    except Exception as ext:  # noqa: BLE001
        out["frames"] = _fail("RENDER.frames", "SOURCE_FAILURE", error=str(ext))

    cg_circ = None
    if isinstance(cg_row, dict):
        cg_circ = cg_row.get("circulating_supply")
    out["coingecko"] = {
        "ok": cg_circ is not None,
        "circulating": cg_circ,
        "source": "coingecko markets render-token",
    }
    if cg_circ is None:
        errors.append("CoinGecko RENDER circulating missing")

    f_circ = (out.get("foundation") or {}).get("circulating")
    conflict = False
    if isinstance(f_circ, (int, float)) and isinstance(cg_circ, (int, float)) and f_circ and cg_circ:
        conflict = abs(float(f_circ) - float(cg_circ)) / max(abs(float(f_circ)), abs(float(cg_circ))) > 0.01
    out["conflict"] = {
        "ok": True,
        "conflicting": conflict,
        "foundation_circ": f_circ,
        "cg_circ": cg_circ,
        "policy": "show both — never average — never drop a source",
        "print": (
            f"Foundation {_fmt_m(f_circ)} · CG {_fmt_m(cg_circ)}"
            if f_circ is not None and cg_circ is not None
            else None
        ),
    }
    out["ok"] = not errors
    out["errors"] = errors
    return out


def _fmt_m(n: Any) -> str:
    if not isinstance(n, (int, float)):
        return "UNKNOWN"
    return f"{n / 1e6:.2f}M"


def collect_hype_live(cg_row: dict[str, Any] | None) -> dict[str, Any]:
    """Hyperliquid tokenDetails + CoinGecko circ %. Never pick one."""
    errors: list[str] = []
    out: dict[str, Any] = {"fetched_at": now_iso(), "source_policy": "show_all_no_average"}
    try:
        r = requests.post(
            HL_INFO,
            json={"type": "tokenDetails", "tokenId": HYPE_TOKEN},
            timeout=45,
            verify=certifi.where(),
        )
        r.raise_for_status()
        td = r.json()
        if not isinstance(td, dict) or str(td.get("name") or "").upper() != "HYPE":
            raise RuntimeError(f"tokenDetails identity fail name={td.get('name')!r}")
        circ_hl = float(td["circulatingSupply"])
        max_s = float(td["maxSupply"])
        ncu = {str(a).lower(): float(b) for a, b in (td.get("nonCirculatingUserBalances") or [])}
        out["hyperliquid"] = {
            "ok": True,
            "circulating": circ_hl,
            "circulating_pct": circ_hl / max_s * 100.0 if max_s else None,
            "total_supply": float(td.get("totalSupply") or 0),
            "max_supply": max_s,
            "future_emissions": float(td.get("futureEmissions") or 0),
            "af_inventory": ncu.get(AF_ADDR),
            "hyperlabs_ncu": ncu.get(HYPERLABS),
            "source": HL_INFO,
        }
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Hyperliquid tokenDetails: {exc}")
        out["hyperliquid"] = _fail("HYPE.hl_circ", "SOURCE_FAILURE", error=str(exc))

    cg_circ = (cg_row or {}).get("circulating_supply") if isinstance(cg_row, dict) else None
    max_s = ((out.get("hyperliquid") or {}).get("max_supply")) or 1_000_000_000
    cg_pct = (float(cg_circ) / float(max_s) * 100.0) if cg_circ else None
    out["coingecko"] = {
        "ok": cg_circ is not None,
        "circulating": cg_circ,
        "circulating_pct": cg_pct,
        "source": "coingecko markets hyperliquid",
    }
    hl_pct = (out.get("hyperliquid") or {}).get("circulating_pct")
    conflict = False
    if isinstance(hl_pct, (int, float)) and isinstance(cg_pct, (int, float)):
        conflict = abs(hl_pct - cg_pct) > 0.5
    out["conflict"] = {
        "ok": True,
        "conflicting": conflict,
        "cg_pct": cg_pct,
        "hl_pct": hl_pct,
        "policy": "show both — never pick one",
        "print": (
            f"CG {cg_pct:.1f}% · HL {hl_pct:.1f}%"
            if cg_pct is not None and hl_pct is not None
            else None
        ),
    }
    out["ok"] = not errors
    out["errors"] = errors
    return out


def collect_pump_live() -> dict[str, Any]:
    from lib.v3.pump_platform_health import fetch_pump_platform_health

    try:
        row = fetch_pump_platform_health(refresh=True)
        return {"ok": bool(row.get("ok")), "data": row, "source": "defillama pump.fun"}
    except Exception as exc:  # noqa: BLE001
        return _fail("PUMP.llama", "SOURCE_FAILURE", error=str(exc))


def collect_sol_live() -> dict[str, Any]:
    errors: list[str] = []
    out: dict[str, Any] = {"fetched_at": now_iso()}
    try:
        tvl = get_json("https://api.llama.fi/v2/historicalChainTvl/Solana")
        last = tvl[-1] if isinstance(tvl, list) and tvl else None
        out["tvl_usd"] = float(last["tvl"]) if isinstance(last, dict) and last.get("tvl") is not None else None
        out["tvl_source"] = "https://api.llama.fi/v2/historicalChainTvl/Solana"
    except Exception as exc:  # noqa: BLE001
        errors.append(f"SOL TVL: {exc}")
        out["tvl_usd"] = None
    try:
        fees = get_json("https://api.llama.fi/summary/fees/solana")
        chart = fees.get("totalDataChart") or []
        last7 = sum(v for _, v in chart[-7:]) if chart else None
        out["fees_7d_avg"] = (last7 / 7.0) if last7 else None
        out["fees_source"] = "https://api.llama.fi/summary/fees/solana"
    except Exception as exc:  # noqa: BLE001
        errors.append(f"SOL fees: {exc}")
    try:
        chains = get_json("https://stablecoins.llama.fi/stablecoinchains")
        sol = next((c for c in (chains or []) if isinstance(c, dict) and c.get("name") == "Solana"), None)
        tcu = (sol or {}).get("totalCirculatingUSD") or {}
        out["stables_usd"] = tcu.get("peggedUSD") if isinstance(tcu, dict) else tcu
        out["stables_source"] = "https://stablecoins.llama.fi/stablecoinchains"
    except Exception as exc:  # noqa: BLE001
        errors.append(f"SOL stables: {exc}")
    try:
        dexs = get_json("https://api.llama.fi/overview/dexs/solana")
        tot = dexs.get("total24h") if isinstance(dexs, dict) else None
        out["dex_24h_usd"] = tot
        out["dex_source"] = "https://api.llama.fi/overview/dexs/solana"
    except Exception as exc:  # noqa: BLE001
        errors.append(f"SOL dexs: {exc}")
    out["ok"] = not errors
    out["errors"] = errors
    return out


def reject_stale(fetched_at: str | None, *, max_age_hours: float = 48.0) -> None:
    if not fetched_at:
        raise RuntimeError("stale-source rejection: missing fetched_at")
    dt = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
    age = (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0
    if age > max_age_hours:
        raise RuntimeError(f"stale-source rejection: {fetched_at} age {age:.1f}h > {max_age_hours}h")
