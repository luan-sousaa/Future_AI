from src.evals.schemas.eval_result import MetricResult

def evaluate_response_quality(
    response: str,
) -> MetricResult:
    
    too_short = len(response.strip()) < 15
    
    if too_short:
        return MetricResult(
            metric_name="response_quality",
            passed=False,
            score=0.0,
            reason="Resposta muito curta.",
        )
        
    return MetricResult(
        metric_name="response_quality",
        passed=True,
        score=1.0,
        reason="Resposta operacional válida.",
    )
