import os
from typing import Optional

from dotenv import load_dotenv

from google.adk.planners import BuiltInPlanner
from google.genai import types

load_dotenv()

MODEL_PROVIDER = os.getenv(
    "MODEL_PROVIDER",
    "gemini"
).lower()


def create_planner() -> Optional[BuiltInPlanner]:
    """
    Cria planner apenas para providers compatíveis.
    """

    if MODEL_PROVIDER not in {"gemini", "google"}:
        return None

    return BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=False,
        )
    )