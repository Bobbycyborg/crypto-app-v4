"""Exclusive ownership of live canonical during a weekly LIVE run.

Job #8 --keep-assets and weekly LIVE must not write canonical at the same time.
Test #5 collision = KNOWN AUTHORISED CONCURRENT WRITE — JOB #8F, not corruption.
"""

from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path
from typing import Any

from lib.v3.weekly_config import WEEKLY_RUNS

LIVE_LOCK_PATH = WEEKLY_RUNS / "WEEKLY_V3_LIVE.lock"


def sha256_file(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def recover_stale_live_lock() -> str | None:
    """Remove lock file when owning PID is dead. Returns recovery note or None."""
    if not LIVE_LOCK_PATH.is_file():
        return None
    try:
        data = json.loads(LIVE_LOCK_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        try:
            LIVE_LOCK_PATH.unlink(missing_ok=True)
        except OSError:
            pass
        return "removed unreadable WEEKLY_V3_LIVE.lock"
    pid = data.get("pid")
    if isinstance(pid, int) and not _pid_alive(pid):
        try:
            LIVE_LOCK_PATH.unlink(missing_ok=True)
        except OSError:
            return f"stale lock pid={pid} but unlink failed"
        return f"recovered stale lock pid={pid} run_id={data.get('run_id')}"
    return None


def detect_external_mutation(path: Path, expected: str | None, label: str) -> str | None:
    """If canonical changed under us, fail loud. Do not overwrite the other writer."""
    if not expected:
        return None
    if not path.is_file():
        return f"EXTERNAL_CANONICAL_MUTATION at {label}: canonical missing"
    got = sha256_file(path)
    if got == expected:
        return None
    return (
        f"EXTERNAL_CANONICAL_MUTATION at {label}: expected {expected} got {got}. "
        "Concurrent authorised writer (weekly LIVE vs Job #8 --keep-assets). "
        "Did not overwrite the other writer's canonical."
    )


def acquire_live_lock(run_id: str) -> tuple[int | None, str | None]:
    """Non-blocking exclusive lock. Returns (fd, error)."""
    WEEKLY_RUNS.mkdir(parents=True, exist_ok=True)
    recovered = recover_stale_live_lock()
    fd = os.open(str(LIVE_LOCK_PATH), os.O_CREAT | os.O_RDWR, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        msg = (
            "EXTERNAL_CANONICAL_MUTATION: weekly LIVE lock held — "
            "another authorised writer owns canonical "
            "(weekly LIVE, --keep-assets, or Job #8 write). Do not run concurrently."
        )
        if recovered:
            msg = f"{recovered}; then {msg}"
        return None, msg
    os.ftruncate(fd, 0)
    os.lseek(fd, 0, os.SEEK_SET)
    payload = {"run_id": run_id, "pid": os.getpid()}
    if recovered:
        payload["stale_lock_recovered"] = recovered
    os.write(fd, json.dumps(payload, indent=2).encode("utf-8"))
    return fd, None


def release_live_lock(fd: int | None) -> None:
    if fd is None:
        return
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)
        try:
            LIVE_LOCK_PATH.unlink(missing_ok=True)
        except OSError:
            pass


def weekly_live_lock_held() -> bool:
    if not LIVE_LOCK_PATH.exists():
        return False
    fd = os.open(str(LIVE_LOCK_PATH), os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(fd, fcntl.LOCK_UN)
        return False
    except BlockingIOError:
        return True
    finally:
        os.close(fd)


def ownership_record(**hashes: Any) -> dict[str, Any]:
    return dict(hashes)
