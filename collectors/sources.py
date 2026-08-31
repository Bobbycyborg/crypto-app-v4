"""Source adapters: fetch only. Metric identity lives in collector-plan.json."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from collectors.http_client import HttpError, HttpResponse, request as http_request
from collectors.source_requests import REQUESTS

ROOT = Path(__file__).resolve().parents[1]
SOLANA_RPC_FAILOVERS = (
    "https://solana-rpc.publicnode.com",
    "https://rpc.ankr.com/solana",
)


def _helius_rpc_url() -> str | None:
    env = ROOT / "config/helius.local.env"
    if not env.is_file():
        return None
    for line in env.read_text(encoding="utf-8").splitlines():
        if line.startswith("HELIUS_API_KEY=") and "your_helius" not in line:
            key = line.split("=", 1)[1].strip().strip('"').strip("'")
            if key:
                return f"https://mainnet.helius-rpc.com/?api-key={key}"
    return None


def _coingecko_headers() -> dict[str, str]:
    pro = os.environ.get("COINGECKO_PRO_API_KEY")
    demo = os.environ.get("COINGECKO_DEMO_API_KEY")
    if pro:
        return {"x-cg-pro-api-key": pro}
    if demo:
        return {"x-cg-demo-api-key": demo}
    return {}


def fetch(request_key: str) -> HttpResponse:
    if request_key not in REQUESTS:
        raise HttpError("SOURCE_UNAVAILABLE", f"unknown request_key {request_key}")
    spec = REQUESTS[request_key]
    url = spec["url"]
    if url.startswith("file://"):
        from collectors.http_client import HttpResponse, body_sha256, utc_now

        rel = url[len("file://") :]
        path = (ROOT / rel) if not rel.startswith("/") else Path(rel)
        body = path.read_bytes()
        return HttpResponse(
            url=url,
            method=spec.get("method", "GET"),
            status_code=200,
            headers={"Content-Type": "application/json"},
            body=body,
            fetched_at=utc_now(),
            attempts=1,
        )
    extra = dict(spec.get("headers") or {})
    if spec.get("auth") == "coingecko_optional":
        extra.update(_coingecko_headers())
    try:
        return http_request(
            spec["method"],
            spec["url"],
            params=spec.get("params"),
            json_body=spec.get("json_body"),
            extra_headers=extra or None,
        )
    except HttpError as exc:
        if spec.get("source_key") == "farside" and exc.http_status == 403:
            from collectors.etf_failover import farside_failover

            return farside_failover(request_key)
        if spec.get("source_key") == "solana_rpc" and exc.http_status in {429, 403}:
            alts: list[str] = []
            helius = _helius_rpc_url()
            if helius:
                alts.append(helius)
            alts.extend(SOLANA_RPC_FAILOVERS)
            last = exc
            for alt in alts:
                try:
                    return http_request(
                        spec["method"],
                        alt,
                        params=spec.get("params"),
                        json_body=spec.get("json_body"),
                        extra_headers=extra or None,
                    )
                except HttpError as alt_exc:
                    last = alt_exc
                    continue
            raise last
        raise


def source_key_for(request_key: str) -> str:
    return REQUESTS[request_key]["source_key"]
