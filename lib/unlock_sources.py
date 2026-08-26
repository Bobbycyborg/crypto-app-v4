"""Fetch PUMP unlock schedule from Tokenomics + DefiLlama public pages."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone

import certifi
import requests

TOKENOMICS_URL = "https://app.tokenomics.com/tokenomics/pump-fun/unlocks"
DEFILLAMA_URL = "https://defillama.com/unlocks/pump"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://defillama.com/",
}


def _fetched_at() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_tokenomics_unlocks() -> dict:
    fetched = _fetched_at()
    r = requests.get(TOKENOMICS_URL, headers=HEADERS, timeout=45, verify=certifi.where())
    r.raise_for_status()
    m = re.search(r'\\"Date\\":\[(.*?)\],\\"Token Amount\\":\[(.*?)\]', r.text, re.S)
    if not m:
        return {
            "source": "tokenomics.com",
            "url": TOKENOMICS_URL,
            "fetched_at": fetched,
            "status": "PARSE_FAILED",
            "events": [],
        }

    dates_raw = [d.strip().strip('"').replace('\\"', "").replace("\\", "") for d in m.group(1).split(",")]
    amounts = [float(x) for x in m.group(2).split(",")]
    dates = [d for d in dates_raw if re.match(r"^\d{2}/\d{2}/\d{4}$", d)]
    # Amount array is the canonical 48-event schedule; pair by index with first date series.
    events = []
    for d, a in zip(dates[: len(amounts)], amounts):
        iso = datetime.strptime(d, "%m/%d/%Y").strftime("%Y-%m-%d")
        events.append({"date": iso, "date_display": d, "amount_tokens": a})
    events.sort(key=lambda e: e["date"])

    return {
        "source": "tokenomics.com",
        "url": TOKENOMICS_URL,
        "fetched_at": fetched,
        "status": "OK",
        "events": events,
    }


def fetch_defillama_unlocks() -> dict:
    fetched = _fetched_at()
    r = requests.get(DEFILLAMA_URL, headers=HEADERS, timeout=45, verify=certifi.where())
    r.raise_for_status()
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
    if not m:
        return {
            "source": "defillama.com",
            "url": DEFILLAMA_URL,
            "fetched_at": fetched,
            "status": "PARSE_FAILED",
            "events": [],
        }

    data = json.loads(m.group(1))
    emissions = data["props"]["pageProps"]["emissions"]
    events = []
    for e in emissions.get("events", []):
        ts = int(e["timestamp"])
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        tokens = e.get("noOfTokens") or []
        amount = float(sum(tokens)) if tokens else None
        events.append(
            {
                "timestamp_utc": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "date": dt.strftime("%Y-%m-%d"),
                "amount_tokens": amount,
                "category": e.get("category"),
                "unlock_type": e.get("unlockType"),
                "description": e.get("description"),
            }
        )

    upcoming = emissions.get("upcomingEvent") or []
    unlock_events = emissions.get("meta", {}).get("unlockEvents") or []

    return {
        "source": "defillama.com",
        "url": DEFILLAMA_URL,
        "fetched_at": fetched,
        "status": "OK",
        "events": events,
        "upcoming_event": upcoming,
        "unlock_events": [
            {
                "timestamp_utc": datetime.fromtimestamp(
                    int(u["timestamp"]), tz=timezone.utc
                ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "cliff_allocations": u.get("cliffAllocations", []),
                "summary": u.get("summary", {}),
            }
            for u in unlock_events
        ],
    }


def reconcile_august_unlock(tokenomics: dict, defillama: dict) -> dict:
    aug12 = "2026-08-12"
    tok = next((e for e in tokenomics.get("events", []) if e["date"] == aug12), None)
    dl_events = [
        e
        for e in defillama.get("events", [])
        if e.get("date") == aug12 or e.get("timestamp_utc", "").startswith(aug12)
    ]
    dl_upcoming = defillama.get("upcoming_event") or []
    dl_aug = []
    for e in dl_upcoming:
        ts = int(e.get("timestamp", 0))
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        if dt.strftime("%Y-%m-%d") == aug12:
            dl_aug.append(e)
    dl_team = sum(float(x) for e in dl_aug for x in e.get("noOfTokens", []) if e.get("category") == "insiders")
    dl_total = sum(float(x) for e in dl_aug for x in e.get("noOfTokens", []))

    # DefiLlama upcoming splits team + investors at 05:00 UTC
    dl_team_amt = None
    dl_inv_amt = None
    for e in dl_aug:
        for n in e.get("noOfTokens", []):
            if "Team" in e.get("description", ""):
                dl_team_amt = float(n)
            elif "Investors" in e.get("description", ""):
                dl_inv_amt = float(n)

    return {
        "date": aug12,
        "tokenomics_amount_tokens": tok["amount_tokens"] if tok else None,
        "tokenomics_fetched_at": tokenomics.get("fetched_at"),
        "tokenomics_url": tokenomics.get("url"),
        "defillama_total_tokens": dl_total if dl_aug else None,
        "defillama_team_tokens": dl_team_amt,
        "defillama_investor_tokens": dl_inv_amt,
        "defillama_fetched_at": defillama.get("fetched_at"),
        "defillama_url": defillama.get("url"),
        "discrepancy_note": (
            "Tokenomics and DefiLlama August amounts differ; "
            "SCHEDULED not equal to DISTRIBUTED."
        )
        if tok and dl_total and abs(tok["amount_tokens"] - dl_total) > 1
        else None,
    }
