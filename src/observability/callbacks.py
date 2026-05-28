from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse

from src.utils.logger import get_logger

logger = get_logger("agent.callbacks")

def before_model_callback(
    callback_context: CallbackContext,
    llm_request,
):
    user_content = getattr(callback_context, "user_content", None)
    
    logger.info("before_model_callback acionado")
    
    if user_content:
        logger.info(f"Mensagem recebida: {user_content}")
    
    return None

def after_model_callback(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
):
    logger.info("after_model_callback acionado")
    
    if (
        llm_response
        and llm_response.content
        and llm_response.content.parts
    ):
        for part in llm_response.content.parts:
            if getattr(part, "text", None):
                logger.info(f"Resposta do agente: {part.text[:300]}")
        
    
    return None

