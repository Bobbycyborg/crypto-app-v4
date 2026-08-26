"""Source adapters: fetch only. Metric identity lives in collector-plan.json."""

from __future__ import annotations

import os
from typing import Any

from collectors.http_client import HttpError, HttpResponse, request as http_request
from collectors.source_requests import REQUESTS


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
    extra = dict(spec.get("headers") or {})
    if spec.get("auth") == "coingecko_optional":
        extra.update(_coingecko_headers())
    return http_request(
        spec["method"],
        spec["url"],
        params=spec.get("params"),
        json_body=spec.get("json_body"),
        extra_headers=extra or None,
    )


def source_key_for(request_key: str) -> str:
    return REQUESTS[request_key]["source_key"]
