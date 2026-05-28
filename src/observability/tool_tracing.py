from contextlib import contextmanager

from src.observability.tracing import get_agent_tracer

@contextmanager
def tool_span(
    agent_name: str,
    span_name: str,
):
    tracer = get_agent_tracer(agent_name)
    
    with tracer.start_as_current_span(
        span_name
    ) as span:
        yield span

