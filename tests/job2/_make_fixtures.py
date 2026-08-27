"""Build minimal Job 2 replay fixtures. Run once."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "tests/job2/fixtures/replay/raw"
RAW.mkdir(parents=True, exist_ok=True)


def meta(request_key: str, source_key: str, url: str, body: bytes, content_type: str) -> None:
    stem = request_key.replace("/", "_")
    (RAW / f"{stem}.body").write_bytes(body)
    payload = {
        "source_key": source_key,
        "request_key": request_key,
        "url": url,
        "params": None,
        "http_status": 200,
        "fetched_at": "2026-08-26T12:00:00Z",
        "content_type": content_type,
        "body_sha256": hashlib.sha256(body).hexdigest(),
        "raw_body_path": f"{stem}.body",
        "attempts": 1,
    }
    (RAW / f"{stem}.meta.json").write_text(json.dumps(payload, indent=2) + "\n")


def j(request_key, source_key, url, obj):
    body = json.dumps(obj).encode()
    meta(request_key, source_key, url, body, "application/json")


cg = []
for cid, px, ch7, ch30, ch90, ath_ch, circ, mx, vol, mcap in [
    ("bitcoin", 100000, 1.5, 3.0, 9.0, -20.0, 19800000, 21000000, 1e9, 2e12),
    ("solana", 90, 2.0, 4.0, 8.0, -30.0, 5e8, None, 2e8, 4.5e10),
    ("render-token", 1.5, 1.0, 2.0, 3.0, -40.0, 5e8, 644245094, 1e7, 7.5e8),
    ("pump-fun", 0.004, 5.0, 10.0, 20.0, -50.0, 3.5e11, 1e12, 5e6, 1.4e9),
    ("io", 0.14, -1.0, -2.0, -3.0, -80.0, 2e8, 8e8, 1e6, 2.8e7),
    ("nosana", 0.3, 1.0, 2.0, 3.0, -70.0, 8.3e7, 1e8, 5e5, 2.5e7),
    ("fartcoin", 0.18, 3.0, 6.0, 12.0, -60.0, 1e9, 1e9, 8e6, 1.8e8),
    ("spx6900", 0.43, 4.0, 8.0, 16.0, -55.0, 9.3e8, 1e9, 3e6, 4e8),
    ("zcash", 40, 1.0, 2.0, 3.0, -10.0, 1.6e7, 2.1e7, 4e7, 6.4e8),
    ("hyperliquid", 74, 2.0, 4.0, 6.0, -15.0, 2.7e8, 1e9, 9e7, 2e10),
]:
    cg.append(
        {
            "id": cid,
            "symbol": cid[:3],
            "current_price": px,
            "market_cap": mcap,
            "total_volume": vol,
            "circulating_supply": circ,
            "max_supply": mx,
            "ath_change_percentage": ath_ch,
            "price_change_percentage_7d_in_currency": ch7,
            "price_change_percentage_30d_in_currency": ch30,
            "price_change_percentage_90d_in_currency": ch90,
            "last_updated": "2026-08-26T12:00:00.000Z",
        }
    )
j("coingecko.markets.active", "coingecko", "https://api.coingecko.com/api/v3/coins/markets", cg)

j(
    "alternative_me.fng",
    "alternative_me",
    "https://api.alternative.me/fng/?limit=1",
    {"name": "Fear and Greed Index", "data": [{"value": "74", "value_classification": "Greed", "timestamp": "1756204800"}]},
)

def klines(start_close: float, n: int, step: float, start: datetime):
    rows = []
    px = start_close
    for i in range(n):
        ts = int((start + timedelta(days=i)).timestamp() * 1000)
        rows.append([ts, str(px), str(px + 1), str(px - 1), str(px), "1", ts, "1", 1, "1", "1", "0"])
        px += step
    return rows

start = datetime(2026, 4, 1, tzinfo=timezone.utc)
# 40 days: BTC 100 → +0.25/day so day 0=100, day 39=109.75; 7d return uses [-1] vs [-8]
j("binance.spot.klines.BTCUSDT.1d", "binance", "https://api.binance.com/api/v3/klines", klines(100, 250, 0.25, start))
j("binance.spot.klines.SOLUSDT.1d", "binance", "https://api.binance.com/api/v3/klines", klines(80, 250, 0.2, start))
j("binance.spot.klines.PUMPUSDT.1d", "binance", "https://api.binance.com/api/v3/klines", klines(0.003, 250, 0.00002, start))

# July 2026 lows: include July rows with low=50000
july = []
for d in range(1, 32):
    dt = datetime(2026, 7, d, tzinfo=timezone.utc)
    low = 50000 + d
    if d == 15:
        low = 48000
    ts = int(dt.timestamp() * 1000)
    july.append([ts, "60000", "61000", str(low), "60000", "1", ts, "1", 1, "1", "1", "0"])
# prepend before June series? july_min uses year/month filter on whatever is in the file.
# The BTC klines file is June start — add July onto BTC file instead.
btc = klines(100, 250, 0.25, start) + july
j("binance.spot.klines.BTCUSDT.1d", "binance", "https://api.binance.com/api/v3/klines", btc)

for sym, fund, oi, last, qvol in [
    ("BTCUSDT", "0.0001", "10000", "100000", "9000000000"),
    ("SOLUSDT", "0.00005", "20000", "90", "800000000"),
    ("PUMPUSDT", "0.0002", "5000000", "0.004", "20000000"),
    ("RENDERUSDT", "0.00003", "1000", "1.5", "15000000"),
    ("FARTCOINUSDT", "0.0004", "800000", "0.18", "30000000"),
    ("SPXUSDT", "0.0001", "200000", "0.43", "12000000"),
    ("ZECUSDT", "-0.0001", "5000", "40", "25000000"),
]:
    j(f"binance.fapi.premiumIndex.{sym}", "binance", "https://fapi.binance.com/fapi/v1/premiumIndex", {"symbol": sym, "lastFundingRate": fund, "markPrice": last})
    if sym in {"BTCUSDT", "FARTCOINUSDT", "PUMPUSDT", "SPXUSDT", "ZECUSDT"}:
        j(f"binance.fapi.openInterest.{sym}", "binance", "https://fapi.binance.com/fapi/v1/openInterest", {"symbol": sym, "openInterest": oi})
    if sym in {"BTCUSDT", "FARTCOINUSDT", "PUMPUSDT", "SPXUSDT", "ZECUSDT"}:
        j(f"binance.fapi.ticker24h.{sym}", "binance", "https://fapi.binance.com/fapi/v1/ticker/24hr", {"symbol": sym, "lastPrice": last, "quoteVolume": qvol})

j("binance.spot.ticker24h.BTCUSDT", "binance", "https://api.binance.com/api/v3/ticker/24hr", {"symbol": "BTCUSDT", "lastPrice": "100000", "quoteVolume": "1000000000"})
j("binance.spot.ticker24h.PUMPUSDT", "binance", "https://api.binance.com/api/v3/ticker/24hr", {"symbol": "PUMPUSDT", "lastPrice": "0.004", "quoteVolume": "4000000"})
j("binance.spot.ticker24h.ZECUSDT", "binance", "https://api.binance.com/api/v3/ticker/24hr", {"symbol": "ZECUSDT", "lastPrice": "40", "quoteVolume": "5000000"})

chart7 = [[i, 1_000_000] for i in range(40)]
j("defillama.summary.fees.pump.fun.dailyRevenue", "defillama", "https://api.llama.fi/summary/fees/pump.fun", {"total24h": 1_000_000, "totalDataChart": chart7})
j("defillama.summary.fees.pump.fun.dailyHoldersRevenue", "defillama", "https://api.llama.fi/summary/fees/pump.fun", {"total24h": 800_000, "totalDataChart": [[i, 800_000] for i in range(40)]})
j("defillama.summary.fees.hyperliquid-perp.dailyFees", "defillama", "https://api.llama.fi/summary/fees/hyperliquid-perp", {"totalDataChart": [[i, 2_000_000] for i in range(40)]})
j("defillama.summary.fees.solana.dailyFees", "defillama", "https://api.llama.fi/summary/fees/solana", {"total24h": 500_000, "totalDataChart": [[i, 500_000] for i in range(40)]})
j("defillama.historicalChainTvl.Solana", "defillama", "https://api.llama.fi/v2/historicalChainTvl/Solana", [{"date": 1, "tvl": 4.8e9}, {"date": 2, "tvl": 5.65e9}])
j("defillama.stablecoinchains", "defillama", "https://stablecoins.llama.fi/stablecoinchains", [{"name": "Solana", "totalCirculatingUSD": {"peggedUSD": 15.91e9}}, {"name": "Ethereum", "totalCirculatingUSD": {"peggedUSD": 100e9}}])
j(
    "defillama.overview.fees",
    "defillama",
    "https://api.llama.fi/overview/fees",
    {
        "protocols": [
            {"slug": "pump.fun", "category": "Launchpad", "total24h": 80},
            {"slug": "other", "category": "Launchpad", "total24h": 20},
            {"slug": "aave", "category": "Lending", "total24h": 999},
        ]
    },
)

j(
    "hyperliquid.info.tokenDetails",
    "hyperliquid",
    "https://api.hyperliquid.xyz/info",
    {
        "name": "HYPE",
        "circulatingSupply": 222_450_000,
        "maxSupply": 1_000_000_000,
        "totalSupply": 1_000_000_000,
        "futureEmissions": 412_440_000,
        "nonCirculatingUserBalances": [
            ["0x43e9abea1910387c4292bca4b94de81462f8a251", 241_240_000],
            ["0xfefefefefefefefefefefefefefefefefefefefe", 46_370_000],
        ],
    },
)

j("io.clusters", "io_explorer", "https://api.io.solutions/v1/io-explorer/network/info/clusters", {"data": {"running_clusters": 42, "total_earnings": 27120000}})
j(
    "nosana.jobs.count",
    "nosana",
    "https://blockchain-indexer.k8s.prd.nos.ci/jobs/count",
    {
        "byState": {"RUNNING": 855, "QUEUED": 12, "COMPLETED": 500000},
        "last30Days": 119000,
        "distinctNodesWithRunningJobs": 35,
    },
)
j("render.supplyInfo", "render_foundation", "https://infra.shikumi.cc/api/v1/supplyInfo", {"circulatingSupply": 518_000_000, "maxSupply": 644_245_094})
j(
    "render.epochBurnStats",
    "render_foundation",
    "https://infra.shikumi.cc/api/v1/epochBurnStats",
    [
        {
            "id": i,
            "burnedRender": 1000,
            "nodeOperatorReward": 2000,
            "latest_node_operator_due": 2500 if i == 11 else 0,
        }
        for i in range(1, 12)
    ],
)
j("render.nodes_and_frames", "render_foundation", "https://stats.renderfoundation.com/api/nodes_and_frames", {"frames": 123456789, "nodes": 4000})
j("solana.rpc.getInflationRate", "solana_rpc", "https://api.mainnet-beta.solana.com", {"jsonrpc": "2.0", "result": {"total": 0.0368, "validator": 0.036, "foundation": 0.0008}, "id": 1})
j(
    "solana.rpc.getVoteAccounts",
    "solana_rpc",
    "https://api.mainnet-beta.solana.com",
    {"jsonrpc": "2.0", "result": {"current": [{"activatedStake": 1_000_000_000_000} for _ in range(3)], "delinquent": []}, "id": 1},
)
j(
    "solana.rpc.getRecentPerformanceSamples",
    "solana_rpc",
    "https://api.mainnet-beta.solana.com",
    {"jsonrpc": "2.0", "result": [{"numNonVoteTransactions": 6000, "numTransactions": 8000, "samplePeriodSecs": 60}], "id": 1},
)
j(
    "zcash.explorer.blockchain-info",
    "zcash_explorer",
    "https://mainnet.zcashexplorer.app/api/v1/blockchain-info",
    {
        "valuePools": [
            {"id": "transparent", "chainValue": 10},
            {"id": "sprout", "chainValue": 1},
            {"id": "sapling", "chainValue": 2},
            {"id": "orchard", "chainValue": 3},
            {"id": "ironwood", "chainValue": 4},
        ],
        "chainSupply": {"chainValue": 20},
        "transactions24h": 12345,
    },
)
j(
    "dexscreener.token.pump",
    "dexscreener",
    "https://api.dexscreener.com/latest/dex/tokens/pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn",
    {
        "pairs": [
            {
                "chainId": "solana",
                "baseToken": {"address": "pumpCmXqMfrsAkQ5r49WcJnRayYRqmXz6ae8H7H9Dfn"},
                "liquidity": {"usd": 17_700_000},
            }
        ]
    },
)

def farside(title, tickers, fname_key, url):
    heads = "".join(f"<th>{t}</th>" for t in tickers)
    rows = []
    for i, (d, tot) in enumerate([("26 Aug 2026", "10.0"), ("25 Aug 2026", "2.0"), ("24 Aug 2026", "1.0")] + [(f"{20-i:02d} Aug 2026", "0.5") for i in range(27)]):
        rows.append(f"<tr><td>{d}</td>" + "".join("<td>0.1</td>" for _ in tickers) + f"<td>{tot}</td></tr>")
    html = f"<html><head><title>{title} Flow – Farside</title></head><body><table><tr><th>Date</th>{heads}<th>Total</th></tr>{''.join(rows)}</table></body></html>"
    meta(fname_key, "farside", url, html.encode(), "text/html")

farside("Bitcoin ETF", ["IBIT", "FBTC", "GBTC"], "farside.html.btc", "https://farside.co.uk/btc/")
farside("Ethereum ETF", ["ETHA", "ETHE"], "farside.html.eth", "https://farside.co.uk/eth/")
farside("Solana ETF", ["BSOL", "VSOL"], "farside.html.sol", "https://farside.co.uk/sol/")

print("wrote", RAW)
