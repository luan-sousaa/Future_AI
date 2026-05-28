import os

from dotenv import load_dotenv

from src.repositories.custom_gemini import CustomGemini

load_dotenv()

MODEL_PROVIDER = os.getenv(
    "MODEL_PROVIDER",
    "gemini"
).lower()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL = os.getenv("MODEL")


def create_model():
    """
    Factory responsável por instanciar o provider/model correto.
    """

    if MODEL_PROVIDER in {"openai", "litellm"}:
        from src.repositories.custom_gpt import CustomModel

        return CustomModel()

    if MODEL_PROVIDER in {"gemini", "google"}:
        return CustomGemini(
            api_key=GOOGLE_API_KEY,
            model=MODEL,
        )

    if MODEL_PROVIDER == "ollama":
        from src.repositories.custom_ollama import CustomOllama

        return CustomOllama()

    if MODEL_PROVIDER == "vllm":
        from src.repositories.custom_vllm import CustomVLlm

        return CustomVLlm()

    raise ValueError(
        "MODEL_PROVIDER must be one of: "
        "gemini, google, openai, litellm, ollama, vllm."
    )