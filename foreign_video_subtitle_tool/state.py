from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

COMPLETED = "completed"
PENDING = "pending"
SKIPPED = "skipped"
FAILED = "failed"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "created_at": utc_now(), "updated_at": utc_now(), "stages": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = utc_now()
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def mark_stage(path: Path, stage: str, status: str, detail: str = "", data: dict[str, Any] | None = None) -> None:
    state = load_state(path)
    state.setdefault("stages", {})[stage] = {
        "status": status,
        "detail": detail,
        "updated_at": utc_now(),
        "data": data or {},
    }
    save_state(path, state)


def file_ready(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def stage_complete(state: dict[str, Any], stage: str, outputs: list[Path], force: bool = False) -> bool:
    if force:
        return False
    stage_info = state.get("stages", {}).get(stage, {})
    if stage_info.get("status") != COMPLETED:
        return False
    return all(file_ready(output) for output in outputs)
