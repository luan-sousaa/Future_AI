from opentelemetry import trace

from src.utils.logger import get_logger

logger = get_logger("tracing")

def get_agent_tracer(
    agent_name: str,
):
    return trace.get_tracer(
        agent_name
    )

