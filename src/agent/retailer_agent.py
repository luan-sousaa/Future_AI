from dotenv import load_dotenv
import os

from google.adk.agents import LlmAgent
from google.adk.planners import BuiltInPlanner

from google.genai import types

from src.prompts.retailer_prompt import create_prompt
from src.repositories.custom_gemini import CustomGemini

from src.tools.mongo_tools import (
    search_product_by_name,
    get_product_by_code,
    get_product_stock_and_price_summary,
    check_product_availability
)

from src.tools.payment_tools import processar_pagamento

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
            search_product_by_name,
            get_product_by_code,
            get_product_stock_and_price_summary,
            check_product_availability,
            processar_pagamento
        ],
        planner=BuiltInPlanner(
            thinking_config=types.ThinkingConfig(
                include_thoughts=False,
            ),
        ),
        generate_content_config= types.GenerateContentConfig(
            temperature=1.0
        )
    )
    
 