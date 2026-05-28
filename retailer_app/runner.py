from typing import Optional

from google.adk.runners import Runner   
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part    

from .agent import root_agent
from src.utils.runner_utils import extract_user_visible_text

APP_NAME = "retailer_app"

_session_service = InMemorySessionService()
_runner: Optional[Runner] = None
_sessions: dict[str, str] = {}

def get_runner() -> Runner:
    global _runner
    if _runner is None:
        _runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=_session_service,
        )
    return _runner

async def process_retailer_message(user_id: str, message: str) -> str:
    runner = get_runner()
    
    if user_id not in _sessions:
        session = await _session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
        )
        _sessions[user_id] = session.id
        
    session_id = _sessions[user_id]
    content = Content(role="user", parts=[Part(text=message)])
    
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            visible_text = extract_user_visible_text(event.content.parts)
            if visible_text:
                return visible_text
    
    return "Desculpe, não consegui processar sua solicitação no momento."
