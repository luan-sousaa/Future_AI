"""
Servico de Evals para ADK Web UI
Responsabilidades:
  - Gerenciar eval sets (criados via Web UI)
  - Gerenciar eval cases (salvos via "Add current session")
  - Executar avaliacoes (via "Run Evaluation" button)
  - Armazenar traces automaticamente
"""

import logging
from typing import Dict, List, Optional
from uuid import uuid4

from src.config.adk_evals_web_config import (
    WebUIMetrics,
    AgentSession,
    ChatMessage,
    EvalCaseManager,
    ExecutionTrace,
    EvaluationEngine,
)

logger = logging.getLogger(__name__)


class ADKEvaluatorWebService:
    """
    Servico para integrar com ADK Web UI
    
    Fluxo:
    1. User interage com agente via Web UI
    2. Sessao e capturada
    3. User clica "Add current session" → eval case criado
    4. User seleciona case e ajusta sliders
    5. User clica "Run Evaluation" → avaliacao executada
    6. Resultados mostrados no Web UI
    """
    
    def __init__(self, agent_name: str = "inventory_agent"):
        self.agent_name = agent_name
        self.case_manager = EvalCaseManager()
        self.eval_engine = EvaluationEngine()
        self.traces: Dict[str, ExecutionTrace] = {}
        
        logger.info(f"ADKEvaluatorWebService inicializado: {agent_name}")
    
    # ═══════════════════════════════════════════════════════════════
    # FLUXO 1: User interage com agente (Web UI chat)
    # ═══════════════════════════════════════════════════════════════
    
    def create_session(self) -> AgentSession:
        """Cria nova sessao (Web UI new chat)"""
        
        session = AgentSession(
            session_id=f"session_{uuid4().hex[:8]}",
            agent_name=self.agent_name,
            messages=[],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        logger.info(f"Sessao criada: {session.session_id}")
        
        return session
    
    def add_message_to_session(
        self,
        session: AgentSession,
        role: str,
        content: str
    ) -> ChatMessage:
        """Adiciona mensagem a sessao (Web UI chat interaction)"""
        
        message = ChatMessage(
            id=f"msg_{uuid4().hex[:8]}",
            role=role,
            content=content,
            timestamp=datetime.now().isoformat()
        )
        
        session.messages.append(message)
        session.updated_at = datetime.now().isoformat()
        
        return message
    
    # ═══════════════════════════════════════════════════════════════
    # FLUXO 2: User clica "Add current session" → eval case criado
    # ═══════════════════════════════════════════════════════════════
    
    def create_eval_case_from_session(
        self,
        session: AgentSession,
        eval_set_id: str,
        expected_output: str,
        tags: List[str] = None
    ) -> str:
        """
        Cria eval case a partir da sessao
        (Equivalente ao Web UI "Add current session" button)
        """
        
        case_id = f"case_{uuid4().hex[:8]}"
        
        # Extrair user input (primeira mensagem do usuario)
        user_input = next(
            (m.content for m in session.messages if m.role == "user"),
            ""
        )
        
        case = self.case_manager.create_from_session(
            case_id=case_id,
            session=session,
            eval_set_id=eval_set_id,
            user_input=user_input,
            expected_output=expected_output
        )
        
        if tags:
            case.tags = tags
        
        logger.info(f"Eval case criado a partir de sessao: {case_id}")
        
        return case_id
    
    def get_eval_case(self, case_id: str):
        """Retorna eval case para edicao (Web UI edit icon)"""
        return self.case_manager.cases.get(case_id)
    
    def edit_eval_case(
        self,
        case_id: str,
        expected_output: Optional[str] = None,
        agent_messages: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ):
        """
        Edita eval case (Web UI edit interface)
        
        Permite:
        - Modificar agent text responses
        - Deletar mensagens individuais
        - Atualizar expected output
        """
        
        return self.case_manager.edit_case(
            case_id=case_id,
            expected_output=expected_output,
            agent_messages=agent_messages,
            tags=tags
        )
    
    def delete_eval_case(self, case_id: str):
        """Deleta eval case (Web UI delete button)"""
        self.case_manager.delete_case(case_id)
        logger.info(f"Eval case deletado: {case_id}")
    
    # ═══════════════════════════════════════════════════════════════
    # FLUXO 3: Capturar traces automaticamente
    # ═══════════════════════════════════════════════════════════════
    
    def create_trace(self, user_message: str) -> ExecutionTrace:
        """Cria trace para rastrear execucao (Web UI Trace tab)"""
        
        trace = ExecutionTrace(
            trace_id=f"trace_{uuid4().hex[:8]}",
            user_message=user_message
        )
        
        self.traces[trace.trace_id] = trace
        
        return trace
    
    def add_trace_event(
        self,
        trace_id: str,
        event_type: str,
        data: Dict
    ):
        """Adiciona evento a trace (capturado do agente)"""
        
        if trace_id not in self.traces:
            logger.warning(f"Trace nao encontrado: {trace_id}")
            return
        
        trace = self.traces[trace_id]
        trace.add_event(event_type, data)
    
    def get_trace_graph(self, trace_id: str) -> Dict:
        """Retorna trace em formato de grafo (Web UI Graph tab)"""
        
        trace = self.traces.get(trace_id)
        if not trace:
            return {}
        
        return trace.to_graph_format()
    
    # ═══════════════════════════════════════════════════════════════
    # FLUXO 4: User ajusta sliders e clica "Run Evaluation"
    # ═══════════════════════════════════════════════════════════════
    
    def get_available_metrics(self) -> List[Dict]:
        """
        Retorna metricas disponveis para Web UI sliders
        (EVALUATION METRIC dialog)
        """
        
        metrics = []
        for metric in WebUIMetrics.all_metrics():
            metrics.append({
                "name": metric.name,
                "description": metric.description,
                "min": metric.min_threshold,
                "max": metric.max_threshold,
                "default": metric.default_threshold,
                "unit": metric.unit,
            })
        
        return metrics
    
    def run_evaluation(
        self,
        case_id: str,
        actual_output: str,
        trace_id: str,
        metric_thresholds: Dict[str, float]
    ):
        """
        Executa avaliacao (equivalente ao Web UI "Start" button)
        
        Args:
            case_id: ID do caso a avaliar
            actual_output: Output real do agente
            trace_id: ID da trace para analisar
            metric_thresholds: Valores dos sliders (do Web UI)
        
        Returns:
            EvaluationRunResult
        """
        
        # Obter case
        case = self.case_manager.cases.get(case_id)
        if not case:
            logger.error(f"Case nao encontrado: {case_id}")
            return None
        
        # Obter trace
        trace = self.traces.get(trace_id)
        if not trace:
            logger.error(f"Trace nao encontrado: {trace_id}")
            return None
        
        # Executar avaliacao com thresholds customizados
        result = self.eval_engine.run_evaluation(
            case=case,
            actual_output=actual_output,
            trace=trace,
            metric_thresholds=metric_thresholds
        )
        
        return result
    
    # ═══════════════════════════════════════════════════════════════
    # EXPORTS E RELATARIOS
    # ═══════════════════════════════════════════════════════════════
    
    def export_eval_set(self, filepath: str = ".adk/artifacts/eval_set.jsonl"):
        """Exporta eval set em formato JSONL"""
        self.case_manager.export_to_jsonl(filepath)
    
    def export_eval_results(self, filepath: str = ".adk/artifacts/eval_results.json"):
        """Exporta resultados de runs"""
        self.eval_engine.run_history.export_to_json(filepath)
    
    def get_evaluation_summary(self) -> Dict:
        """Retorna resumo da avaliacao"""
        
        runs = self.eval_engine.run_history.runs.values()
        
        if not runs:
            return {
                "total_runs": 0,
                "pass_rate": 0.0,
                "failed_cases": [],
            }
        
        total = len(runs)
        passed = sum(1 for r in runs if r.passed)
        failed = [r.case_id for r in runs if not r.passed]
        
        return {
            "total_runs": total,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
            "failed_cases": failed,
            "runs": [r.to_dict() for r in runs],
        }