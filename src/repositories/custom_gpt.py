import os

from google.adk.models.lite_llm import LiteLlm

class CustomModel(LiteLlm):
    def __init__(self) -> None:
        model = os.getenv("LITELLM_MODEL")

        if not model:
            raise ValueError("LITELLM_MODEL is not configured.")

        super().__init__(model=model)
