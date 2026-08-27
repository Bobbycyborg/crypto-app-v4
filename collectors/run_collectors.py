#!/usr/bin/env python3
"""Job 2 collector orchestrator. No UI. No Job 1 mutation. Fail closed."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import sys
import time
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from collectors.derive import derive
from collectors.extract import (
    ExtractError,
    extract,
    klines_rs_pct,
    open_interest_usd,
    parse_json_body,
    perp_spot_ratio,
)
from collectors.http_client import HttpError, body_sha256, redact_url, utc_now
from collectors.normalize import normalize
from collectors.source_requests import REQUESTS
from collectors.sources import fetch as live_fetch

PLAN_PATH = ROOT / "collectors/collector-plan.json"
REG_PATH = ROOT / "metrics/metric-registry.json"
RUNTIME = ROOT / "runtime-NOT-FOR-GH/job2"

EXIT_OK = 0
EXIT_REQUIRED_FAIL = 2
EXIT_CONTRACT = 3
EXIT_AUTH = 4
EXIT_INTERNAL = 5


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def json_dump(obj: Any) -> str:
    def conv(o: Any) -> Any:
        if isinstance(o, Decimal):
            if o == o.to_integral_value():
                return int(o)
            return format(o, "f")
        raise TypeError(type(o))

    return json.dumps(obj, indent=2, default=conv) + "\n"


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    tmp.replace(path)


def load_plan() -> dict[str, Any]:
    return json.loads(PLAN_PATH.read_text(encoding="utf-8"))


def load_registry() -> dict[str, Any]:
    return json.loads(REG_PATH.read_text(encoding="utf-8"))


def validate_contract(plan: dict[str, Any], registry: dict[str, Any]) -> None:
    metrics = registry["metrics"]
    ids = [m["metric_id"] for m in metrics]
    if len(ids) != len(set(ids)):
        raise RuntimeError("duplicate metric_id in Job 1 registry")
    entries = plan["entries"]
    pids = [e["metric_id"] for e in entries]
    if len(pids) != len(set(pids)):
        raise RuntimeError("duplicate_metric_writer")
    if set(ids) != set(pids):
        missing = set(ids) - set(pids)
        extra = set(pids) - set(ids)
        raise RuntimeError(f"plan/registry mismatch missing={sorted(missing)[:8]} extra={sorted(extra)[:8]}")
    by_id = {m["metric_id"]: m for m in metrics}
    for e in entries:
        mid = e["metric_id"]
        m = by_id[mid]
        disp = e["disposition"]
        if disp == "COLLECT":
            if not e.get("source_key") or not e.get("request_key") or not e.get("selector") or not e.get("normalizer"):
                raise RuntimeError(f"COLLECT incomplete {mid}")
            if e["request_key"] not in REQUESTS:
                raise RuntimeError(f"unknown request_key {e['request_key']}")
            if REQUESTS[e["request_key"]]["source_key"] != e["source_key"]:
                raise RuntimeError(f"unproved_provider_substitution {mid}")
        if disp == "DERIVE":
            der = e.get("derivation") or {}
            if not der.get("inputs") or not der.get("op") or not der.get("calculation_version"):
                raise RuntimeError(f"DERIVE incomplete {mid}")
        if disp == "GROK_WALLET" and m["owner"] != "GROK":
            raise RuntimeError(f"wallet_collector mis-tagged {mid}")
        if disp == "COLLECT" and m["owner"] == "GROK":
            raise RuntimeError(f"wallet_collector {mid}")
        if disp == "COLLECT" and m["asset"] in {"RAY", "GRASS", "DRIFT"}:
            raise RuntimeError(f"dormant_asset_collector {mid}")
        if disp == "BLOCKED_SOURCE" and e.get("required"):
            raise RuntimeError(f"required_blocked_source {mid}")
        if "helius" in json.dumps(e).lower():
            raise RuntimeError("helius mentioned in plan")


def new_run_id() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "_" + secrets.token_hex(4)


def encode_value(v: Decimal | int) -> str | int:
    if isinstance(v, int):
        return v
    if v == v.to_integral_value():
        return int(v)
    return format(v, "f")


def fact_error(metric_id: str, status: str, err: str, **extra: Any) -> dict[str, Any]:
    row = {
        "metric_id": metric_id,
        "status": status,
        "raw_source_value": None,
        "normalized_value": None,
        "unit": extra.get("unit"),
        "source_key": extra.get("source_key"),
        "request_key": extra.get("request_key"),
        "source_field": extra.get("source_field"),
        "source_as_of": "UNKNOWN",
        "fetched_at": extra.get("fetched_at"),
        "raw_capture_sha256": extra.get("raw_capture_sha256"),
        "calculation_version": extra.get("calculation_version"),
        "derivation_inputs": extra.get("derivation_inputs"),
        "error": err,
    }
    return row


class Capture:
    def __init__(self, meta: dict[str, Any], body: bytes, parsed: Any, html: str | None) -> None:
        self.meta = meta
        self.body = body
        self.parsed = parsed
        self.html = html


def persist_capture(run_dir: Path, request_key: str, resp_meta: dict[str, Any], body: bytes) -> Path:
    raw_dir = run_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    body_path = raw_dir / f"{request_key.replace('/', '_')}.body"
    body_path.write_bytes(body)
    meta_path = raw_dir / f"{request_key.replace('/', '_')}.meta.json"
    atomic_write(meta_path, json.dumps(resp_meta, indent=2) + "\n")
    return body_path


def load_replay_captures(replay_path: Path) -> dict[str, Capture]:
    out: dict[str, Capture] = {}
    raw_dir = replay_path / "raw" if (replay_path / "raw").is_dir() else replay_path
    for meta_path in sorted(raw_dir.glob("*.meta.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        request_key = meta["request_key"]
        body_path = raw_dir / Path(meta["raw_body_path"]).name
        if not body_path.is_file():
            body_path = meta_path.with_suffix("").with_suffix(".body")
        body = body_path.read_bytes()
        kind = REQUESTS.get(request_key, {}).get("response_kind", "json")
        html = None
        parsed: Any = None
        if kind == "html":
            html = body.decode("utf-8")
        else:
            parsed = parse_json_body(body, meta.get("content_type"))
        out[request_key] = Capture(meta, body, parsed, html)
    return out


def fetch_live(request_key: str, run_dir: Path) -> Capture:
    spec = REQUESTS[request_key]
    resp = live_fetch(request_key)
    content_type = resp.headers.get("Content-Type") or resp.headers.get("content-type") or ""
    meta = {
        "source_key": spec["source_key"],
        "request_key": request_key,
        "url": redact_url(resp.url),
        "params": spec.get("params"),
        "http_status": resp.status_code,
        "fetched_at": resp.fetched_at,
        "content_type": content_type,
        "body_sha256": body_sha256(resp.body),
        "raw_body_path": f"{request_key.replace('/', '_')}.body",
        "attempts": resp.attempts,
    }
    persist_capture(run_dir, request_key, meta, resp.body)
    kind = spec.get("response_kind", "json")
    html = None
    parsed: Any = None
    if kind == "html":
        html = resp.body.decode("utf-8")
    else:
        parsed = parse_json_body(resp.body, content_type)
        ident = spec.get("identity")
        if ident and isinstance(parsed, dict):
            for k, v in ident.items():
                if parsed.get(k) != v and str(parsed.get(k) or "").upper() != str(v).upper():
                    raise ExtractError("SOURCE_SCHEMA_MISMATCH", f"identity {k}={v!r} got {parsed.get(k)!r}")
    return Capture(meta, resp.body, parsed, html)


def extract_metric(entry: dict[str, Any], captures: dict[str, Capture]) -> tuple[Any, str | None]:
    selector = entry["selector"]
    request_key = entry["request_key"]
    cap = captures[request_key]
    name = selector.get("name")
    if name == "klines_rs_pct":
        bench_key = selector["bench_request_key"]
        if bench_key not in captures:
            raise ExtractError("SOURCE_UNAVAILABLE", f"missing bench capture {bench_key}")
        return klines_rs_pct(cap.parsed, captures[bench_key].parsed, int(selector["window_days"])), None
    if name == "market_chart_rs_pct":
        bench_key = selector["bench_request_key"]
        if bench_key not in captures:
            raise ExtractError("SOURCE_UNAVAILABLE", f"missing bench capture {bench_key}")
        from collectors.phase_b_selectors_extra import market_chart_rs_pct

        return market_chart_rs_pct(cap.parsed, captures[bench_key].parsed, int(selector["window_days"])), None
    if name == "open_interest_usd":
        mark_key = selector["mark_request_key"]
        if mark_key not in captures:
            raise ExtractError("SOURCE_UNAVAILABLE", f"missing mark capture {mark_key}")
        return open_interest_usd(cap.parsed, captures[mark_key].parsed, selector), None
    if name == "perp_spot_ratio":
        spot_key = selector["spot_request_key"]
        if spot_key not in captures:
            raise ExtractError("SOURCE_UNAVAILABLE", f"missing spot capture {spot_key}")
        return perp_spot_ratio(cap.parsed, captures[spot_key].parsed, selector), None
    if name == "perp_vs_coinbase_spot_ratio":
        spot_key = selector["spot_request_key"]
        if spot_key not in captures:
            raise ExtractError("SOURCE_UNAVAILABLE", f"missing spot capture {spot_key}")
        from collectors.phase_b_selectors_extra import perp_vs_coinbase_spot_ratio

        return perp_vs_coinbase_spot_ratio(cap.parsed, captures[spot_key].parsed, selector), None
    if name == "dex_chain_ratio":
        den_key = selector["den_request_key"]
        if den_key not in captures:
            raise ExtractError("SOURCE_UNAVAILABLE", f"missing den capture {den_key}")
        from collectors.phase_b_selectors_extra import dex_chain_ratio

        return dex_chain_ratio(cap.parsed, captures[den_key].parsed, selector), None
    if name == "pump_circulating_pct_of_max":
        sup_key = selector["solana_supply_request_key"]
        if sup_key not in captures:
            raise ExtractError("SOURCE_UNAVAILABLE", f"missing supply capture {sup_key}")
        from collectors.phase_b_selectors_extra import pump_circulating_pct_of_max

        return pump_circulating_pct_of_max(cap.parsed, captures[sup_key].parsed, selector), None
    if name == "solana_top20_pct_of_mint":
        sup_key = selector["solana_supply_request_key"]
        if sup_key not in captures:
            raise ExtractError("SOURCE_UNAVAILABLE", f"missing supply capture {sup_key}")
        from collectors.phase_b_selectors_extra import solana_top20_pct_of_mint

        return solana_top20_pct_of_mint(cap.parsed, captures[sup_key].parsed, selector), None
    if name == "participation_above_50d_n":
        charts_key = selector.get("charts_request_key", "coingecko.market_charts.breadth_bundle")
        if charts_key not in captures:
            raise ExtractError("SOURCE_UNAVAILABLE", f"missing charts capture {charts_key}")
        from collectors.phase_b_selectors_extra import participation_above_50d_n

        return participation_above_50d_n(cap.parsed, selector, captures[charts_key].parsed), None
    if name == "bme_burn_emit_ratio_last_n":
        liab_key = selector.get("liability_request_key", "render.liabilityEpochs")
        if liab_key not in captures:
            raise ExtractError("SOURCE_UNAVAILABLE", f"missing liability capture {liab_key}")
        from collectors.phase_b_selectors_extra import bme_burn_emit_ratio_last_n

        return bme_burn_emit_ratio_last_n(cap.parsed, captures[liab_key].parsed, selector), None
    raw = extract(cap.parsed, selector, html=cap.html)
    return raw, cap.meta.get("fetched_at")


def extra_request_keys(entry: dict[str, Any]) -> list[str]:
    sel = entry.get("selector") or {}
    extra = []
    for k in ("bench_request_key", "mark_request_key", "spot_request_key", "den_request_key", "solana_supply_request_key", "charts_request_key", "liability_request_key"):
        if sel.get(k):
            extra.append(sel[k])
    return extra


def run(mode: str, replay_path: Path | None) -> tuple[int, dict[str, Any]]:
    plan = load_plan()
    registry = load_registry()
    try:
        validate_contract(plan, registry)
    except RuntimeError as exc:
        print(f"CONTRACT FAIL: {exc}", file=sys.stderr)
        return EXIT_CONTRACT, {}

    run_id = new_run_id() if mode == "live" else "REPLAY"
    started = utc_now()
    run_dir = RUNTIME / ("replay" if mode == "replay" else run_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    captures: dict[str, Capture] = {}
    if mode == "replay":
        if not replay_path:
            return EXIT_CONTRACT, {}
        captures = load_replay_captures(replay_path)

    entries = plan["entries"]
    collect_entries = [e for e in entries if e["disposition"] == "COLLECT"]
    derive_entries = [e for e in entries if e["disposition"] == "DERIVE"]

    needed: list[str] = []
    for e in collect_entries:
        needed.append(e["request_key"])
        needed.extend(extra_request_keys(e))
    needed_unique = list(dict.fromkeys(needed))

    fetch_errors: dict[str, str] = {}
    auth_fail = False
    if mode == "live":
        for rk in needed_unique:
            try:
                captures[rk] = fetch_live(rk, run_dir)
            except HttpError as exc:
                fetch_errors[rk] = f"{exc.status}: {exc.message}"
                if exc.status == "AUTH_MISSING":
                    auth_fail = True
            except ExtractError as exc:
                fetch_errors[rk] = f"{exc.status}: {exc.message}"
    else:
        for rk in needed_unique:
            if rk not in captures:
                fetch_errors[rk] = "SOURCE_UNAVAILABLE: missing replay capture"

    facts: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}

    for e in entries:
        mid = e["metric_id"]
        disp = e["disposition"]
        if disp in {"PRESERVE", "GROK_WALLET", "LEGACY_INACTIVE", "COMPOSITE_ONLY"}:
            facts.append(
                fact_error(mid, "OUT_OF_SCOPE", f"disposition={disp}", unit=e.get("unit"), calculation_version=None)
            )
            continue
        if disp == "BLOCKED_SOURCE":
            row = fact_error(
                mid,
                "UNKNOWN",
                e.get("notes") or "blocked",
                unit=e.get("unit"),
            )
            facts.append(row)
            by_id[mid] = row
            continue
        if disp == "COLLECT":
            rk = e["request_key"]
            if rk in fetch_errors or any(x in fetch_errors for x in extra_request_keys(e)):
                err = fetch_errors.get(rk) or next(fetch_errors[x] for x in extra_request_keys(e) if x in fetch_errors)
                status = "AUTH_MISSING" if err.startswith("AUTH_MISSING") else "SOURCE_UNAVAILABLE"
                row = fact_error(
                    mid,
                    status,
                    err,
                    unit=e.get("unit"),
                    source_key=e.get("source_key"),
                    request_key=rk,
                )
                facts.append(row)
                by_id[mid] = row
                continue
            cap = captures[rk]
            try:
                raw, _fetched = extract_metric(e, captures)
                if raw is None:
                    raise ExtractError("VALUE_MISSING", "extracted null")
                norm = normalize(raw, e.get("normalizer"))
                as_of = "UNKNOWN"
                as_sel = e.get("source_as_of")
                if as_sel:
                    try:
                        as_of = str(extract(cap.parsed, as_sel, html=cap.html))
                    except ExtractError:
                        as_of = "UNKNOWN"
                row = {
                    "metric_id": mid,
                    "status": "OK",
                    "raw_source_value": str(raw),
                    "normalized_value": encode_value(norm),
                    "unit": e.get("unit"),
                    "source_key": e.get("source_key"),
                    "request_key": rk,
                    "source_field": json.dumps(e.get("selector")),
                    "source_as_of": as_of,
                    "fetched_at": cap.meta.get("fetched_at"),
                    "raw_capture_sha256": cap.meta.get("body_sha256"),
                    "calculation_version": None,
                    "derivation_inputs": None,
                    "error": None,
                }
            except ExtractError as exc:
                row = fact_error(
                    mid,
                    exc.status,
                    exc.message,
                    unit=e.get("unit"),
                    source_key=e.get("source_key"),
                    request_key=rk,
                    fetched_at=cap.meta.get("fetched_at"),
                    raw_capture_sha256=cap.meta.get("body_sha256"),
                )
            except HttpError as exc:
                row = fact_error(mid, exc.status, exc.message, unit=e.get("unit"), source_key=e.get("source_key"), request_key=rk)
            facts.append(row)
            by_id[mid] = row
            continue
        if disp == "DERIVE":
            continue
        facts.append(fact_error(mid, "VALUE_INVALID", f"unknown disposition {disp}"))

    for e in derive_entries:
        mid = e["metric_id"]
        der = e["derivation"]
        inputs = der["inputs"]
        blocked = False
        vals: list[Decimal] = []
        for inp in inputs:
            src = by_id.get(inp)
            if not src or src.get("status") != "OK":
                blocked = True
                break
            vals.append(Decimal(str(src["normalized_value"])))
        if blocked:
            row = fact_error(
                mid,
                "DERIVATION_BLOCKED",
                f"inputs not OK: {inputs}",
                unit=e.get("unit"),
                derivation_inputs=inputs,
                calculation_version=der.get("calculation_version"),
            )
            facts.append(row)
            by_id[mid] = row
            continue
        try:
            out = derive(der["op"], vals, der["calculation_version"])
            row = {
                "metric_id": mid,
                "status": "OK",
                "raw_source_value": None,
                "normalized_value": encode_value(out),
                "unit": e.get("unit"),
                "source_key": None,
                "request_key": None,
                "source_field": der["op"],
                "source_as_of": "UNKNOWN",
                "fetched_at": None,
                "raw_capture_sha256": None,
                "calculation_version": der["calculation_version"],
                "derivation_inputs": inputs,
                "error": None,
            }
        except ExtractError as exc:
            row = fact_error(mid, exc.status, exc.message, unit=e.get("unit"), derivation_inputs=inputs)
        facts.append(row)
        by_id[mid] = row

    required_all = [e for e in entries if e.get("required")]
    required_dynamic = [e for e in required_all if e["disposition"] in {"COLLECT", "DERIVE"}]
    required_blocked = [e for e in required_all if e["disposition"] == "BLOCKED_SOURCE"]
    req_ok = sum(1 for e in required_dynamic if by_id.get(e["metric_id"], {}).get("status") == "OK")
    req_fail = [e["metric_id"] for e in required_dynamic if by_id.get(e["metric_id"], {}).get("status") != "OK"]
    required_unaccounted = [
        e["metric_id"]
        for e in required_all
        if e["disposition"] not in {"COLLECT", "DERIVE", "BLOCKED_SOURCE"}
    ]

    if mode == "replay":
        overall = "REPLAY"
    elif required_blocked or required_unaccounted:
        overall = "FAIL"
    elif not required_dynamic:
        overall = "SUCCESS"
    elif req_fail and req_ok:
        overall = "PARTIAL_FAIL"
    elif req_fail:
        overall = "FAIL"
    else:
        overall = "SUCCESS"

    finished = utc_now()
    output = {
        "run_id": run_id if mode == "live" else f"REPLAY_{replay_path.name if replay_path else ''}",
        "started_at": started,
        "finished_at": finished,
        "job1_registry_sha256": sha256_file(REG_PATH),
        "collector_plan_sha256": sha256_file(PLAN_PATH),
        "overall_status": overall,
        "mode": mode,
        "source_requests": len(needed_unique),
        "required_total": len(required_all),
        "required_dynamic": len(required_dynamic),
        "required_ok": req_ok,
        "required_failed": len(req_fail),
        "required_failed_ids": req_fail,
        "required_blocked_source": [e["metric_id"] for e in required_blocked],
        "required_dynamic_unaccounted": required_unaccounted,
        "facts": facts,
    }
    out_path = run_dir / "collector-run.json"
    atomic_write(out_path, json_dump(output))

    print(f"run_id {output['run_id']}")
    print(f"source requests {len(needed_unique)}")
    print(f"required metrics OK {req_ok}")
    print(f"required metrics failed {len(req_fail)}")
    print(f"overall status {overall}")
    print(f"output location {out_path}")

    if auth_fail:
        return EXIT_AUTH, output
    if overall == "FAIL" and mode == "live":
        return EXIT_REQUIRED_FAIL, output
    if overall == "PARTIAL_FAIL" and mode == "live":
        return EXIT_REQUIRED_FAIL, output
    return EXIT_OK, output


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--live", action="store_true")
    p.add_argument("--replay", type=str, default=None)
    args = p.parse_args()
    if args.replay:
        code, _ = run("replay", Path(args.replay))
        return code
    if args.live:
        code, _ = run("live", None)
        return code
    print("usage: run_collectors.py --live | --replay PATH", file=sys.stderr)
    return EXIT_CONTRACT


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except HttpError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(EXIT_AUTH if exc.status == "AUTH_MISSING" else EXIT_INTERNAL)
    except Exception as exc:  # noqa: BLE001
        print(f"INTERNAL {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(EXIT_INTERNAL)
