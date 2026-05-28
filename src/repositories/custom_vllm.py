import os

from google.adk.models.lite_llm import LiteLlm

class CustomVLlm(LiteLlm):
    def __init__(self) -> None:
        model = os.getenv(
            "VLLM_MODEL",
            "openai/Qwen/Qwen2.5-7B-Instruct"
        )
        
        super().__init__(
             model=model,
            api_base="http://localhost:8000/v1",
            api_key=os.getenv("OPENAI_API_KEY"),
        )