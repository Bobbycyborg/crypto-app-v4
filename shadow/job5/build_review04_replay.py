#!/usr/bin/env python3
"""Package Review04 replay directory. Copy exact raw bytes only — never invent bodies."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--captures-dir", default=None, help="Optional directory of Review04 raw captures")
    p.add_argument("--out", required=True)
    args = p.parse_args()
    out = Path(args.out)
    raw = out / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    copied = 0
    if args.captures_dir:
        src = Path(args.captures_dir)
        if not src.is_dir():
            raise SystemExit(f"captures dir missing: {src}")
        for meta in src.glob("*.meta.json"):
            body = meta.with_suffix("").with_suffix(".body")
            if not body.is_file():
                alt = src / json.loads(meta.read_text())["raw_body_path"]
                body = alt
            shutil.copy2(meta, raw / meta.name)
            shutil.copy2(body, raw / Path(body).name)
            copied += 1
    (out / "replay-meta.json").write_text(
        json.dumps(
            {
                "mode": "review04_historical",
                "live_fetches": 0,
                "raw_captures_copied": copied,
                "note": "Missing request keys stay SOURCE_UNAVAILABLE until Job5 historical bridge merge.",
            },
            indent=2,
        )
        + "\n"
    )
    print(f"replay_dir {out} raw_captures {copied}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
