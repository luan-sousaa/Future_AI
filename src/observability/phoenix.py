import os

from opentelemetry import trace 

from opentelemetry.sdk.trace import (
    TracerProvider,
)

from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
)

from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)

from src.utils.logger import get_logger

logger = get_logger("phoenix")

def setup_phoenix():
    endpoint = os.getenv(
        "PHOENIX_COLLECTOR_ENDPOINT",
        "http://localhost:6006/v1/traces",
    )
    
    logger.info(f"Conectando Phoenix em: {endpoint}")
    
    provider = TracerProvider()
    
    exporter = OTLPSpanExporter(
        endpoint=endpoint,
    )
    
    processor = BatchSpanProcessor(exporter)
    
    provider.add_span_processor(processor)
    
    trace.set_tracer_provider(provider)
    
    logger.info("Phoenix configurado com sucesso")
    
    return provider

