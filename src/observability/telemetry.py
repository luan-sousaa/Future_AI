import time
from functools import wraps

from src.utils.logger import get_logger
from src.observability.tracing import get_agent_tracer

logger = get_logger("telemetry")

def track_tool_execution(
    agent_name: str,
    tool_name: str,
):
    tracer = get_agent_tracer(agent_name)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            
            with tracer.start_as_current_span(
                tool_name
            ) as span:
                span.set_attribute(
                    "agent.name",
                    agent_name,
                )
                
                span.set_attribute(
                    "tool.name",
                    tool_name,
                )
                
                logger.info(f"Executando ferramenta: {tool_name} do agente: {agent_name}")
                
                try:
                    result = func(
                        *args,
                        **kwargs,
                    )
                    
                    elapsed = (
                        time.perf_counter() - start
                    )
                    
                    span.set_attribute(
                        "tool.execution_time",
                        elapsed,
                    )
                    
                    logger.info(f"Ferramenta {tool_name} executada em {elapsed:.2f} segundos")
                    
                    return result
                
                except Exception as e:
                    span.record_exception(e)
                    
                    span.set_attribute(
                        "tool.success",
                        False,  
                    )
                    
                    logger.exception(f"Erro ao executar ferramenta: {tool_name} do agente: {agent_name}")
                    raise
            
        return wrapper
    
    return decorator

