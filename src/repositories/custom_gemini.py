import os
from functools import cached_property
from typing import Optional

from google.adk.models import Gemini
from google.genai import Client, types

class CustomGemini(Gemini):
    api_key: Optional[str] = None

    @cached_property
    def api_client(self):
        effective_key = self.api_key or os.getenv("GOOGLE_API_KEY")

        return Client(
            api_key=effective_key,
        )
