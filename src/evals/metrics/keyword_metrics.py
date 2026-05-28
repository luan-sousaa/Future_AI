from src.evals.schemas.eval_result import MetricResult

def evaluate_keywords(
    expected_keywords: list[str],
    response: str,
) -> MetricResult:
    
    response_lower = response.lower()
    
    missing = [
        keyword
        for keyword in expected_keywords
        if keyword.lower() not in response_lower
    ]
    
    passed = len(missing) == 0
    
    return MetricResult(
        metric_name="keyword_match",
        passed=passed,
        score=1.0 if passed else 0.0,
        reason=(
            "Todas keywords encontradas."
            if passed
            else f"Keywords ausentes: {missing}"
        ),
    )