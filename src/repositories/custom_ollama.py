import os

from google.adk.models.lite_llm import LiteLlm

class CustomOllama(LiteLlm):
    model_config = {
        "arbitrary_types_allowed": True
    }

    def __init__(self):
        model = os.getenv("OLLAMA_MODEL")

        if not model:
            raise ValueError(
                "OLLAMA_MODEL not configured."
            )

        api_base = os.getenv(
            "OLLAMA_API_BASE",
            "http://localhost:11434",
        )

        super().__init__(
            model=f"ollama_chat/{model}",
            api_base=api_base,
        )