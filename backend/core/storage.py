from __future__ import annotations
import json, threading
from pathlib import Path
from dataclasses import asdict
from .contracts import Trajectory

class JsonStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
    def save(self, t: Trajectory):
        p = self.root / f"{t.run_id}.json"
        with self._lock:
            p.write_text(json.dumps(asdict(t), indent=2), encoding="utf-8")
        return p
    def load(self, run_id: str):
        p = self.root / f"{run_id}.json"
        if not p.exists(): return None
        return json.loads(p.read_text(encoding="utf-8"))
