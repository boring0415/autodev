import json
import time
from pathlib import Path
from typing import Any


class JsonlLogger:
    """Append-only run events; secrets are never passed to this class."""

    def __init__(self, path: Path, run_id: str):
        self.path, self.run_id = path, run_id

    def event(self, *, phase: str, event: str, iteration: int, **data: Any) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = {"run_id": self.run_id, "timestamp": time.time(), "phase": phase,
                  "event": event, "iteration": iteration, **data}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
