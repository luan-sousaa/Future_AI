from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse

from src.observability.tracing import get_agent_tracer
from src.utils.logger import get_logger

logger = get_logger("sales.callback")

tracer = get_agent_tracer("retailer_agent")

def before_callback(
    callback_context: CallbackContext,
    llm_request,
):
    with tracer.start_as_current_span("retailer.before_model") as span:
        user_content = getattr(callback_context, "user_content", None)
        
        if user_content:
            span.set_attribute("agent.name", "retailer_agent")
            
            span.set_attribute("user.message", str(user_content))
            
            logger.info(f"[Retailer] - {user_content}")
        
    return None
    
def after_callback(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
):
    with tracer.start_as_current_span("retailer.after_model") as span:
        if(llm_response and llm_response.content and llm_response.content.parts):
            for part in (llm_response.content.parts):
                if getattr(part, "text", None):
                    response_text = (part.text[:300])
                    
                    span.set_attribute("agent.response", response_text)
                    
                    logger.info(f"[Retailer] - Resposta do modelo: {response_text}")
        
    return None