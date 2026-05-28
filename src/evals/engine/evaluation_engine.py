from src.evals.schemas.eval_case import EvalCase
from src.evals.schemas.eval_result import EvalResult

from src.evals.metrics.tool_metrics import evaluate_tool_usage
from src.evals.metrics.keyword_metrics import evaluate_keywords
from src.evals.metrics.response_metrics import (
    evaluate_response_quality,
)


class EvaluationEngine:

    def evaluate(
        self,
        case: EvalCase,
        response: str,
        tools_used: list[str],
    ) -> EvalResult:

        metrics = []

        metrics.append(
            evaluate_tool_usage(
                expected_tools=case.expected_tools,
                used_tools=tools_used,
            )
        )

        metrics.append(
            evaluate_keywords(
                expected_keywords=case.expected_keywords,
                response=response,
            )
        )

        metrics.append(
            evaluate_response_quality(
                response=response,
            )
        )

        passed = all(metric.passed for metric in metrics)

        return EvalResult(
            case_id=case.id,
            passed=passed,
            response=response,
            tools_used=tools_used,
            metrics=metrics,
        )

