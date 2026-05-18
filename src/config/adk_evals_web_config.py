"""
ADK Evals - Estruturas compatveis com Web UI
Documentacao: https://adk.dev/evaluate/
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 1. EVAL METRIC (Metricas customizaveis via Web UI)
# ═══════════════════════════════════════════════════════════════

@dataclass
class EvalMetricConfig:
    """Configuracao de metrica customizavel (Web UI sliders)"""
    name: str
    description: str
    min_threshold: float
    max_threshold: float
    default_threshold: float
    unit: str  # "score", "percentage", "ms"


class WebUIMetrics:
    """Metricas que podem ser ajustadas via Web UI sliders"""
    
    TOOL_TRAJECTORY_SCORE = EvalMetricConfig(
        name="tool_trajectory_avg_score",
        description="Score medio da trajectory de tools",
        min_threshold=0.0,
        max_threshold=10.0,
        default_threshold=8.0,
        unit="score"
    )
    
    RESPONSE_MATCH_SCORE = EvalMetricConfig(
        name="response_match_score",
        description="Score de correspondencia da resposta",
        min_threshold=0.0,
        max_threshold=100.0,
        default_threshold=80.0,
        unit="percentage"
    )
    
    LATENCY_THRESHOLD = EvalMetricConfig(
        name="latency_threshold_ms",
        description="Latencia maxima aceitavel",
        min_threshold=500.0,
        max_threshold=5000.0,
        default_threshold=3000.0,
        unit="ms"
    )
    
    @classmethod
    def all_metrics(cls) -> List[EvalMetricConfig]:
        """Retorna todas as metricas para Web UI"""
        return [
            cls.TOOL_TRAJECTORY_SCORE,
            cls.RESPONSE_MATCH_SCORE,
            cls.LATENCY_THRESHOLD,
        ]


# ═══════════════════════════════════════════════════════════════
# 2. SESSION (Sessao de conversa - criada via Web UI)
# ═══════════════════════════════════════════════════════════════

@dataclass
class ChatMessage:
    """Mensagem individual na sessao"""
    id: str
    role: str  # "user" ou "assistant"
    content: str
    timestamp: str


@dataclass
class AgentSession:
    """Sessao de conversa com o agente (criada via Web UI)"""
    session_id: str
    agent_name: str
    messages: List[ChatMessage]
    created_at: str
    updated_at: str
    
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp,
                }
                for m in self.messages
            ],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ═══════════════════════════════════════════════════════════════
# 3. EVAL CASE (Caso de teste - criado via "Add current session")
# ═══════════════════════════════════════════════════════════════

@dataclass
class EvalCase:
    """Um caso de teste (criado via Web UI "Add current session")"""
    case_id: str
    session_id: str
    eval_set_id: str
    user_input: str
    expected_output: str
    agent_messages: List[str]  # Mensagens do agente na sessao
    created_at: str
    edited_at: Optional[str]
    tags: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)


class EvalCaseManager:
    """Gerencia casos de teste (armazenados via Web UI)"""
    
    def __init__(self):
        self.cases: Dict[str, EvalCase] = {}
    
    def create_from_session(
        self,
        case_id: str,
        session: AgentSession,
        eval_set_id: str,
        user_input: str,
        expected_output: str
    ) -> EvalCase:
        """Cria eval case a partir de sessao Web UI"""
        
        agent_messages = [
            m.content
            for m in session.messages
            if m.role == "assistant"
        ]
        
        case = EvalCase(
            case_id=case_id,
            session_id=session.session_id,
            eval_set_id=eval_set_id,
            user_input=user_input,
            expected_output=expected_output,
            agent_messages=agent_messages,
            created_at=datetime.now().isoformat(),
            edited_at=None,
            tags=[]
        )
        
        self.cases[case_id] = case
        logger.info(f"Eval case criado: {case_id}")
        
        return case
    
    def edit_case(
        self,
        case_id: str,
        expected_output: Optional[str] = None,
        agent_messages: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> EvalCase:
        """Edita caso de teste (via Web UI edit icon)"""
        
        if case_id not in self.cases:
            raise ValueError(f"Caso nao encontrado: {case_id}")
        
        case = self.cases[case_id]
        
        if expected_output is not None:
            case.expected_output = expected_output
        
        if agent_messages is not None:
            case.agent_messages = agent_messages
        
        if tags is not None:
            case.tags = tags
        
        case.edited_at = datetime.now().isoformat()
        
        logger.info(f"Eval case editado: {case_id}")
        
        return case
    
    def delete_case(self, case_id: str):
        """Deleta caso de teste"""
        if case_id in self.cases:
            del self.cases[case_id]
            logger.info(f"Eval case deletado: {case_id}")
    
    def export_to_jsonl(self, filepath: str):
        """Exporta casos para JSONL (formato ADK)"""
        with open(filepath, 'w') as f:
            for case in self.cases.values():
                f.write(json.dumps(case.to_dict()) + "\n")
        
        logger.info(f"Eval cases exportados: {filepath}")


# ═══════════════════════════════════════════════════════════════
# 4. TRACE (Rastreamento de execucao - capturado automaticamente)
# ═══════════════════════════════════════════════════════════════

@dataclass
class TraceEvent:
    """Um evento na trace"""
    event_type: str  # "llm_call", "tool_call", "tool_result", "error"
    timestamp: str
    data: Dict[str, Any]


class ExecutionTrace:
    """
    Trace de execucao (capturada automaticamente pelo ADK)
    Inclui: LLM calls, tool calls, responses
    """
    
    def __init__(self, trace_id: str, user_message: str):
        self.trace_id = trace_id
        self.user_message = user_message
        self.events: List[TraceEvent] = []
        self.created_at = datetime.now().isoformat()
    
    def add_event(self, event_type: str, data: Dict):
        """Adiciona evento a trace"""
        event = TraceEvent(
            event_type=event_type,
            timestamp=datetime.now().isoformat(),
            data=data
        )
        self.events.append(event)
    
    def to_dict(self) -> Dict:
        return {
            "trace_id": self.trace_id,
            "user_message": self.user_message,
            "events": [
                {
                    "event_type": e.event_type,
                    "timestamp": e.timestamp,
                    "data": e.data,
                }
                for e in self.events
            ],
            "created_at": self.created_at,
        }
    
    def to_graph_format(self) -> Dict:
        """Converte para formato de grafo (Web UI Graph tab)"""
        nodes = []
        edges = []
        
        for i, event in enumerate(self.events):
            node_id = f"event_{i}"
            
            nodes.append({
                "id": node_id,
                "label": event.event_type,
                "type": event.event_type,
                "data": event.data,
            })
            
            if i > 0:
                edges.append({
                    "source": f"event_{i-1}",
                    "target": node_id,
                })
        
        return {
            "nodes": nodes,
            "edges": edges,
        }


# ═══════════════════════════════════════════════════════════════
# 5. EVALUATION RUN (Execucao de avaliacao - via Web UI button)
# ═══════════════════════════════════════════════════════════════

@dataclass
class EvaluationMetricResult:
    """Resultado de uma metrica para um caso"""
    metric_name: str
    actual_value: float
    threshold: float
    passed: bool


@dataclass
class EvaluationRunResult:
    """Resultado de uma execucao de avaliacao (via "Run Evaluation" button)"""
    run_id: str
    case_id: str
    passed: bool
    timestamp: str
    metric_results: Dict[str, EvaluationMetricResult]
    actual_output: str
    expected_output: str
    failure_reason: Optional[str]
    
    def to_dict(self) -> Dict:
        return {
            "run_id": self.run_id,
            "case_id": self.case_id,
            "passed": self.passed,
            "timestamp": self.timestamp,
            "metric_results": {
                k: {
                    "metric_name": v.metric_name,
                    "actual_value": v.actual_value,
                    "threshold": v.threshold,
                    "passed": v.passed,
                }
                for k, v in self.metric_results.items()
            },
            "actual_output": self.actual_output,
            "expected_output": self.expected_output,
            "failure_reason": self.failure_reason,
        }


class EvaluationRunHistory:
    """Historico de runs de avaliacao"""
    
    def __init__(self):
        self.runs: Dict[str, EvaluationRunResult] = {}
    
    def add_run(self, run: EvaluationRunResult):
        """Adiciona run ao historico"""
        self.runs[run.run_id] = run
        logger.info(f"Run adicionado: {run.run_id}")
    
    def export_to_json(self, filepath: str):
        """Exporta historico para JSON"""
        data = {
            "total_runs": len(self.runs),
            "runs": [r.to_dict() for r in self.runs.values()]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Historico exportado: {filepath}")


# ═══════════════════════════════════════════════════════════════
# 6. EVALUATION ENGINE (Motor de avaliacao customizado)
# ═══════════════════════════════════════════════════════════════

class EvaluationEngine:
    """
    Motor de avaliacao que usa metricas customizaveis (Web UI sliders)
    """
    
    def __init__(self):
        self.run_history = EvaluationRunHistory()
    
    def run_evaluation(
        self,
        case: EvalCase,
        actual_output: str,
        trace: ExecutionTrace,
        metric_thresholds: Dict[str, float]
    ) -> EvaluationRunResult:
        """
        Executa avaliacao com metricas customizadas (do Web UI)
        
        metric_thresholds: valores dos sliders do Web UI
            {
                "tool_trajectory_avg_score": 8.0,
                "response_match_score": 80.0,
                "latency_threshold_ms": 3000.0,
            }
        """
        
        from uuid import uuid4
        run_id = f"run_{uuid4().hex[:8]}"
        
        logger.info(f"Avaliando caso {case.case_id} com run {run_id}")
        
        metric_results = {}
        all_passed = True
        
        # 1. Avaliar tool trajectory score
        tool_score = self._evaluate_tool_trajectory(trace)
        threshold = metric_thresholds.get("tool_trajectory_avg_score", 8.0)
        
        metric_results["tool_trajectory_avg_score"] = EvaluationMetricResult(
            metric_name="tool_trajectory_avg_score",
            actual_value=tool_score,
            threshold=threshold,
            passed=tool_score >= threshold
        )
        
        if tool_score < threshold:
            all_passed = False
        
        # 2. Avaliar response match score
        match_score = self._evaluate_response_match(
            actual_output,
            case.expected_output
        )
        threshold = metric_thresholds.get("response_match_score", 80.0)
        
        metric_results["response_match_score"] = EvaluationMetricResult(
            metric_name="response_match_score",
            actual_value=match_score,
            threshold=threshold,
            passed=match_score >= threshold
        )
        
        if match_score < threshold:
            all_passed = False
        
        # 3. Avaliar latencia
        latency_ms = self._evaluate_latency(trace)
        threshold = metric_thresholds.get("latency_threshold_ms", 3000.0)
        
        metric_results["latency_ms"] = EvaluationMetricResult(
            metric_name="latency_ms",
            actual_value=latency_ms,
            threshold=threshold,
            passed=latency_ms <= threshold
        )
        
        if latency_ms > threshold:
            all_passed = False
        
        # Determinar razao de falha
        failure_reason = None
        if not all_passed:
            failures = [
                f"{k}: {v.actual_value:.1f} vs {v.threshold}"
                for k, v in metric_results.items()
                if not v.passed
            ]
            failure_reason = "; ".join(failures)
        
        result = EvaluationRunResult(
            run_id=run_id,
            case_id=case.case_id,
            passed=all_passed,
            timestamp=datetime.now().isoformat(),
            metric_results=metric_results,
            actual_output=actual_output,
            expected_output=case.expected_output,
            failure_reason=failure_reason
        )
        
        self.run_history.add_run(result)
        
        return result
    
    def _evaluate_tool_trajectory(self, trace: ExecutionTrace) -> float:
        """Avalia score medio da trajectory de tools"""
        
        tool_events = [
            e for e in trace.events
            if e.event_type in ["tool_call", "tool_result"]
        ]
        
        if not tool_events:
            return 10.0
        
        # Score simples: 10 se nenhum erro
        has_errors = any(
            e.event_type == "error"
            for e in trace.events
        )
        
        return 5.0 if has_errors else 10.0
    
    def _evaluate_response_match(
        self,
        actual: str,
        expected: str
    ) -> float:
        """Avalia similaridade entre resposta atual e esperada (0-100)"""
        
        if not expected or not actual:
            return 0.0
        
        # Matching simples por palavras-chave
        expected_words = set(expected.lower().split())
        actual_words = set(actual.lower().split())
        
        if not expected_words:
            return 100.0
        
        match_count = len(expected_words & actual_words)
        match_percentage = (match_count / len(expected_words)) * 100
        
        return min(100.0, match_percentage)
    
    def _evaluate_latency(self, trace: ExecutionTrace) -> float:
        """Calcula latencia total em ms"""
        
        if not trace.events:
            return 0.0
        
        first_event = trace.events[0]
        last_event = trace.events[-1]
        
        first_time = datetime.fromisoformat(first_event.timestamp)
        last_time = datetime.fromisoformat(last_event.timestamp)
        
        duration_ms = (last_time - first_time).total_seconds() * 1000
        
        return duration_ms