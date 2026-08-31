#!/usr/bin/env python3
"""Synthetic wallet plug-in: two opaque payloads, same non-wallet snapshot."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shadow/job5"))
from classify_diff import wallet_blob, sha256_bytes  # noqa: E402

TPL = """<html><body>price</body>
<script type="application/json" id="siren-watch-data">{payload}</script>
</html>"""


def test_wallet_opacity():
    a = TPL.format(payload="SYNTHETIC_WALLET_OPAQUE_A")
    b = TPL.format(payload="SYNTHETIC_WALLET_OPAQUE_B")
    ha = sha256_bytes(wallet_blob(a))
    hb = sha256_bytes(wallet_blob(b))
    assert ha != hb
    # non-wallet prefix identical
    assert a.split("id=\"siren-watch-data\">")[0] == b.split("id=\"siren-watch-data\">")[0]
    print("test_wallet_opacity PASS")
    print(f"synthetic_a={ha}")
    print(f"synthetic_b={hb}")


if __name__ == "__main__":
    test_wallet_opacity()
