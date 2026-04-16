from dotenv import load_dotenv
import os

from google.adk.agents import LlmAgent
from google.adk.planners import BuiltInPlanner

from google.genai import types

from src.prompts.prompt import create_prompt
from src.repositories.custom_gemini import CustomGemini
from Future_AI.src.tools.db_tools_mocked import (
    search_for_product_name,
    get_product_details,
    get_prices_summary
)

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL=os.getenv("MODEL")

def create_agent() -> LlmAgent:
    model = CustomGemini(
        api_key=GOOGLE_API_KEY,
        model=MODEL 
    )
    
    return LlmAgent(
        name = "retailer_agent",
        model=model,
        description="An agent that helps retailers optimize their inventory management and sales strategies.",
        instruction=create_prompt(),
        tools = [
            search_for_product_name,
            get_product_details,
            get_prices_summary
        ],
        planner=BuiltInPlanner(
            thinking_config=types.ThinkingConfig(
                include_thoughts=False,
                thinking_level="low"
            ),
        ),
        generate_content_config= types.GenerateContentConfig(
            temperature=1.0
        )
    )
    
