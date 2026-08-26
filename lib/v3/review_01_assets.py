"""Review-01 12-asset V3 assembly. Regenerates product JSON; does not rerun Stage-1 research."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from lib.v3.fields import now_iso
from lib.v3.weekly_config import configured_slugs, v3_json_name

MANIFEST_NAME = "weekly-asset-build.json"
ALLOWED_REFRESH_MODES = frozenset(
    {"LIVE_REFRESH", "REGENERATED_FROM_LOCKED_EVIDENCE", "MIXED", "FAIL"}
)

# Honest weekly contract. Locked Stage-1 / hardcoded research is NOT "new research".
REFRESH_CONTRACT: dict[str, dict[str, Any]] = {
    "btc": {
        "mode": "REGENERATED_FROM_LOCKED_EVIDENCE",
        "loader": "lib.v3.btc_intel.write_btc_v3",
        "live_fields_refreshed": [],
        "snapshot_fields_preserved": [
            "hero.price_display",
            "context",
            "research_pack",
            "meta.gathered_at_utc",
        ],
    },
    "sol": {
        "mode": "MIXED",
        "loader": "lib.v3.sol_intel.build_sol_v3",
        "live_fields_refreshed": ["v4 price overlay when sol.json rebuilt"],
        "snapshot_fields_preserved": ["sol-forensics stage1 packs"],
    },
    "render": {
        "mode": "REGENERATED_FROM_LOCKED_EVIDENCE",
        "loader": "lib.v3.render_product.build_render_v3_from_packs",
        "live_fields_refreshed": [],
        "snapshot_fields_preserved": ["stage1 packs", "hero.price_as_of", "HTML render pin"],
    },
    "pump": {
        "mode": "MIXED",
        "loader": "lib.v3.render_intel.build_pump_v3",
        "live_fields_refreshed": ["v3 evidence", "v4 report", "platform health"],
        "snapshot_fields_preserved": ["pump-forensics snapshot", "buyer forensics"],
    },
    "grass": {
        "mode": "REGENERATED_FROM_LOCKED_EVIDENCE",
        "loader": "lib.v3.grass_product.write_grass_v3",
        "live_fields_refreshed": [],
        "snapshot_fields_preserved": ["stage1 packs", "hero.price_as_of"],
    },
    "ray": {
        "mode": "REGENERATED_FROM_LOCKED_EVIDENCE",
        "loader": "lib.v3.ray_intel.write_ray_v3",
        "live_fields_refreshed": [],
        "snapshot_fields_preserved": [
            "hero.price_display",
            "context",
            "research_pack_path",
            "meta.gathered_at_utc",
        ],
    },
    "io": {
        "mode": "REGENERATED_FROM_LOCKED_EVIDENCE",
        "loader": "lib.v3.io_product.write_io_v3",
        "live_fields_refreshed": [],
        "snapshot_fields_preserved": ["stage1 packs", "hero.price_as_of"],
    },
    "nos": {
        "mode": "REGENERATED_FROM_LOCKED_EVIDENCE",
        "loader": "lib.v3.nos_product.write_nos_v3",
        "live_fields_refreshed": [],
        "snapshot_fields_preserved": ["stage1 packs", "hero.price_as_of"],
    },
    "fartcoin": {
        "mode": "REGENERATED_FROM_LOCKED_EVIDENCE",
        "loader": "lib.v3.fartcoin_product.write_fartcoin_v3",
        "live_fields_refreshed": [],
        "snapshot_fields_preserved": ["stage1 packs", "hero.price_as_of"],
    },
    "spx6900": {
        "mode": "REGENERATED_FROM_LOCKED_EVIDENCE",
        "loader": "lib.v3.spx_product.write_spx_v3",
        "live_fields_refreshed": [],
        "snapshot_fields_preserved": ["stage1 packs", "hero.price_as_of"],
    },
    "zec": {
        "mode": "REGENERATED_FROM_LOCKED_EVIDENCE",
        "loader": "lib.v3.zec_product.write_zec_v3",
        "live_fields_refreshed": [],
        "snapshot_fields_preserved": ["stage1 packs", "hero.price_as_of"],
    },
    "hype": {
        "mode": "REGENERATED_FROM_LOCKED_EVIDENCE",
        "loader": "lib.v3.hype_product.write_hype_v3",
        "live_fields_refreshed": [],
        "snapshot_fields_preserved": ["stage1 packs", "hero.price_as_of"],
    },
}


def _ensure_slug(doc: dict[str, Any], slug: str) -> dict[str, Any]:
    meta = doc.setdefault("meta", {})
    if not meta.get("slug"):
        meta["slug"] = slug
    return doc


def _dump(out_dir: Path, slug: str, doc: dict[str, Any]) -> Path:
    path = out_dir / v3_json_name(slug)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _mtime_iso(path: Path) -> str:
    ts = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def _research_as_of(doc: dict[str, Any]) -> str | None:
    meta = doc.get("meta") or {}
    hero = doc.get("hero") or {}
    stage1 = doc.get("stage1") or {}
    stage1_meta = stage1.get("meta") if isinstance(stage1, dict) else {}
    return (
        hero.get("price_as_of")
        or meta.get("gathered_at_utc")
        or (stage1_meta or {}).get("fetched_at_utc")
        or meta.get("report_date")
    )


def _record(slug: str, path: Path, doc: dict[str, Any], *, ok: bool, error: str | None = None) -> dict[str, Any]:
    contract = REFRESH_CONTRACT[slug]
    generated = (doc.get("meta") or {}).get("generated_at") or _mtime_iso(path)
    mode = contract["mode"] if ok else "FAIL"
    return {
        "asset": slug,
        "json_path": str(path),
        "generated_at": generated,
        "file_mtime": _mtime_iso(path),
        "refresh_mode": mode,
        "ok": ok,
        "live_fields_refreshed": list(contract["live_fields_refreshed"]) if ok else [],
        "snapshot_fields_preserved": list(contract["snapshot_fields_preserved"]),
        "research_as_of": _research_as_of(doc),
        "loader": contract["loader"],
        "error": error,
    }


def _locked_writers() -> dict[str, Callable[..., dict[str, Any]]]:
    from lib.v3.fartcoin_product import write_fartcoin_v3
    from lib.v3.grass_product import write_grass_v3
    from lib.v3.hype_product import write_hype_v3
    from lib.v3.io_product import write_io_v3
    from lib.v3.nos_product import write_nos_v3
    from lib.v3.spx_product import write_spx_v3
    from lib.v3.zec_product import write_zec_v3

    return {
        "grass": write_grass_v3,
        "io": write_io_v3,
        "nos": write_nos_v3,
        "fartcoin": write_fartcoin_v3,
        "spx6900": write_spx_v3,
        "zec": write_zec_v3,
        "hype": write_hype_v3,
    }


def complete_review_01_assets(
    out_dir: Path,
    already: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Write all 12 current-run V3 JSONs into out_dir. Does not rerun Stage-1 research."""
    out_dir.mkdir(parents=True, exist_ok=True)
    slugs = configured_slugs()
    writers = _locked_writers()
    assets: dict[str, dict[str, Any]] = dict(already)
    records: dict[str, dict[str, Any]] = {}
    errors: list[str] = []

    for slug in slugs:
        try:
            if slug in already:
                doc = _ensure_slug(already[slug], slug)
                path = _dump(out_dir, slug, doc)
            elif slug in writers:
                doc = _ensure_slug(writers[slug](out_dir), slug)
                path = out_dir / v3_json_name(slug)
                if not path.is_file():
                    path = _dump(out_dir, slug, doc)
            else:
                raise RuntimeError(f"no Review-01 writer for {slug}")
            assets[slug] = doc
            records[slug] = _record(slug, path, doc, ok=True)
        except Exception as exc:  # noqa: BLE001 — per-asset fail must not skip the rest
            errors.append(f"{slug}: {exc}")
            records[slug] = {
                "asset": slug,
                "json_path": None,
                "generated_at": None,
                "file_mtime": None,
                "refresh_mode": "FAIL",
                "ok": False,
                "live_fields_refreshed": [],
                "snapshot_fields_preserved": list(
                    (REFRESH_CONTRACT.get(slug) or {}).get("snapshot_fields_preserved") or []
                ),
                "research_as_of": None,
                "loader": (REFRESH_CONTRACT.get(slug) or {}).get("loader"),
                "error": str(exc),
            }

    manifest = {
        "report_dir": str(out_dir),
        "built_at": now_iso(),
        "asset_count": len(slugs),
        "assets": records,
        "errors": errors,
        "ok": not errors,
        "note": (
            "generated_at is product regeneration time. "
            "research_as_of / snapshot_fields_preserved are locked Stage-1 or hardcoded research. "
            "Regenerated ≠ new research."
        ),
    }
    (out_dir / MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return assets, manifest


def load_asset_build_manifest(report_dir: Path | None) -> dict[str, Any] | None:
    if report_dir is None or not report_dir.is_dir():
        return None
    path = report_dir / MANIFEST_NAME
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def validate_current_run_coverage(
    manifest: dict[str, Any] | None,
    slugs: tuple[str, ...],
) -> dict[str, Any]:
    """Stale pre-existing JSON is not a current-run result."""
    errors: list[str] = []
    if not manifest:
        return {
            "ok": False,
            "errors": [
                "weekly-asset-build.json missing — 12-asset current-run coverage not proven"
            ],
            "assets": {},
        }
    rows = manifest.get("assets") or {}
    for slug in slugs:
        row = rows.get(slug)
        if not row:
            errors.append(f"{slug}: no current-run build result (stale JSON cannot silently pass)")
            continue
        if not row.get("ok"):
            errors.append(f"{slug}: build FAIL ({row.get('error') or row.get('refresh_mode')})")
            continue
        mode = row.get("refresh_mode")
        if mode not in ALLOWED_REFRESH_MODES or mode == "FAIL":
            errors.append(f"{slug}: invalid refresh_mode {mode}")
            continue
        path = Path(row["json_path"]) if row.get("json_path") else None
        if path is None or not path.is_file():
            errors.append(f"{slug}: current-run json missing at {row.get('json_path')}")
    return {"ok": not errors, "errors": errors, "assets": rows}
