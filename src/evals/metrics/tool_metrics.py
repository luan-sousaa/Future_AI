from src.evals.schemas.eval_result import MetricResult

def evaluate_tool_usage(
    expected_tools: list[str],
    used_tools: list[str],
) -> MetricResult:
    
    missing = [
        tool
        for tool in expected_tools
        if tool not in used_tools
    ]
    
    passed = len(missing) == 0
    
    return MetricResult(
        metric_name="tool_usage",
        passed=passed,
        score=1.0 if passed else 0.0,
        reason=(
            "Todas as tools esperadas foram utilizadas."
            if passed
            else f"Tools ausentes: {missing}"
        ),
    )