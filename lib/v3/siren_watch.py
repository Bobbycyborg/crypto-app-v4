"""Bag wallet watch. Transfer ≠ sale. Log every listed wallet. Empty list → siren blank."""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any

import certifi
import requests

from lib.helius_client import rpc, rpc_url

PUBLIC_RPC = "https://api.mainnet-beta.solana.com"

ROOT = Path(__file__).resolve().parents[2]
CFG_PATH = ROOT / "config" / "siren-wallets.json"
TAGS_PATH = ROOT / "config" / "siren-wallet-tags.json"
CACHE_PATH = ROOT / "data" / "cache" / "siren-watch.json"
HIST_PATH = ROOT / "data" / "cache" / "siren-now-hist.json"
LISBON = ZoneInfo("Europe/Lisbon")
INDEX = ROOT / "index-v4.html"
# 2026-08-01 00:00:00 UTC (brief's 1754006400 is 2025-08-01 — do not use)
AUG1 = 1785542400
AUG1_ISO = "2026-08-01T00:00:00Z"
SIG_PAGE = 25
SIG_PAGES = 3

COINS = [
    "PUMP",
    "RENDER",
    "NOS",
    "ORCA",
    "GRASS",
    "IO",
    "FART",
    "SPX",
    "BONK",
    "GIGA",
    "LOCKIN",
    "RETARDIO",
    "2Z",
    "DRIFT",
    "ANSEM",
]

MINTS = {
    "PUMP": "pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn",
    "RENDER": "rndrizKT3MK1iimdxRdWabcF7Zg7AR5T4nud4EkHBof",
    "NOS": "nosXBVoaCTtYdLvKY6Csb4AC8JCdQKKAaWYtx2ZMoo7",
    "ORCA": "orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE",
    "GRASS": "Grass7B4RdKfBCjTKgSqnXkqjwiGvQyFbuSCUJr3XXjs",
    "IO": "BZLbGTNCSFfoth2GYDtwr7e4imWzpR5jqcUuGEwr646K",
    "FART": "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump",
    "SPX": "J3NKxxXZcnNiMjKw9hYb2K4LUxgwB6t1FtPtQVsv3KFr",
    "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
    "GIGA": "63LfDmNb3MQ8mw9MtZ2To9bEA2M71kZUUGq5tiJxcqj9",
    "LOCKIN": "8Ki8DpuWNxu9VsS3kQbarsCWMcFGWkzzA8pUPto9zBd5",
    "RETARDIO": "6ogzHhzdrQr9Pgv6hZ2MNze7UrzBMAFyBBWUYp1Fhitx",
    "2Z": "J6pQQ3FAcJQeWPPGppWRb4nM8jU3wLyYbRrLh7feMfvd",
    "DRIFT": "DriFtupJYLTosbwoN8koMbEYSx54aFAVLddWsbksjwg7",
    "ANSEM": "9cRCn9rGT8V2imeM2BaKs13yhMEais3ruM3rPvTGpump",
}

TICKER_TO_KEY = {
    "PUMP": "PUMP",
    "RENDER": "RENDER",
    "NOS": "NOS",
    "ORCA": "ORCA",
    "GRASS": "GRASS",
    "IO": "IO",
    "FARTCOIN": "FART",
    "SPX6900": "SPX",
    "BONK": "BONK",
    "GIGA": "GIGA",
    "LOCKIN": "LOCKIN",
    "RETARDIO": "RETARDIO",
    "2Z": "2Z",
    "DRIFT": "DRIFT",
    "ANSEM": "ANSEM",
}

WINTERMUTE = "MfDuWeqSHEqTFVYZ7LoexgAK9dxk7cy4DFJWjWMGVWa"

CEX_PATH = ROOT / "config" / "known-cex-wallets.json"
MM_PATHS = [
    ROOT / "config" / "known-mm-wallets.json",
    ROOT / "reports/shared-mm-registry/shared-entity-wallet-registry.json",
]


def _cex_tag(meta: dict[str, Any]) -> str:
    if meta.get("entity"):
        return str(meta["entity"])
    if meta.get("name"):
        return str(meta["name"])
    label = str(meta.get("label") or "")
    for name in (
        "Wintermute",
        "Bybit",
        "Binance",
        "OKX",
        "Coinbase",
        "DWF",
        "Gate.io",
        "Bitfinex",
        "Kraken",
    ):
        if name.lower() in label.lower():
            return name
    return "CEX"


def _load_dest_tags() -> tuple[dict[str, str], dict[str, str]]:
    cex: dict[str, str] = {}
    mm: dict[str, str] = {}
    raw = json.loads(CEX_PATH.read_text())
    for addr, meta in (raw.get("wallets") or {}).items():
        kind = meta.get("type")
        if kind == "cex":
            cex[addr] = _cex_tag(meta)
        elif kind == "mm" and not str(addr).startswith("0x"):
            mm[addr] = meta.get("entity") or _cex_tag(meta)
    for path in MM_PATHS:
        if not path.exists():
            continue
        reg = json.loads(path.read_text())
        rows = reg.get("wallets") or []
        if isinstance(rows, dict):
            rows = [{"address": a, **(m if isinstance(m, dict) else {})} for a, m in rows.items()]
        for w in rows:
            if w.get("chain") not in (None, "solana"):
                continue
            if w.get("confidence") not in (None, "HIGH", "MEDIUM"):
                continue
            addr = w.get("address")
            if addr and not str(addr).startswith("0x"):
                mm[addr] = w.get("entity") or "MM"
    return cex, mm


def _token_balance(address: str, mint: str) -> float | None:
    try:
        res = _rpc_retry(
            "getTokenAccountsByOwner",
            [address, {"mint": mint}, {"encoding": "jsonParsed"}],
        )
    except Exception:
        return None
    total = 0.0
    for v in (res or {}).get("value") or []:
        try:
            amt = (v["account"]["data"]["parsed"]["info"]["tokenAmount"]["uiAmount"]) or 0
            total += float(amt)
        except (KeyError, TypeError, ValueError):
            continue
    return total


def _dest_label(addr: str, cex: dict[str, str], mm: dict[str, str]) -> str | None:
    if addr in mm:
        return mm[addr]
    if addr in cex:
        return cex[addr]
    return None


def load_wallets() -> dict[str, list[str]]:
    raw = json.loads(CFG_PATH.read_text())
    out: dict[str, list[str]] = {}
    for k in COINS:
        if k not in raw:
            raise KeyError(f"siren-wallets.json missing {k}")
        vals = raw[k]
        if not isinstance(vals, list):
            raise TypeError(f"{k} must be a list")
        out[k] = [str(a) for a in vals]
    extra = set(raw) - set(COINS)
    if extra:
        raise ValueError(f"unexpected keys in siren-wallets.json: {sorted(extra)}")
    return out


def load_tags() -> dict[str, dict[str, str]]:
    if not TAGS_PATH.exists():
        return {}
    return json.loads(TAGS_PATH.read_text())


def fmt_lisbon(ts: int | None) -> str | None:
    if not ts:
        return None
    return datetime.fromtimestamp(int(ts), tz=LISBON).strftime("%d %b %H:%M")


def yesterday_start_unix() -> int:
    now = datetime.now(timezone.utc)
    y = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int(y.timestamp())


def fmt_tokens(n: float) -> str:
    x = abs(float(n))
    if x >= 1_000_000_000:
        s = f"{x / 1_000_000_000:.1f}".rstrip("0").rstrip(".")
        return f"{s}B"
    if x >= 1_000_000:
        s = f"{x / 1_000_000:.1f}".rstrip("0").rstrip(".")
        return f"{s}M"
    if x >= 1_000:
        s = f"{x / 1_000:.1f}".rstrip("0").rstrip(".")
        return f"{s}k"
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return s or "0"


def _rpc_once(url: str, method: str, params: list) -> Any:
    r = requests.post(
        url,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        timeout=20,
        verify=certifi.where(),
    )
    if r.status_code == 429:
        raise RuntimeError("429")
    r.raise_for_status()
    data = r.json()
    if data.get("error"):
        raise RuntimeError(data["error"])
    return data.get("result")


_DEAD_RPC: set[str] = set()


def _rpc_urls() -> list[str]:
    urls: list[str] = []
    try:
        urls.append(rpc_url())
    except Exception:
        pass
    urls.append(PUBLIC_RPC)
    return [u for u in urls if u not in _DEAD_RPC]


def _rpc_retry(method: str, params: list) -> Any:
    last_err: Exception | None = None
    for attempt in range(8):
        urls = _rpc_urls()
        if not urls:
            raise RuntimeError("429")
        for url in urls:
            try:
                return _rpc_once(url, method, params)
            except Exception as e:
                if "429" in str(e):
                    _DEAD_RPC.add(url)
                    continue
                last_err = e
                continue
        if not _rpc_urls():
            raise RuntimeError("429")
        time.sleep(min(8 * (attempt + 1), 40.0))
    raise RuntimeError(last_err)


def _tx_mint_delta(tx: dict, wallet: str, mint: str) -> tuple[float, float, list[str]]:
    meta = (tx or {}).get("meta") or {}
    pre = {((b.get("owner") or ""), b.get("mint")): float((b.get("uiTokenAmount") or {}).get("uiAmount") or 0)
           for b in (meta.get("preTokenBalances") or [])}
    post = {((b.get("owner") or ""), b.get("mint")): float((b.get("uiTokenAmount") or {}).get("uiAmount") or 0)
            for b in (meta.get("postTokenBalances") or [])}
    owners = {o for o, m in list(pre) + list(post) if m == mint}
    sent = received = 0.0
    hops: list[str] = []
    for owner in owners:
        a0 = pre.get((owner, mint), 0.0)
        a1 = post.get((owner, mint), 0.0)
        d = a1 - a0
        if owner == wallet:
            if d < 0:
                sent += -d
            elif d > 0:
                received += d
        elif d > 0:
            hops.append(owner)
    return sent, received, hops


def _sent_dest_mmcex(
    row: dict[str, Any], watched: set[str], cex: dict[str, str], mm: dict[str, str]
) -> str:
    if float(row.get("sent") or 0) <= 0:
        return ""
    return _last_outbound_dest(row.get("new_hops") or [], watched, cex, mm)


def _is_loud_row(
    row: dict[str, Any], watched: set[str], cex: dict[str, str], mm: dict[str, str]
) -> bool:
    return bool(_sent_dest_mmcex(row, watched, cex, mm)) and not row.get("error")


def _coin_loud(
    rows: list[dict[str, Any]], watched: set[str], cex: dict[str, str], mm: dict[str, str]
) -> bool:
    return any(_is_loud_row(r, watched, cex, mm) for r in rows)


def _last_outbound_dest(hops: list[str], watched: set[str], cex: dict[str, str], mm: dict[str, str]) -> str:
    for h in hops:
        if h in watched:
            continue
        lab = _dest_label(h, cex, mm)
        if lab:
            return lab
    return ""


def _pre_mint_amount(tx: dict[str, Any], wallet: str, mint: str) -> float | None:
    meta = (tx or {}).get("meta") or {}
    total = 0.0
    found = False
    for b in meta.get("preTokenBalances") or []:
        if b.get("owner") == wallet and b.get("mint") == mint:
            found = True
            total += float((b.get("uiTokenAmount") or {}).get("uiAmount") or 0)
    return total if found else None


def _page_signatures(address: str) -> tuple[list[dict[str, Any]], bool]:
    all_sigs: list[dict[str, Any]] = []
    before: str | None = None
    for _ in range(SIG_PAGES):
        params: dict[str, Any] = {"limit": SIG_PAGE}
        if before:
            params["before"] = before
        batch = _rpc_retry("getSignaturesForAddress", [address, params]) or []
        time.sleep(0.28)
        if not batch:
            return all_sigs, True
        for s in batch:
            ts = int(s.get("blockTime") or 0)
            all_sigs.append(s)
            if ts and ts < AUG1:
                return all_sigs, True
        before = batch[-1].get("signature")
        if len(batch) < SIG_PAGE:
            return all_sigs, True
    return all_sigs, False


def wallet_to_box(
    row: dict[str, Any],
    tag: str,
    cex: dict[str, str],
    mm: dict[str, str],
    watched: set[str],
) -> dict[str, Any]:
    if not tag or tag in ("?", ""):
        tag = "NeedTag"
    err = row.get("error")
    bal = row.get("balance")
    sent_raw = row.get("sent")
    aug1 = row.get("aug1")
    aug1_status = row.get("aug1_status") or "unknown"
    last_out_status = row.get("last_out_status") or "unknown"
    last_ts = row.get("last_out_ts")
    if last_ts is None:
        last_ts = row.get("last_transfer_ts")
    last_amt = float(row.get("last_out_amount") or row.get("last_transfer_amount") or 0)

    if aug1_status in ("proved", "unmoved_equals_now") and aug1 is not None:
        aug1_fmt = fmt_tokens(aug1)
    else:
        aug1_fmt = "UNKNOWN"

    if bal is None:
        balance_fmt = "UNKNOWN"
    else:
        balance_fmt = fmt_tokens(bal)

    if last_out_status == "none_since_aug1":
        last_out_when = "none since 1 Aug"
        last_out_fmt = ""
    elif last_out_status == "filled" and last_ts:
        last_out_when = fmt_lisbon(int(last_ts)) or "UNKNOWN"
        last_out_fmt = fmt_tokens(last_amt) if last_amt else ""
    else:
        last_out_when = "UNKNOWN"
        last_out_fmt = ""

    if err or sent_raw is None:
        left_24h: float | None = None
        left_24h_fmt = "UNKNOWN"
    else:
        sent = float(sent_raw)
        if sent > 0:
            left_24h = sent
            left_24h_fmt = f"left {fmt_tokens(sent)}"
        else:
            left_24h = 0
            left_24h_fmt = "none left"

    dest = ""
    if last_out_status == "filled":
        dest = row.get("last_out_dest_tag") or row.get("last_dest") or ""
        if not dest and row.get("last_out_hops"):
            dest = _last_outbound_dest(row.get("last_out_hops") or [], watched, cex, mm)

    addr = row.get("wallet") or ""
    tag_l = (tag or "").lower()
    book = ""
    if addr in mm or "wintermute" in tag_l:
        book = "MM"
    elif addr in cex or any(w in tag_l for w in (
        "binance", "bybit", "gate", "okx", "coinbase", "kraken",
        "kucoin", "mexc", "bitget", "hyperunit",
    )):
        book = "CEX"
    if book and aug1_status not in ("proved", "unmoved_equals_now"):
        aug1_fmt = f"{book} book"

    return {
        "tag": tag,
        "book": book,
        "aug1": aug1,
        "aug1_status": aug1_status,
        "aug1_as_of": row.get("aug1_as_of"),
        "aug1_fmt": aug1_fmt,
        "balance": bal,
        "balance_fmt": balance_fmt,
        "left_24h": left_24h if left_24h is not None else 0,
        "left_24h_fmt": left_24h_fmt,
        "last_out_ts": last_ts,
        "last_out_when": last_out_when,
        "last_out_amount": last_amt if last_amt > 0 else 0,
        "last_out_fmt": last_out_fmt,
        "last_out_status": last_out_status,
        "last_out_dest_tag": dest,
        "dest": dest,
        "error": err,
        "now_prev": row.get("now_prev"),
        "now_as_of": row.get("now_as_of"),
        "now_chg_fmt": row.get("now_chg_fmt") or "",
    }


def check_wallet(
    address: str, mint: str, watched: set[str], gte_time: int, cex: dict[str, str], mm: dict[str, str]
) -> dict[str, Any]:
    balance = _token_balance(address, mint)
    time.sleep(0.28)
    sigs, reached_aug1 = _page_signatures(address)
    sent = received = 0.0
    hops: list[str] = []
    last_out_amt = 0.0
    last_out_ts: int | None = None
    last_out_hops: list[str] = []
    mint_after: list[tuple[int, dict[str, Any]]] = []
    for s in sigs:
        ts = int(s.get("blockTime") or 0)
        if ts and ts < AUG1:
            continue
        sig = s.get("signature")
        if not sig:
            continue
        tx = _rpc_retry(
            "getTransaction",
            [sig, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}],
        )
        time.sleep(0.28)
        ds, dr, dh = _tx_mint_delta(tx, address, mint)
        if ds > 0 and last_out_ts is None:
            last_out_amt = ds
            last_out_ts = ts or None
            last_out_hops = list(dh)
        if ts >= gte_time:
            sent += ds
            received += dr
            hops.extend(dh)
        if ds > 0 or dr > 0:
            mint_after.append((ts, tx))

    if last_out_ts is not None:
        last_out_status = "filled"
    elif reached_aug1:
        last_out_status = "none_since_aug1"
        last_out_amt = 0.0
    else:
        last_out_status = "unknown"

    aug1: float | None = None
    aug1_status = "unknown"
    aug1_as_of: str | None = None
    if balance is None:
        aug1 = None
        aug1_status = "unknown"
    elif reached_aug1 and mint_after:
        earliest = min(mint_after, key=lambda x: x[0] or 10**18)
        pre = _pre_mint_amount(earliest[1], address, mint)
        if pre is None:
            aug1 = None
            aug1_status = "unknown"
        else:
            aug1 = pre
            aug1_status = "proved"
            aug1_as_of = AUG1_ISO
    elif reached_aug1:
        aug1 = balance
        aug1_status = "unmoved_equals_now"
        aug1_as_of = AUG1_ISO
    else:
        aug1 = None
        aug1_status = "unknown"

    seen_h: set[str] = set()
    uniq: list[str] = []
    for h in hops:
        if h in watched or h in seen_h:
            continue
        seen_h.add(h)
        uniq.append(h)
    last_dest = _last_outbound_dest(last_out_hops, watched, cex, mm) if last_out_status == "filled" else ""
    sent_dest = _last_outbound_dest(uniq, watched, cex, mm) if sent > 0 else ""
    if sent <= 0 and received <= 0:
        status = "still sitting"
        line = "still sitting"
    else:
        bits = []
        if sent > 0:
            bits.append(f"sent {fmt_tokens(sent)}")
        if received > 0 and sent <= 0:
            bits.append(f"received {fmt_tokens(received)}")
        if sent > 0:
            if sent_dest:
                bits.append(f"dest {sent_dest}")
            else:
                bits.append("dest unread")
        status = "moved"
        line = " · ".join(bits)
        if sent <= 0 and received > 0:
            status = "received"
    out: dict[str, Any] = {
        "wallet": address,
        "status": status,
        "line": line,
        "sent": sent,
        "received": received,
        "new_hops": uniq,
        "balance": balance,
        "aug1": aug1,
        "aug1_status": aug1_status,
        "last_transfer_amount": last_out_amt,
        "last_transfer_ts": last_out_ts,
        "last_out_amount": last_out_amt,
        "last_out_ts": last_out_ts,
        "last_out_status": last_out_status,
        "last_out_dest_tag": last_dest,
        "last_dest": last_dest,
        "sent_dest": sent_dest,
        "error": None,
    }
    if aug1_as_of:
        out["aug1_as_of"] = aug1_as_of
    return out


def coin_summary(
    coin: str,
    rows: list[dict[str, Any]],
    watched: set[str],
    cex: dict[str, str],
    mm: dict[str, str],
) -> str:
    n = len(rows)
    if n == 0:
        return ""
    loud_rows = [r for r in rows if _is_loud_row(r, watched, cex, mm)]
    if loud_rows:
        total = sum(float(r.get("sent") or 0) for r in loud_rows)
        return f"{len(loud_rows)} to MM/CEX · {fmt_tokens(total)} {coin}"
    return f"{n} watched · no MM/CEX send"


def run_check() -> dict[str, Any]:
    wallets = load_wallets()
    tags = load_tags()
    cex, mm = _load_dest_tags()
    gte = yesterday_start_unix()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    coins_out: dict[str, Any] = {}
    errors: list[str] = []
    for coin in COINS:
        addrs = wallets[coin]
        mint = MINTS.get(coin)
        watched = set(addrs)
        rows: list[dict[str, Any]] = []
        if not addrs:
            coins_out[coin] = {
                "wallets": [],
                "summary": "",
                "loud": False,
                "popup": [],
                "boxes": [],
            }
            continue
        if not mint:
            raise RuntimeError(f"no mint for {coin}")
        for i, addr in enumerate(addrs, 1):
            print(f"siren {coin} {i}/{len(addrs)}", flush=True)
            try:
                row = check_wallet(addr, mint, watched, gte, cex, mm)
            except Exception as e:
                if "429" in str(e):
                    raise RuntimeError(f"429 abort at {coin} {addr}: {e}") from e
                row = {
                    "wallet": addr,
                    "status": "error",
                    "line": f"error {e}",
                    "sent": None,
                    "received": None,
                    "new_hops": [],
                    "balance": None,
                    "aug1": None,
                    "aug1_status": "unknown",
                    "last_transfer_amount": 0.0,
                    "last_transfer_ts": None,
                    "last_out_amount": 0.0,
                    "last_out_ts": None,
                    "last_out_status": "unknown",
                    "last_out_dest_tag": "",
                    "last_dest": "",
                    "sent_dest": "",
                    "error": str(e),
                }
                errors.append(f"{coin} {addr}: {e}")
            rows.append(row)
            time.sleep(0.28)
        if len(rows) != len(addrs):
            raise RuntimeError(f"{coin} skipped wallets: {len(addrs)} listed {len(rows)} logged")
        summary = coin_summary(coin, rows, watched, cex, mm)
        loud = _coin_loud(rows, watched, cex, mm)
        coin_tags = tags.get(coin) or {}
        sorted_rows = sorted(
            rows,
            key=lambda r: (
                0 if (float(r.get("sent") or 0) > 0) else 1,
                -(float(r.get("sent") or 0)),
            ),
        )
        boxes = [
            wallet_to_box(
                r,
                coin_tags.get(r["wallet"]) or "NeedTag",
                cex,
                mm,
                watched,
            )
            for r in sorted_rows
        ]
        coins_out[coin] = {
            "wallets": [
                {
                    "wallet": r["wallet"],
                    "line": r["line"],
                    "status": r["status"],
                    "sent": r["sent"],
                    "received": r["received"],
                    "new_hops": r["new_hops"],
                    "balance": r.get("balance"),
                    "aug1": r.get("aug1"),
                    "aug1_status": r.get("aug1_status") or "unknown",
                    "aug1_as_of": r.get("aug1_as_of"),
                    "last_transfer_ts": r.get("last_transfer_ts"),
                    "last_transfer_amount": r.get("last_transfer_amount"),
                    "last_out_ts": r.get("last_out_ts"),
                    "last_out_amount": r.get("last_out_amount"),
                    "last_out_status": r.get("last_out_status") or "unknown",
                    "last_out_dest_tag": r.get("last_out_dest_tag") or "",
                    "last_dest": r.get("last_dest"),
                    "sent_dest": r.get("sent_dest"),
                    "error": r.get("error"),
                }
                for r in sorted_rows
            ],
            "boxes": boxes,
            "summary": summary,
            "loud": loud,
            "popup": [f"{b['tag']} · {r['line']}" for b, r in zip(boxes, sorted_rows)],
        }
    out = {
        "as_of": now,
        "since": gte,
        "coins": coins_out,
        "errors": errors,
    }
    persist_bundle(out)
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    day_dir = ROOT / "reports" / day / "siren-watch"
    day_dir.mkdir(parents=True, exist_ok=True)
    (day_dir / "siren-watch.json").write_text(json.dumps(out, indent=2) + "\n")
    lines = [f"siren-watch {now} since {gte}"]
    for coin in COINS:
        c = coins_out[coin]
        coin_tags = tags.get(coin) or {}
        lines.append(f"== {coin} summary: {c['summary'] or '(blank)'} loud={c.get('loud')}")
        for row in c["wallets"]:
            tag = coin_tags.get(row["wallet"]) or "?"
            lines.append(f"  {tag} · {row['line']}")
        if not c["wallets"]:
            lines.append("  (empty list)")
    (day_dir / "siren-watch.log").write_text("\n".join(lines) + "\n")
    return out


def _enrich_bundle_boxes(bundle: dict[str, Any]) -> dict[str, Any]:
    tags = load_tags()
    cex, mm = _load_dest_tags()
    wallets_cfg = load_wallets()
    coins = bundle.get("coins") or {}
    out: dict[str, Any] = {}
    for coin in COINS:
        c = dict(coins.get(coin) or {})
        addrs = wallets_cfg.get(coin) or []
        rows_by_wallet = {r["wallet"]: r for r in (c.get("wallets") or [])}
        ordered = sorted(
            addrs,
            key=lambda a: -float(rows_by_wallet.get(a, {}).get("balance") or 0),
        )
        rows: list[dict[str, Any]] = []
        watched = set(addrs)
        for addr in ordered:
            if addr in rows_by_wallet:
                r = dict(rows_by_wallet[addr])
                if not r.get("sent_dest") and float(r.get("sent") or 0) > 0:
                    r["sent_dest"] = _last_outbound_dest(
                        r.get("new_hops") or [], watched, cex, mm
                    )
                rows.append(r)
            else:
                rows.append(
                    {
                        "wallet": addr,
                        "status": "still sitting",
                        "line": "still sitting",
                        "sent": 0.0,
                        "received": 0.0,
                        "new_hops": [],
                        "balance": None,
                        "aug1": None,
                        "aug1_status": "unknown",
                        "last_transfer_ts": None,
                        "last_transfer_amount": 0.0,
                        "last_out_ts": None,
                        "last_out_amount": 0.0,
                        "last_out_status": "unknown",
                        "last_out_dest_tag": "",
                        "last_dest": "",
                        "sent_dest": "",
                        "error": None,
                    }
                )
        watched = set(addrs)
        coin_tags = tags.get(coin) or {}
        c["boxes"] = [
            wallet_to_box(
                r,
                coin_tags.get(r["wallet"]) or "NeedTag",
                cex,
                mm,
                watched,
            )
            for r in rows
        ]
        if rows:
            c["wallets"] = rows
        c["loud"] = _coin_loud(rows, watched, cex, mm)
        c["summary"] = coin_summary(coin, rows, watched, cex, mm)
        tracked = 0.0
        for r in rows:
            try:
                tracked += float(r.get("balance") or 0)
            except Exception:
                pass
        c["tracked"] = tracked
        c["tracked_fmt"] = fmt_tokens(tracked)
        supply = c.get("supply")
        try:
            supply_f = float(supply) if supply is not None else None
        except Exception:
            supply_f = None
        c["supply_fmt"] = fmt_tokens(supply_f) if supply_f is not None else ""
        if c["supply_fmt"]:
            c["cover_fmt"] = f'{c["supply_fmt"]} / {c["tracked_fmt"]}'
        else:
            c["cover_fmt"] = c["tracked_fmt"]
        out[coin] = c
    bundle = dict(bundle)
    bundle["coins"] = out
    return bundle


SIREN_BOX_JS = """
  document.addEventListener('click', function (e) {
    var ico = e.target.closest('.hold-siren-ico.has-watch');
    if (!ico) return;
    e.preventDefault();
    e.stopPropagation();
    var key = ico.getAttribute('data-siren-key');
    var el = document.getElementById('siren-watch-data');
    var all = {};
    try { all = JSON.parse(el && el.textContent || '{}'); } catch (err) { all = {}; }
    var coin = all[key] || {};
    var boxes = coin.boxes || [];
    var modal = document.getElementById('stance-modal');
    var body = document.getElementById('stance-modal-body');
    var title = document.getElementById('stance-modal-title');
    if (!modal || !body) return;
    if (title) {
      function esc(s) { return String(s || '').replace(/</g,'&lt;'); }
      var circ = coin.supply_fmt ? esc(coin.supply_fmt) : '';
      var tracked = coin.tracked_fmt ? esc(coin.tracked_fmt) : '';
      var bits = '';
      if (circ) bits += '<span class="siren-watch-num">' + circ + '</span><span class="siren-watch-unit"> CIRC.</span>';
      if (circ && tracked) bits += '<span class="siren-watch-gap"></span>';
      if (tracked) bits += '<span class="siren-watch-num">' + tracked + '</span><span class="siren-watch-unit"> TRACKED</span>';
      title.innerHTML = '<span>' + (key || 'WATCH') + ' WATCH</span>' +
        (bits ? '<span class="siren-watch-cover">' + bits + '</span>' : '');
    }
    if (!boxes.length) {
      body.innerHTML = '<p class="stance-p">No watch data for this coin yet.</p>';
    } else {
      body.innerHTML = '<div class="siren-watch-grid">' + boxes.map(function (b) {
        var cls = 'siren-watch-box';
        if ((b.left_24h || 0) > 0 && b.left_24h_fmt !== 'UNKNOWN') cls += ' is-moved';
        if (b.book === 'CEX' || b.book === 'MM') cls += ' is-desk';
        var tag = String(b.tag || 'NeedTag');
        if (b.book === 'CEX' || b.book === 'MM') tag = tag + ' · ' + b.book;
        var aug1 = (b.book === 'CEX' || b.book === 'MM')
          ? (b.aug1_fmt || (b.book + ' book'))
          : ((b.aug1_fmt && b.aug1_status && b.aug1_status !== 'unknown') ? b.aug1_fmt : 'UNKNOWN');
        var nowv = (b.balance_fmt && b.balance_fmt !== '—') ? b.balance_fmt : 'UNKNOWN';
        var latest;
        if (b.last_out_status === 'none_since_aug1' || b.last_out_when === 'none since 1 Aug') {
          latest = 'none since 1 Aug';
        } else if (b.last_out_status === 'filled' && b.last_out_when && b.last_out_when !== 'UNKNOWN') {
          latest = b.last_out_when + (b.last_out_fmt ? ' · ' + b.last_out_fmt : '');
        } else {
          latest = 'UNKNOWN';
        }
        var left = b.left_24h_fmt || 'UNKNOWN';
        var dest = b.dest ? '<span class="siren-box-row siren-box-dest">dest ' + String(b.dest).replace(/</g,'&lt;') + '</span>' : '';
        return '<div class="' + cls + '">' +
          '<span class="siren-box-tag">' + tag.replace(/</g,'&lt;') + '</span>' +
          '<span class="siren-box-row">1 Aug <span class="siren-box-val">' + String(aug1).replace(/</g,'&lt;') + '</span></span>' +
          '<span class="siren-box-row">now <span class="siren-box-val">' + String(nowv).replace(/</g,'&lt;') + '</span></span>' +
          (b.now_chg_fmt ? '<span class="siren-box-row">since last <span class="siren-box-val">' + String(b.now_chg_fmt).replace(/</g,'&lt;') + '</span></span>' : '') +
          '<span class="siren-box-row">latest out <span class="siren-box-val">' + String(latest).replace(/</g,'&lt;') + '</span></span>' +
          '<span class="siren-box-row">last 24h <span class="siren-box-val">' + String(left).replace(/</g,'&lt;') + '</span></span>' +
          dest + '</div>';
      }).join('') + '</div>';
    }
    modal.hidden = false;
    document.body.classList.add('stance-modal-open');
  }, true);
"""

SIREN_BOX_CSS = """
.siren-watch-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(9.5rem, 1fr));
  gap: 0.55rem;
}
.siren-watch-box {
  border: 1px solid var(--edge, #2a2d38);
  border-radius: 0.35rem;
  padding: 0.45rem 0.5rem;
  font-size: 0.58rem;
  line-height: 1.35;
}
.siren-watch-box.is-moved { border-color: #c47a7a; }
.siren-watch-box.is-desk { border-color: #6a8aaa; }
.stance-modal-title { display: flex; align-items: baseline; gap: 0.8rem; flex-wrap: wrap; }
.siren-watch-cover { display: inline-flex; align-items: baseline; flex-wrap: wrap; gap: 0.15rem 0.2rem; letter-spacing: 0; text-transform: none; }
.siren-watch-num { font-family: var(--display); font-size: 1.2rem; font-weight: 700; color: var(--ink); line-height: 1; }
.siren-watch-unit { font-family: var(--display); font-size: 0.6rem; font-weight: 500; color: var(--muted); letter-spacing: 0.06em; }
.siren-watch-gap { width: 0.7rem; }
.siren-box-kind { color: #6a8aaa; }
.siren-box-tag {
  display: block;
  font-weight: 700;
  font-size: 0.62rem;
  margin-bottom: 0.28rem;
  color: var(--ink);
}
.siren-box-row { display: block; color: var(--muted); margin-top: 0.12rem; }
.siren-box-val { color: var(--ink); }
.siren-box-dest { color: var(--muted); margin-top: 0.15rem; }
"""


def persist_bundle(bundle: dict[str, Any], stamp_index: bool = False) -> None:
    """Atomic cache write. Never replace last-good with an empty object."""
    if not isinstance(bundle, dict) or not (bundle.get("coins") or {}):
        raise RuntimeError("refuse to persist empty siren bundle")
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CACHE_PATH.with_name("siren-watch.json.tmp")
    tmp.write_text(json.dumps(bundle, indent=2) + "\n")
    tmp.replace(CACHE_PATH)
    if stamp_index:
        apply_index(bundle)


def apply_index(bundle: dict[str, Any] | None = None) -> None:
    if bundle is None:
        if not CACHE_PATH.exists():
            bundle = {
                "coins": {k: {"summary": "", "loud": False, "popup": [], "wallets": [], "boxes": []} for k in COINS}
            }
        else:
            bundle = json.loads(CACHE_PATH.read_text())
    bundle = _enrich_bundle_boxes(bundle)
    wallets_cfg = load_wallets()
    from lib.v3.write_guard import refuse_frozen_v3_live_write

    refuse_frozen_v3_live_write(INDEX)
    html = INDEX.read_text()
    marker = ".hold-siren-ico.is-on { animation: siren-pulse 1.35s ease-in-out infinite; }"
    if ".hold-siren-ico.has-watch" not in html:
        html = html.replace(
            marker,
            marker + "\n.hold-siren-ico.has-watch { pointer-events: auto; cursor: pointer; }",
            1,
        )
    if ".siren-watch-grid" not in html:
        html = html.replace(
            ".hold-siren-ico.has-watch { pointer-events: auto; cursor: pointer; }",
            ".hold-siren-ico.has-watch { pointer-events: auto; cursor: pointer; }" + SIREN_BOX_CSS,
            1,
        )

    import re

    payload = json.dumps(bundle.get("coins") or {}, separators=(",", ":"))
    blob = f'<script type="application/json" id="siren-watch-data">{payload}</script>'
    html = re.sub(
        r'<script type="application/json" id="siren-watch-data">.*?</script>\n?',
        "",
        html,
        count=1,
        flags=re.S,
    )
    html = html.replace('<div id="stance-modal"', blob + "\n<div id=\"stance-modal\"", 1)

    needle = (
        "  document.querySelectorAll('.hold').forEach(function (btn) {\n"
        "    btn.addEventListener('click', function () {\n"
        "      var slug = btn.getAttribute('data-asset-slug');"
    )
    repl = (
        "  document.querySelectorAll('.hold').forEach(function (btn) {\n"
        "    btn.addEventListener('click', function (e) {\n"
        "      if (e.target.closest('.hold-siren-ico')) return;\n"
        "      var slug = btn.getAttribute('data-asset-slug');"
    )
    if "e.target.closest('.hold-siren-ico')" not in html:
        if needle not in html:
            raise RuntimeError("hold click handler not found")
        html = html.replace(needle, repl, 1)

    html = re.sub(
        r"  document\.addEventListener\('click', function \(e\) \{\n"
        r"    var ico = e\.target\.closest\('\.hold-siren-ico\.has-watch'\);[\s\S]*?"
        r"  \}, true\);\n",
        "",
        html,
    )
    html = html.replace(
        "  document.addEventListener('click', function (e) {\n    var btn = e.target.closest('.stance-see-more');",
        SIREN_BOX_JS + "\n  document.addEventListener('click', function (e) {\n    var btn = e.target.closest('.stance-see-more');",
        1,
    )
    INDEX.write_text(html)
