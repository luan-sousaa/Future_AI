import json
from pathlib import Path

from src.evals.schemas.trace import ExecutionTrace


class TraceStore:
    def __init__(self, base_path: str = ".traces"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, trace: ExecutionTrace):
        filepath = self.base_path / f"{trace.trace_id}.json"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                trace.model_dump(),
                f,
                ensure_ascii=False,
                indent=2,
            )

    def load(self, trace_id: str) -> dict:
        filepath = self.base_path / f"{trace_id}.json"

        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)