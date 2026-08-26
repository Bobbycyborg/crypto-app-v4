"""BTC daily close — local cache + optional blockchain.info refresh."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from lib.paths import CACHE, DATA

JSON_PATH = DATA / "btc-daily-close.json"
RAW_PATH = CACHE / "btc-daily-close-raw.json"


def fetch_blockchain() -> list[dict]:
    CACHE.mkdir(parents=True, exist_ok=True)
    url = "https://api.blockchain.info/charts/market-price?timespan=all&format=json&sampled=false"
    subprocess.run(
        ["curl", "-sS", url, "-H", "User-Agent: Mozilla/5.0", "-o", str(RAW_PATH)],
        check=True,
    )
    raw = json.loads(RAW_PATH.read_text())
    rows: list[dict] = []
    for v in raw["values"]:
        d = datetime.fromtimestamp(v["x"], timezone.utc).strftime("%Y-%m-%d")
        p = float(v["y"])
        if p > 0:
            rows.append({"date": d, "close": round(p, 2)})
    return rows


def write_cache(rows: list[dict]) -> dict:
    meta = {
        "source": "blockchain.info",
        "series": "market-price (daily close proxy)",
        "fetched": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(rows),
        "from": rows[0]["date"],
        "to": rows[-1]["date"],
        "data": rows,
    }
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(meta, separators=(",", ":")))
    return meta


def load_btc_daily(refresh: bool = False) -> tuple[list[dict], dict]:
    if refresh or not JSON_PATH.exists():
        rows = fetch_blockchain()
        meta = write_cache(rows)
        return meta["data"], {k: meta[k] for k in meta if k != "data"}
    meta = json.loads(JSON_PATH.read_text())
    return meta["data"], {k: meta[k] for k in meta if k != "data"}
