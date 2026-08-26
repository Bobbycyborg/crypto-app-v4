"""Reclassify unrefreshed DYNAMIC fields. Manifest source contract wins."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

APPLY_MISS = "APPLY_MISS"
DERIVED = "DERIVED"
REUSED = "REUSED_LIVE_VALUE"
SOURCE_RETRIEVAL = "SOURCE_RETRIEVAL_FAILURE"
SOURCE_INACCESSIBLE = "SOURCE_NOT_MACHINE_ACCESSIBLE"
STATIC_MIS = "STATIC/HISTORICAL — MISCLASSIFIED"

_ADAPTER = {
    "HELIUS": "Helius bounded DEX sampling",
    "FOUNDATION": "Render Foundation (supplyInfo / BME / nodes_and_frames)",
    "SOLANA_RPC": "Solana RPC (concentration / inflation / labelled accounts)",
    "FARSIDE": "Farside Investors ETF tables",
    "LLAMA": "DefiLlama protocol / chain / stables / dexs",
    "CG_BINANCE": "CoinGecko markets + Binance spot/perp",
    "ZEC_EXPL": "zcashexplorer.app blockchain-info",
    "DEX": "DexScreener pair liquidity",
    "OKX": "OKX open interest (RAY Stage-1)",
    "COINBASE": "Coinbase spot 24h (FART vs CB)",
}


def _apply_miss_names(log: list[str]) -> set[str]:
    out: set[str] = set()
    for line in log or []:
        if line.startswith("APPLY_MISS ") and len(line.split()) >= 2:
            out.add(line.split()[1])
    return out


def _from_contract(source_1: str | None) -> str | None:
    s = source_1 or ""
    if "Derived from already-pulled" in s:
        return DERIVED
    if "same canonical pull" in s or "REUSED" in s:
        return REUSED
    if s.startswith("Tokenomics parameter") or "not a weekly" in s or "historical labelled" in s:
        return STATIC_MIS
    return None


def _adapter_for(source_1: str, text: str) -> str:
    s = (source_1 or "") + " " + (text or "")
    if "Helius" in s:
        return "HELIUS"
    if "Foundation" in s or "nodes_and_frames" in s or "liabilityEpochs" in s:
        return "FOUNDATION"
    if "Solana RPC" in s or "getTokenLargest" in s or "getInflationRate" in s:
        return "SOLANA_RPC"
    if "Farside" in s:
        return "FARSIDE"
    if "DefiLlama" in s or "Llama" in s:
        return "LLAMA"
    if "zcashexplorer" in s:
        return "ZEC_EXPL"
    if "DexScreener" in s:
        return "DEX"
    if "OKX" in s:
        return "OKX"
    if "Coinbase" in s:
        return "COINBASE"
    if "CoinGecko" in s or "Binance" in s:
        return "CG_BINANCE"
    return "OTHER"


def classify_one_failure(
    row: dict[str, Any],
    miss: set[str],
    feeds: dict[str, Any],
    source_1: str | None = None,
) -> str:
    locked = _from_contract(source_1)
    if locked:
        return locked
    text = row.get("report_01") or row.get("report_01_text") or ""
    asset = (row.get("asset") or "").lower()
    if "Jan 2025" in text or (asset == "pump" and text.strip() in ("31.2 %", "31.2%")):
        return STATIC_MIS
    if any(h in text for h in ("Sample buy", "Sample sell", "Top-5 buy", "Top5 buy", "Gross buy", "902 swaps")):
        return SOURCE_RETRIEVAL
    if "Last-4 emit" in text or "Cumulative frames" in text or "78.07M" in text:
        return SOURCE_RETRIEVAL
    if "top-20" in text.lower() or "Sol top-20" in text or "Raw top-20" in text:
        return SOURCE_RETRIEVAL
    if "OKX OI" in text:
        return SOURCE_RETRIEVAL
    if miss:
        return APPLY_MISS
    return SOURCE_RETRIEVAL


def map_failures(
    coverage: dict[str, Any],
    apply_log: list[str],
    feeds: dict[str, Any] | None = None,
    manifest_by_id: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    miss = _apply_miss_names(apply_log)
    remaining = [
        r
        for r in coverage.get("fields") or []
        if r.get("classification") == "DYNAMIC" and r.get("status") == "SOURCE_FAILURE"
    ]
    rows = []
    counts: Counter[str] = Counter()
    contradictions = 0
    adapters: dict[str, list[str]] = defaultdict(list)
    for r in remaining:
        man = (manifest_by_id or {}).get(r["field_id"]) or {}
        source_1 = man.get("source_1")
        cause = classify_one_failure(r, miss, feeds or {}, source_1)
        contract = _from_contract(source_1)
        if contract and cause == SOURCE_RETRIEVAL:
            contradictions += 1
            cause = contract
        counts[cause] += 1
        adapter = _adapter_for(source_1 or "", r.get("report_01") or "") if cause == SOURCE_RETRIEVAL else None
        if adapter:
            adapters[adapter].append(r["field_id"])
        rows.append(
            {
                "field_id": r["field_id"],
                "asset": r.get("asset"),
                "section": r.get("section"),
                "cause": cause,
                "source_1": source_1,
                "adapter": adapter,
                "report_01": r.get("report_01"),
            }
        )
    genuine = counts[SOURCE_RETRIEVAL] + counts[SOURCE_INACCESSIBLE]
    fake = counts[APPLY_MISS] + counts[DERIVED] + counts[REUSED] + counts[STATIC_MIS]
    return {
        "schema": "autojob01-failure-cause-v2-contract",
        "remaining_unrefreshed_dynamic": len(remaining),
        "counts": dict(counts),
        "genuine_retrieval_or_inaccessible": genuine,
        "true_external_adapter_count": len(adapters),
        "adapters": {k: {"n": len(v), "fields": v} for k, v in sorted(adapters.items())},
        "not_source_failure": fake,
        "manifest_failure_contradictions": contradictions,
        "fields": rows,
    }


def format_map(payload: dict[str, Any]) -> str:
    c = payload.get("counts") or {}
    lines = [
        f"Unrefreshed DYNAMIC remaining = {payload['remaining_unrefreshed_dynamic']}",
        f"APPLY_MISS = {c.get(APPLY_MISS, 0)}",
        f"DERIVED = {c.get(DERIVED, 0)}",
        f"REUSED_LIVE_VALUE = {c.get(REUSED, 0)}",
        f"SOURCE_RETRIEVAL_FAILURE = {c.get(SOURCE_RETRIEVAL, 0)}",
        f"SOURCE_NOT_MACHINE_ACCESSIBLE = {c.get(SOURCE_INACCESSIBLE, 0)}",
        f"STATIC/HISTORICAL — MISCLASSIFIED = {c.get(STATIC_MIS, 0)}",
        f"genuine retrieval/automation gaps = {payload['genuine_retrieval_or_inaccessible']}",
        f"true external adapters = {payload.get('true_external_adapter_count', 0)}",
        f"manifest/failure-cause contradictions = {payload.get('manifest_failure_contradictions', 0)}",
        f"fake SOURCE_FAILURE (apply/derived/reused/static) = {payload['not_source_failure']}",
        "",
    ]
    for r in payload.get("fields") or []:
        lines.append(
            f"{r['field_id']}\t{r['cause']}\t{r.get('adapter') or '-'}\t{r.get('asset')}\t{r.get('report_01')}"
        )
    return "\n".join(lines) + "\n"


def format_adapters(payload: dict[str, Any]) -> str:
    lines = [
        f"True external adapters = {payload.get('true_external_adapter_count', 0)}",
        "Report remaining gaps by adapter, not by repeated visible fields.",
        "",
    ]
    for name, row in (payload.get("adapters") or {}).items():
        label = _ADAPTER.get(name, name)
        lines.append(f"{name}\t{label}\tfields={row['n']}\t{','.join(row['fields'])}")
    if not payload.get("adapters"):
        lines.append("(none)")
    return "\n".join(lines) + "\n"
