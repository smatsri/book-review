"""Thin subprocess runner for the local pipeline operator UI (no LLM)."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from book import BookPaths, ROOT, require_book_id

# stage_id → argv after `python main.py` (before --book).
STAGE_ARGV: dict[str, list[str]] = {
    "chapters": ["chapters"],
    "summarize": ["summarize", "--all"],
    "report": ["report"],
    "rollup": ["rollup"],
    "aliases": ["aliases"],
    "footnotes": ["footnotes", "--all"],
    "reduce": ["reduce"],
    "visual_identity": ["visual-identity"],
    "visual_characters": ["visual-characters"],
    "visual_places": ["visual-places"],
    "visual_scenes": ["visual-scenes"],
    "visual_handoff": ["visual-handoff"],
    "visual_resolved": ["visual-resolve"],
    "enriched": ["enriched"],
    "export_report": ["export", "--mode", "report"],
    "export_enriched": ["export", "--mode", "enriched"],
}

# Manual assets / nested local servers — Copy CLI / links only.
NON_RUNNABLE_STAGES = frozenset({"illustrations", "visual_answers"})

LOG_TAIL_BYTES = 32_768

_lock = threading.Lock()
_process: subprocess.Popen[bytes] | None = None
_log_handle: Any = None
_current: dict[str, Any] | None = None


def stage_is_runnable(stage_id: str) -> bool:
    return stage_id in STAGE_ARGV


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _status_path(paths: BookPaths) -> Path:
    return paths.state_dir / "run-status.json"


def _log_path(paths: BookPaths) -> Path:
    return paths.state_dir / "pipeline-run.log"


def _write_status(paths: BookPaths, payload: dict[str, Any]) -> None:
    paths.state_dir.mkdir(parents=True, exist_ok=True)
    path = _status_path(paths)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _read_log_tail(log_path: Path) -> str:
    if not log_path.is_file():
        return ""
    try:
        data = log_path.read_bytes()
    except OSError:
        return ""
    if len(data) > LOG_TAIL_BYTES:
        data = data[-LOG_TAIL_BYTES:]
    return data.decode("utf-8", errors="replace")


def _refresh_locked() -> dict[str, Any]:
    """Update exit_code/finished_at when the child has exited. Caller holds _lock."""
    global _process, _log_handle, _current

    if _current is None:
        return {"state": "idle"}

    if _process is not None:
        code = _process.poll()
        if code is not None:
            if _log_handle is not None:
                try:
                    _log_handle.close()
                except OSError:
                    pass
                _log_handle = None
            _current["exit_code"] = code
            if _current.get("finished_at") is None:
                _current["finished_at"] = _utc_now()
            _current["state"] = "finished"
            book_id = _current.get("book_id")
            if isinstance(book_id, str) and book_id:
                paths = BookPaths(book_id=book_id, root=ROOT)
                _write_status(paths, {k: v for k, v in _current.items() if k != "log_tail"})
            _process = None

    payload = dict(_current)
    log_rel = payload.get("log")
    if isinstance(log_rel, str) and log_rel:
        payload["log_tail"] = _read_log_tail(ROOT / log_rel)
    else:
        payload["log_tail"] = ""
    return payload


def get_run_status() -> dict[str, Any]:
    """Return idle or current/last run payload (includes log_tail)."""
    with _lock:
        return _refresh_locked()


def start_run(book_id: str, stage_id: str, *, root: Path = ROOT) -> dict[str, Any]:
    """Spawn one allowlisted CLI step. Raises ValueError / RuntimeError."""
    global _process, _log_handle, _current

    book_id = (book_id or "").strip()
    stage_id = (stage_id or "").strip()
    if not book_id:
        raise ValueError("Missing book")
    if not stage_id:
        raise ValueError("Missing stage")
    if stage_id in NON_RUNNABLE_STAGES:
        raise ValueError(f"Stage {stage_id!r} is not runnable from the UI")
    if stage_id not in STAGE_ARGV:
        raise ValueError(f"Unknown or non-runnable stage {stage_id!r}")

    meta = require_book_id(book_id, root=root)
    paths = BookPaths(book_id=meta.id, root=root)
    argv_tail = STAGE_ARGV[stage_id]
    argv = [
        sys.executable,
        str(root / "main.py"),
        *argv_tail,
        "--book",
        meta.id,
    ]

    with _lock:
        _refresh_locked()
        if _process is not None and _process.poll() is None:
            raise RuntimeError("A pipeline run is already in progress")

        paths.state_dir.mkdir(parents=True, exist_ok=True)
        log_path = _log_path(paths)
        log_rel = log_path.relative_to(root).as_posix()
        log_handle = open(log_path, "wb")
        try:
            proc = subprocess.Popen(
                argv,
                cwd=str(root),
                stdout=log_handle,
                stderr=subprocess.STDOUT,
            )
        except OSError:
            log_handle.close()
            raise

        started = _utc_now()
        status = {
            "state": "running",
            "book_id": meta.id,
            "stage_id": stage_id,
            "argv": argv,
            "pid": proc.pid,
            "started_at": started,
            "finished_at": None,
            "exit_code": None,
            "log": log_rel,
        }
        _write_status(paths, status)
        _process = proc
        _log_handle = log_handle
        _current = status
        return _refresh_locked()
