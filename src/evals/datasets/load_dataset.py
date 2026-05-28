import json
from pathlib import Path

from src.evals.schemas.eval_case import EvalCase


def _normalize_case(data: dict, index: int) -> dict:
    data.setdefault("id", f"case_{index}")
    data.setdefault("expected_tools", [])
    data.setdefault("expected_keywords", [])
    data.setdefault("tags", [])

    return data


def load_eval_dataset(filepath: str) -> list[EvalCase]:
    path = Path(filepath)
    
    cases = []
    
    with open(path, "r", encoding="utf-8") as f:
        for index, line in enumerate(f, start=1):
            line = line.strip()
            
            if not line:
                continue
            
            data = json.loads(line)
            
            cases.append(EvalCase(**_normalize_case(data, index)))
        
        return cases


load_eval_database = load_eval_dataset

