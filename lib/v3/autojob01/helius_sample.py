"""Stage-1 bounded SWAP sample via Helius. One retrieval fans to dependent fields.

SWAP-only on principal Solana pools seeded by DexScreener 24h volume.
Not market-wide. Fail loud on 429 after backoff. Never dated Stage-1 JSON.
"""

from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

import certifi
import requests

from lib.fetchers.live_spot_price import now_iso
from lib.helius_client import load_api_key, rpc as helius_rpc
from lib.v3.autojob01.contracts import PRICE_ASSETS

DEX_OK = {"raydium", "meteora", "orca", "pumpswap", "whirlpool"}
MAX_POOLS = 3
MAX_PAGES = 10
PAGE_LIMIT = 100


def _fail(field: str, err: str) -> dict[str, Any]:
    return {"ok": False, "field": field, "error": str(err), "freshness": "MISSING"}


def _dex_pools(mint: str) -> tuple[list[str], float | None]:
    r = requests.get(
        f"https://api.dexscreener.com/latest/dex/tokens/{mint}",
        timeout=45,
        verify=certifi.where(),
    )
    r.raise_for_status()
    pairs = r.json().get("pairs") or []
    sol = [
        p
        for p in pairs
        if isinstance(p, dict)
        and str(p.get("chainId") or "").lower() == "solana"
        and str(p.get("dexId") or "").lower() in DEX_OK
        and p.get("pairAddress")
    ]
    sol.sort(key=lambda p: float((p.get("volume") or {}).get("h24") or 0), reverse=True)
    px = None
    for p in sol:
        try:
            px = float(p.get("priceUsd") or 0) or px
        except (TypeError, ValueError):
            pass
        if px:
            break
    return [p["pairAddress"] for p in sol[:MAX_POOLS]], px


def _paginate(address: str, gte_time: int) -> list[dict]:
    all_txs: list[dict] = []
    before: str | None = None
    seen: set[str] = set()
    key = load_api_key()
    for _ in range(MAX_PAGES):
        params: dict[str, Any] = {"api-key": key, "limit": PAGE_LIMIT, "gte-time": gte_time}
        if before:
            params["before"] = before
        for attempt in range(2):
            r = requests.get(
                f"https://api.helius.xyz/v0/addresses/{address}/transactions",
                params=params,
                timeout=12,
                verify=certifi.where(),
            )
            if r.status_code == 429:
                time.sleep(min(2 ** attempt, 3.0))
                continue
            r.raise_for_status()
            break
        else:
            raise RuntimeError(f"Helius 429 persisted for {address}")
        txs = r.json()
        time.sleep(0.45)
        if not txs:
            break
        new = [t for t in txs if t.get("signature") not in seen]
        for t in new:
            seen.add(t["signature"])
        all_txs.extend(new)
        if txs[-1].get("timestamp", 0) < gte_time:
            break
        before = txs[-1]["signature"]
        if not new:
            break
    return all_txs


def _swap_delta(tx: dict, wallet: str, mint: str) -> tuple[float, float]:
    if tx.get("type") != "SWAP":
        return 0.0, 0.0
    buy = sell = 0.0
    for t in tx.get("tokenTransfers") or []:
        if t.get("mint") != mint:
            continue
        amt = float(t.get("tokenAmount") or 0)
        if t.get("toUserAccount") == wallet:
            buy += amt
        if t.get("fromUserAccount") == wallet:
            sell += amt
    return buy, sell


def _token_balance(owner: str, mint: str) -> float | None:
    try:
        res = helius_rpc(
            "getTokenAccountsByOwner",
            [owner, {"mint": mint}, {"encoding": "jsonParsed"}],
        )
        return sum(
            float(a["account"]["data"]["parsed"]["info"]["tokenAmount"].get("uiAmount") or 0)
            for a in (res or {}).get("value", [])
        )
    except Exception:
        return None


def sample_mint(symbol: str) -> dict[str, Any]:
    spec = PRICE_ASSETS.get(symbol) or {}
    mint = spec.get("dex_mint")
    if not mint:
        return _fail(f"HELIUS.{symbol}", "no dex mint")
    try:
        pools, px = _dex_pools(mint)
        if not pools:
            raise RuntimeError("no principal Solana pools")
        gte = int(datetime.now(timezone.utc).timestamp()) - 24 * 3600
        by_sig: dict[str, dict] = {}
        for i, addr in enumerate(pools):
            if i:
                time.sleep(0.3)
            for tx in _paginate(addr, gte):
                if tx.get("type") != "SWAP":
                    continue
                if not any(t.get("mint") == mint for t in (tx.get("tokenTransfers") or [])):
                    continue
                by_sig[tx["signature"]] = tx
        pool_set = set(pools)
        buy: dict[str, float] = defaultdict(float)
        sell: dict[str, float] = defaultdict(float)
        for tx in by_sig.values():
            involved: set[str] = set()
            for t in tx.get("tokenTransfers") or []:
                if t.get("mint") != mint:
                    continue
                if t.get("toUserAccount"):
                    involved.add(t["toUserAccount"])
                if t.get("fromUserAccount"):
                    involved.add(t["fromUserAccount"])
            for wallet in involved:
                if wallet in pool_set:
                    continue
                b, s = _swap_delta(tx, wallet, mint)
                if b > 0:
                    buy[wallet] += b
                if s > 0:
                    sell[wallet] += s
        gross_buy = sum(buy.values())
        gross_sell = sum(sell.values())
        buyers = sorted(buy.items(), key=lambda kv: kv[1], reverse=True)
        top5 = sum(v for _, v in buyers[:5])
        top5_pct = (top5 / gross_buy * 100.0) if gross_buy else None
        nets = sorted(
            ((w, buy.get(w, 0) - sell.get(w, 0)) for w in set(buy) | set(sell)),
            key=lambda kv: kv[1],
            reverse=True,
        )
        still = 0.0
        checked = 0
        for w, net in nets[:10]:
            if net <= 0:
                continue
            bal = _token_balance(w, mint)
            time.sleep(0.12)
            if bal is None:
                continue
            checked += 1
            if bal > 0:
                still += bal
        sample_buy = sum(v for _, v in buyers[:20])
        sellers = sorted(sell.items(), key=lambda kv: kv[1], reverse=True)
        sample_sell = sum(v for _, v in sellers[:20])
        return {
            "ok": True,
            "symbol": symbol,
            "mint": mint,
            "pools": pools,
            "price_usd": px,
            "swap_count": len(by_sig),
            "unique_buyers": len(buy),
            "gross_buy_tokens": gross_buy,
            "gross_sell_tokens": gross_sell,
            "sample_buy_tokens": sample_buy,
            "sample_sell_tokens": sample_sell,
            "net_tokens": gross_buy - gross_sell,
            "top5_buy_pct": top5_pct,
            "still_held_tokens": still,
            "still_held_checked": checked,
            "sample_buy_usd": (sample_buy * px) if px else None,
            "sample_sell_usd": (sample_sell * px) if px else None,
            "source": "Helius enhanced txs SWAP-only · DexScreener principal pools",
            "fetched_at": now_iso(),
        }
    except Exception as exc:  # noqa: BLE001
        return _fail(f"HELIUS.{symbol}", str(exc))
