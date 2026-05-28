from pydantic import BaseModel
from typing import Dict, Any, List


class MetricResult(BaseModel):
    metric_name: str
    passed: bool
    score: float
    reason: str


class EvalResult(BaseModel):
    case_id: str
    passed: bool
    response: str

    tools_used: List[str]

    metrics: List[MetricResult]

    metadata: Dict[str, Any] = {}