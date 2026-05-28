import os

from phoenix.otel import register

from src.utils.logger import get_logger

logger = get_logger("phoenix")

_tracer_provider: dict[str, object] = {}

def setup_phoenix(
    project_name: str
):
    if project_name in _tracer_provider:
        return _tracer_provider[project_name]
    
    endpoint = os.getenv("PHOENIX_ENDPOINT", "http://localhost:6006/v1/traces")
    
    logger.info(f"Configuring Phoenix | project={project_name} | endpoint={endpoint}")
    
    tracer_provider = register(
        project_name=project_name,
        endpoint=endpoint,
        auto_instrument=True,
    )
    
    _tracer_provider[project_name] = tracer_provider
      
    logger.info(f"Phoenix configured successfully | project={project_name}")
    
    return tracer_provider

