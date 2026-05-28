from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse

from src.observability.tracing import get_agent_tracer

from src.utils.logger import get_logger

logger = get_logger("inventory_callback")

tracer = get_agent_tracer("inventory_agent")

def before_model_callback(
    callback_context: CallbackContext,
    llm_request,
):
    with tracer.start_as_current_span("inventory.before_model") as span:
        user_content = getattr(callback_context, "user_content", None)
        
        if user_content:
            span.set_attribute("agent.name","inventory-agent", )
            
            span.set_attribute("user.message", str(user_content),)
            
            logger.info(f"[Inventory] - {user_content}")
    
    return None

def after_model_callback(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
):
    with tracer.start_as_current_span("inventory.after_model") as span:
        if(llm_response and llm_response.content and llm_response.content.parts):
            for part in (llm_response.content.parts):
                if getattr(part, "text", None):
                    response_text = (part.text[:300])
                    
                    span.set_attribute("agent.response", response_text)
                    
                    logger.info(f"[Inventory] - Resposta do modelo: {response_text}")
    
    return None
                    