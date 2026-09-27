"""Primary source and one live fallback per metric. Old files are not a fallback."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "config" / "sources.json"


def load_sources() -> dict:
    if not PATH.exists():
        return {"metrics": {}}
    return json.loads(PATH.read_text(encoding="utf-8"))


def fallbacks_for(metric_id: str) -> list[str]:
    row = (load_sources().get("metrics") or {}).get(metric_id) or {}
    return [item for item in (row.get("fallbacks") or []) if item and not str(item).startswith("file:")]


def write_catalog() -> None:
    plan = json.loads((ROOT / "collectors" / "collector-plan.json").read_text())
    by_asset_requests: dict[str, list[str]] = {}
    for entry in plan["entries"]:
        key = entry.get("request_key")
        if key:
            by_asset_requests.setdefault(entry.get("asset") or "", []).append(key)
    metrics = {}
    for entry in plan["entries"]:
        if entry.get("disposition") != "COLLECT":
            continue
        mid = entry["metric_id"]
        primary = entry.get("request_key")
        fallbacks: list[str] = []
        if primary == "farside.html.btc":
            fallbacks = ["tftc:https://www.tftc.io/bitcoin-etf-flows/data.json"]
        elif primary in {"farside.html.eth", "farside.html.sol"}:
            fallbacks = []
        elif mid.endswith(".price.usd.live"):
            for key in by_asset_requests.get(entry.get("asset") or "", []):
                if key != primary and (
                    key.startswith("binance.spot.ticker24h.") or key.startswith("dexscreener.token.")
                ):
                    fallbacks.append(key)
                    break
        elif primary and primary.startswith("solana.rpc."):
            fallbacks = ["https://solana-rpc.publicnode.com"]
        metrics[mid] = {
            "primary": primary,
            "fallbacks": fallbacks,
            "never": ["collectors/etf-fallback"] if "etf.flow" in mid or (primary or "").startswith("farside.") else [],
        }
    PATH.write_text(json.dumps({"metrics": metrics}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write_catalog()
    print(f"wrote {PATH}")
