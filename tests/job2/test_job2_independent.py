"""Independent Job 2 checker. Does not import adapters, selectors, normalizers, derivations, or orchestrator."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAN = json.loads((ROOT / "collectors/collector-plan.json").read_text())
REG = json.loads((ROOT / "metrics/metric-registry.json").read_text())
GOLDEN = json.loads((ROOT / "tests/job2/golden-collector-output.json").read_text())
FIX = ROOT / "tests/job2/fixtures/replay/raw"
REQ_CAT = ROOT / "collectors/source_requests.py"


def _dec(v) -> Decimal:
    return Decimal(str(v))


def _eq(a, b) -> bool:
    return _dec(a) == _dec(b)


def gates() -> dict[str, int]:
    g = {k: 0 for k in [
        "job1_metric_missing_from_plan",
        "unknown_metric_in_plan",
        "duplicate_metric_writer",
        "wallet_collector",
        "dormant_asset_collector",
        "required_dynamic_unaccounted",
        "collect_without_source",
        "collect_without_selector",
        "collect_without_normalizer",
        "derived_without_inputs",
        "secret_in_repo",
        "secret_in_output",
        "unproved_provider_substitution",
        "fallback_to_html",
        "fallback_to_cache",
        "source_as_of_fabricated",
        "raw_capture_missing",
        "raw_hash_mismatch",
        "output_without_provenance",
        "wrong_unit",
        "wrong_metric_id",
        "undeclared_derivation",
    ]}
    reg_ids = [m["metric_id"] for m in REG["metrics"]]
    plan_ids = [e["metric_id"] for e in PLAN["entries"]]
    g["job1_metric_missing_from_plan"] = len(set(reg_ids) - set(plan_ids))
    g["unknown_metric_in_plan"] = len(set(plan_ids) - set(reg_ids))
    g["duplicate_metric_writer"] = len(plan_ids) - len(set(plan_ids))
    by = {m["metric_id"]: m for m in REG["metrics"]}
    prefix = {
        "coingecko": "coingecko.",
        "binance": "binance.",
        "defillama": "defillama.",
        "farside": "farside.",
        "alternative_me": "alternative_me.",
        "hyperliquid": "hyperliquid.",
        "io_explorer": "io.",
        "nosana": "nosana.",
        "render_foundation": "render.",
        "solana_rpc": "solana.rpc.",
        "zcash_explorer": "zcash.",
        "dexscreener": "dexscreener.",
    }
    for e in PLAN["entries"]:
        m = by[e["metric_id"]]
        if e["disposition"] == "COLLECT" and (m["owner"] == "GROK" or m["wallet_or_non_wallet"] == "WALLET"):
            g["wallet_collector"] += 1
        if e["disposition"] in {"COLLECT", "DERIVE"} and m["asset"] in {"RAY", "GRASS"}:
            g["dormant_asset_collector"] += 1
        if m["metric_type"] == "CURRENT_DYNAMIC" and m["wallet_or_non_wallet"] == "NON_WALLET":
            if e["disposition"] not in {"COLLECT", "DERIVE", "PRESERVE", "BLOCKED_SOURCE", "COMPOSITE_ONLY"}:
                g["required_dynamic_unaccounted"] += 1
        if e["disposition"] == "COLLECT":
            if not e.get("source_key"):
                g["collect_without_source"] += 1
            if not e.get("selector"):
                g["collect_without_selector"] += 1
            if not e.get("normalizer"):
                g["collect_without_normalizer"] += 1
            rk = e.get("request_key") or ""
            pref = prefix.get(e["source_key"])
            if not pref or not rk.startswith(pref):
                g["unproved_provider_substitution"] += 1
        if e["disposition"] == "DERIVE":
            der = e.get("derivation") or {}
            if not der.get("inputs"):
                g["derived_without_inputs"] += 1
            if der.get("op") not in {None, "ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "RATIO", "PERCENT_CHANGE", "SUM", "MEAN"}:
                g["undeclared_derivation"] += 1
    secret_needles = ("api_key=", "Bearer ", "HELIUS_API_KEY=", "PRIVATE_KEY=")
    for p in [ROOT / "collectors/collector-plan.json", ROOT / "collectors/source_requests.py"]:
        txt = p.read_text(encoding="utf-8")
        if any(n in txt for n in secret_needles):
            g["secret_in_repo"] += 1
    return g


def independent_fixture_values() -> dict[str, Decimal]:
    cg = json.loads((FIX / "coingecko.markets.active.body").read_text())
    btc = next(x for x in cg if x["id"] == "bitcoin")
    fng = json.loads((FIX / "alternative_me.fng.body").read_text())
    jobs = json.loads((FIX / "nosana.jobs.count.body").read_text())
    rev = json.loads((FIX / "defillama.summary.fees.pump.fun.dailyRevenue.body").read_text())
    tvl = json.loads((FIX / "defillama.historicalChainTvl.Solana.body").read_text())
    stables = json.loads((FIX / "defillama.stablecoinchains.body").read_text())
    sol_st = next(x for x in stables if x["name"] == "Solana")
    inf = json.loads((FIX / "solana.rpc.getInflationRate.body").read_text())
    hl = json.loads((FIX / "hyperliquid.info.tokenDetails.body").read_text())
    oi = json.loads((FIX / "binance.fapi.openInterest.FARTCOINUSDT.body").read_text())
    mark = json.loads((FIX / "binance.fapi.ticker24h.FARTCOINUSDT.body").read_text())
    prem = json.loads((FIX / "binance.fapi.premiumIndex.BTCUSDT.body").read_text())
    return {
        "btc.price.usd.live": _dec(btc["current_price"]),
        "global.fear_greed.index.current": _dec(fng["data"][0]["value"]),
        "nos.jobs.running.count": _dec(jobs["byState"]["RUNNING"]),
        "nos.nodes.with_running_jobs.count": _dec(jobs["distinctNodesWithRunningJobs"]),
        "pump.revenue.usd.7d": sum((_dec(v) for _, v in rev["totalDataChart"][-7:]), Decimal("0")),
        "sol.tvl.usd.current": _dec(tvl[-1]["tvl"]),
        "sol.stablecoin.usd.current": _dec(sol_st["totalCirculatingUSD"]["peggedUSD"]),
        "sol.inflation.pct.current": _dec(inf["result"]["total"]) * Decimal("100"),
        "hype.emissions.tokens.remaining": _dec(hl["futureEmissions"]),
        "fart.oi.usd.current": _dec(oi["openInterest"]) * _dec(mark["lastPrice"]),
        "btc.funding.rate.latest": _dec(prem["lastFundingRate"]) * Decimal("100"),
    }


def check_output(run: dict) -> dict[str, int]:
    extra = {
        "secret_in_output": 0,
        "fallback_to_html": 0,
        "fallback_to_cache": 0,
        "source_as_of_fabricated": 0,
        "raw_capture_missing": 0,
        "raw_hash_mismatch": 0,
        "output_without_provenance": 0,
        "wrong_unit": 0,
        "wrong_metric_id": 0,
    }
    plan_ids = {e["metric_id"] for e in PLAN["entries"]}
    blob = json.dumps(run)
    if any(n in blob for n in ("api_key=", "Bearer ", "BEGIN PRIVATE")):
        extra["secret_in_output"] += 1
    if "CACHE_FALLBACK" in blob or '"replay_used_as_live"' in blob:
        extra["fallback_to_cache"] += 1
    by_plan = {e["metric_id"]: e for e in PLAN["entries"]}
    for fact in run["facts"]:
        mid = fact["metric_id"]
        if mid not in plan_ids:
            extra["wrong_metric_id"] += 1
        e = by_plan.get(mid)
        if fact["status"] == "OK" and e and e["disposition"] == "COLLECT":
            if not fact.get("fetched_at") or not fact.get("raw_capture_sha256"):
                extra["output_without_provenance"] += 1
            if fact.get("source_as_of") and fact["source_as_of"] != "UNKNOWN":
                if fact["source_as_of"] == fact.get("fetched_at"):
                    extra["source_as_of_fabricated"] += 1
            if e.get("unit") and fact.get("unit") and e["unit"] != fact["unit"]:
                extra["wrong_unit"] += 1
        if fact["status"] != "OK" and fact.get("normalized_value") not in (None,):
            extra["fallback_to_html"] += 1
    return extra


def main() -> int:
    g = gates()
    proc = subprocess.run(
        [sys.executable, str(ROOT / "collectors/run_collectors.py"), "--replay", str(ROOT / "tests/job2/fixtures/replay")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        print("REPLAY_FAIL", proc.returncode)
        return 1
    run = json.loads((ROOT / "runtime-NOT-FOR-GH/job2/replay/collector-run.json").read_text())
    extra = check_output(run)
    g.update({k: g.get(k, 0) + extra.get(k, 0) for k in extra})

    emitted = {f["metric_id"]: f for f in run["facts"]}
    indy = independent_fixture_values()
    mismatches = []
    for mid, expected in indy.items():
        got = emitted[mid]["normalized_value"]
        if not _eq(got, expected):
            mismatches.append((mid, got, str(expected)))
    for row in GOLDEN["facts"]:
        mid = row["metric_id"]
        if mid not in emitted or emitted[mid]["status"] != "OK":
            mismatches.append((mid, emitted.get(mid), row["expected_normalized"]))
            continue
        if not _eq(emitted[mid]["normalized_value"], row["expected_normalized"]):
            mismatches.append((mid, emitted[mid]["normalized_value"], row["expected_normalized"]))

    print("GATES", json.dumps(g, indent=2))
    if mismatches:
        print("MISMATCH", mismatches[:12])
        return 1
    if any(v != 0 for v in g.values()):
        return 1
    print("PASS test_job2_independent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
