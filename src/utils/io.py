from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path


def generate_run_id() -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_id = uuid.uuid4().hex[:8]
    return f"{ts}_{short_id}"


def create_run_dir(base: Path, run_id: str) -> Path:
    run_dir = base / run_id
    for sub in ["versions", "critiques", "revised", "safety", "final"]:
        (run_dir / sub).mkdir(parents=True, exist_ok=True)
    return run_dir


def save_json(data: dict | list, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(path: Path) -> dict | list:
    with open(path) as f:
        return json.load(f)
