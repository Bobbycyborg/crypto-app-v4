#!/usr/bin/env python3
"""G1 dest-loader check. No RPC. No reports folder required."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.v3.siren_watch import _load_dest_tags

WINTERMUTE = "MfDuWeqSHEqTFVYZ7LoexgAK9dxk7cy4DFJWjWMGVWa"
DWF = "HwDkuDCUipJHHKodBBCjffFvrjhmd4iVVh7fq25fShvt"
REPORTS_MM = ROOT / "reports/shared-mm-registry/shared-entity-wallet-registry.json"


def main() -> int:
    print("cwd_root", ROOT)
    print("reports_mm_exists", REPORTS_MM.exists())
    cex, mm = _load_dest_tags()
    print("cex_n", len(cex))
    print("mm_n", len(mm))
    print("wintermute_resolve", mm.get(WINTERMUTE) or cex.get(WINTERMUTE))
    print("dwf_resolve", mm.get(DWF) or cex.get(DWF))
    print("mm_keys", sorted(mm))
    ok = (
        not REPORTS_MM.exists()
        and len(cex) == 227
        and len(mm) == 4
        and (mm.get(WINTERMUTE) == "Wintermute")
        and (mm.get(DWF) == "DWF Labs")
    )
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
