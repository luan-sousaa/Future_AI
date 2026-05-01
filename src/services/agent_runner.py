from typing import Optional

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

APP_NAME = "retailer_agent"

_session_service = InMemorySessionService()
_runner: Optional[Runner] = None
_sessions: dict[str, str] = {}  # phone_number → session_id


def _get_runner() -> Runner:
    global _runner
    if _runner is None:
        from adk_app.agent import root_agent
        _runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=_session_service,
        )
    return _runner


async def process_message(user_id: str, message: str) -> str:
    runner = _get_runner()

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
        if event.is_final_response():
            if event.content and event.content.parts:
                return event.content.parts[0].text

    return "Desculpe, não consegui processar sua mensagem."
