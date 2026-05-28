import json
from pathlib import Path

from src.evals.schemas.eval_result import EvalResult


def export_results(
    results: list[EvalResult],
    filepath: str,
):

    path = Path(filepath)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(path, "w", encoding="utf-8") as f:

        json.dump(
            [r.model_dump() for r in results],
            f,
            ensure_ascii=False,
            indent=2,
        )