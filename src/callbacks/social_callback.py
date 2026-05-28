from google.adk.models import LlmResponse
from google.genai import types

SOCIAL_MESSAGES = {
    "oi",
    "olá",
    "ola",
    "bom dia",
    "boa tarde",
    "boa noite",
}

def social_callback(callback_context, llm_request):
    user_text = (
        callback_context.user_content.parts[0].text
        .strip()
        .lower()
    )

    if user_text not in SOCIAL_MESSAGES:
        return None

    return LlmResponse(
        content=types.Content(
            role="model",
            parts=[
                types.Part.from_text(
                    text="Olá! Como posso ajudar com o inventário?"
                )
            ],
        )
    )