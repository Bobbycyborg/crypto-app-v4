"""Generate Phase B replay fixtures missing from base _make_fixtures.py."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "tests/job2/fixtures/replay/raw"
RAW.mkdir(parents=True, exist_ok=True)


def meta(request_key: str, source_key: str, url: str, body: bytes, content_type: str = "application/json") -> None:
    stem = request_key.replace("/", "_")
    (RAW / f"{stem}.body").write_bytes(body)
    payload = {
        "source_key": source_key,
        "request_key": request_key,
        "url": url,
        "params": None,
        "http_status": 200,
        "fetched_at": "2026-08-27T12:00:00Z",
        "content_type": content_type,
        "body_sha256": hashlib.sha256(body).hexdigest(),
        "raw_body_path": f"{stem}.body",
        "attempts": 1,
    }
    (RAW / f"{stem}.meta.json").write_text(json.dumps(payload, indent=2) + "\n")


def j(request_key, source_key, url, obj):
    meta(request_key, source_key, url, json.dumps(obj).encode())


def klines(start: float, n: int, step: float):
    start_dt = datetime(2026, 6, 1, tzinfo=timezone.utc)
    rows = []
    px = start
    for i in range(n):
        ts = int((start_dt + timedelta(days=i)).timestamp() * 1000)
        rows.append([ts, str(px), str(px + 1), str(px - 1), str(px), "1", ts, "1", 1, "1", "1", "0"])
        px += step
    return rows


# DefiLlama holders revenue
j(
    "defillama.overview.fees.dailyHoldersRevenue",
    "defillama",
    "https://api.llama.fi/overview/fees",
    {"protocols": [{"name": "Hyperliquid", "total30d": 43900000}, {"name": "Hyperliquid Perps", "total30d": 1}]},
)

j("defillama.overview.dexs.solana", "defillama", "https://api.llama.fi/overview/dexs/solana", {"total24h": 500000000, "total7d": 3000000000})
j("defillama.overview.dexs.ethereum", "defillama", "https://api.llama.fi/overview/dexs/ethereum", {"total24h": 2000000000, "total7d": 12000000000})
j("defillama.summary.fees.pump.fun.dailyFees", "defillama", "https://api.llama.fi/summary/fees/pump.fun", {"total24h": 1000000})
j("defillama.stablecoincharts.all", "defillama", "https://stablecoins.llama.fi/stablecoincharts/all", [{"name": "Solana", "totalCirculating": [[i, 15e9 + i * 1e6] for i in range(40)]}])

for sym, last, qv, oi in [
    ("HYPEUSDT", "74", "90000000", "1200000"),
    ("IOUSDT", "0.14", "5000000", "8000000"),
    ("RENDERUSDT", "1.5", "15000000", "1000000"),
    ("SOLUSDT", "90", "800000000", "20000000"),
    ("SPXUSDT", "0.43", "12000000", "200000"),
]:
    j(f"binance.fapi.ticker24h.{sym}", "binance", "https://fapi.binance.com/fapi/v1/ticker/24hr", {"symbol": sym, "lastPrice": last, "quoteVolume": qv})
    j(f"binance.fapi.openInterest.{sym}", "binance", "https://fapi.binance.com/fapi/v1/openInterest", {"symbol": sym, "openInterest": oi})

for sym in ["FARTCOINUSDT", "HYPEUSDT", "IOUSDT", "RENDERUSDT", "SOLUSDT", "SPXUSDT", "ZECUSDT"]:
    j(f"binance.fapi.klines.{sym}.1d", "binance", "https://fapi.binance.com/fapi/v1/klines", klines(1.0, 250, 0.01))

for sym in ["IOUSDT", "RENDERUSDT", "ZECUSDT"]:
    j(f"binance.spot.klines.{sym}.1d", "binance", "https://api.binance.com/api/v3/klines", klines(1.0, 220, 0.01))

for sym in ["IOUSDT", "RENDERUSDT", "SOLUSDT"]:
    j(f"binance.spot.ticker24h.{sym}", "binance", "https://api.binance.com/api/v3/ticker/24hr", {"symbol": sym, "lastPrice": "1", "quoteVolume": "1000000"})

j("binance.spot.tickerPrice.BONKUSDT", "binance", "https://api.binance.com/api/v3/ticker/price", {"symbol": "BONKUSDT", "price": "0.00001"})
j("binance.spot.tickerPrice.ORCAUSDT", "binance", "https://api.binance.com/api/v3/ticker/price", {"symbol": "ORCAUSDT", "price": "2.1"})
j("binance.fapi.fundingRate.SOLUSDT", "binance", "https://fapi.binance.com/fapi/v1/fundingRate", [{"symbol": "SOLUSDT", "fundingRate": "0.0001"} for _ in range(10)])

latest_ts = 1_700_000_000_000
day = 86400000
oi_hist = []
for i in range(31):
    ts = latest_ts - (30 - i) * day
    oi = 2000000 if i < 30 else 3000000
    oi_hist.append({"symbol": "SPXUSDT", "sumOpenInterestValue": str(oi), "timestamp": ts})
j("binance.fapi.openInterestHist.SPXUSDT.1d", "binance", "https://fapi.binance.com/futures/data/openInterestHist", oi_hist)
j("coingecko.market_charts.breadth_bundle", "coingecko", "file://local", json.loads((ROOT / "tests/job2/fixtures/local/breadth_market_charts.json").read_text()))

btc_oi = []
for i in range(31):
    ts = latest_ts - (30 - i) * day
    oi = 9000000000 if i < 30 else 9500000000
    btc_oi.append({"symbol": "BTCUSDT", "sumOpenInterestValue": str(oi), "timestamp": ts})
j("binance.fapi.openInterestHist.BTCUSDT.1d", "binance", "https://fapi.binance.com/futures/data/openInterestHist", btc_oi)

j("coinbase.spot.stats.FARTCOIN-USD", "coinbase", "https://api.exchange.coinbase.com/products/FARTCOIN-USD/stats", {"volume_30day": "1000000", "quote_24h": "500000"})

j("coingecko.market_chart.nosana", "coingecko", "https://api.coingecko.com/api/v3/coins/nosana/market_chart", {"prices": [[i * 86400000, 0.3 + i * 0.001] for i in range(260)]})

for coin, start_px, step in [("bitcoin", 60000, 50), ("fartcoin", 0.5, 0.002)]:
    prices = [[i * 86400000, start_px + i * step] for i in range(120)]
    j(
        f"coingecko.market_chart.{coin}.90d",
        "coingecko",
        f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart",
        {"prices": prices},
    )

fee_chart = [[latest_ts - (34 - i) * day, 1_000_000 + i * 10_000] for i in range(35)]
j(
    "defillama.summary.fees.hyperliquid.dailyFees",
    "defillama",
    "https://api.llama.fi/summary/fees/hyperliquid",
    {"totalDataChart": fee_chart, "total24h": 1_350_000},
)

j("nosana.jobs.timestamps_hours", "nosana", "https://blockchain-indexer.k8s.prd.nos.ci/jobs/stats/timestamps-hours", {"total": 420000})

j("hyperliquid.info.metaAndAssetCtxs", "hyperliquid", "https://api.hyperliquid.xyz/info", [
    {"universe": [{"name": "HYPE"}, {"name": "BTC"}]},
    [{"openInterest": "1000", "markPx": "74", "dayNtlVlm": "50000000"}, {"openInterest": "10", "markPx": "100000", "dayNtlVlm": "1000000"}],
])
j("hyperliquid.info.validatorSummaries", "hyperliquid", "https://api.hyperliquid.xyz/info", [{"stake": "50000000000000000"}])

j("io.inventory", "io_explorer", "https://api.io.solutions/v1/io-explorer/network/inventory-aggregated", {"data": {"total": 125000}})
j(
    "io.total_earnings_summary",
    "io_explorer",
    "https://api.io.solutions/v1/io-explorer/network/info/cluster/total-earnings-summary",
    {"data": [{"daily_earnings": 10000 + i * 100, "total_earnings": 27120000} for i in range(40)]},
)
j("io.clusters", "io_explorer", "https://api.io.solutions/v1/io-explorer/network/info/clusters", {"data": {"running_clusters": 42, "total_earnings": 27120000, "gpu_hours_last_30d": 1200000}})

j("nosana.stats", "nosana", "https://blockchain-indexer.k8s.prd.nos.ci/stats", {"nosStaked": 75000000, "maxSupply": 100000000, "gpu_hours_window_total": 420000})
j("nosana.jobs.stats", "nosana", "https://blockchain-indexer.k8s.prd.nos.ci/jobs/stats", {"last30Days": 119000, "usdReward": 8500000})

j(
    "render.liabilityEpochs",
    "render_foundation",
    "https://infra.shikumi.cc/api/v1/liabilityEpochs",
    [{"nodeOperatorReward": 1500, "burnedRender": 800} for _ in range(12)],
)

for token, mint in [
    ("2z", "2z"),
    ("fartcoin", "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump"),
    ("giga", "giga"),
    ("lockin", "lockin"),
    ("retardio", "retardio"),
]:
    liq = 4200000 if token == "fartcoin" else 1000000
    j(
        f"dexscreener.token.{token}",
        "dexscreener",
        f"https://api.dexscreener.com/latest/dex/tokens/{mint}",
        {
            "pairs": [
                {
                    "chainId": "solana",
                    "priceUsd": "0.18" if token == "fartcoin" else "1.23",
                    "liquidity": {"usd": liq},
                    "baseToken": {"address": mint},
                }
            ]
        },
    )

j("forensics.pump.ownership_vesting", "forensics", "file://local", json.loads((ROOT / "tests/job2/fixtures/local/pump_ownership_vesting.json").read_text()))
j("stage1.fart.top20_classified", "stage1_evidence", "file://local", json.loads((ROOT / "tests/job2/fixtures/local/fart_top20.json").read_text()))

html = '<html><body><div>Leftover Emissions</div><div>2,384,638</div></body></html>'
meta("render.dashboard.main", "render_foundation", "https://stats.renderfoundation.com/", html.encode(), "text/html")

j("solana.rpc.getTokenSupply.pump", "solana_rpc", "https://api.mainnet-beta.solana.com", {"jsonrpc": "2.0", "result": {"value": {"amount": "350000000000000", "decimals": 6}}, "id": 1})

j(
    "solana.rpc.getSupply",
    "solana_rpc",
    "https://api.mainnet-beta.solana.com",
    {"jsonrpc": "2.0", "result": {"value": {"circulating": 480000000, "total": 500000000}}, "id": 1},
)
spx_accounts = [{"uiAmount": 1000000 - i * 10000} for i in range(20)]
j(
    "solana.rpc.getTokenLargestAccounts.spx",
    "solana_rpc",
    "https://api.mainnet-beta.solana.com",
    {"jsonrpc": "2.0", "result": {"value": spx_accounts}, "id": 1},
)
j(
    "solana.rpc.getTokenSupply.spx",
    "solana_rpc",
    "https://api.mainnet-beta.solana.com",
    {"jsonrpc": "2.0", "result": {"value": {"amount": "930000000000000", "decimals": 6}}, "id": 1},
)

print("phase b fixtures", RAW)
