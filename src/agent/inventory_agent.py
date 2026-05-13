from dotenv import load_dotenv
import os

from google.adk.agents import LlmAgent  
from google.adk.planners import BuiltInPlanner
from google.genai import types  

from src.prompts.inventory_prompt import create_inventory_prompt
from src.repositories.custom_gemini import CustomGemini
from src.repositories.custom_gpt import CustomModel

from src.tools.mongo_tools import (
    check_product_availability,
    get_inactive_products,
    search_product_by_name,
    get_product_by_code,
    get_product_stock_and_price_summary,
    get_critical_stock_products,
    get_inventory_overview,
    get_inventory_diff_by_period
)

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL = os.getenv("MODEL")

def create_inventory_agent() -> LlmAgent:
    model = CustomGemini(
        api_key = GOOGLE_API_KEY,
        model = MODEL,
    )
    
    return LlmAgent(
        name = "inventory_agent",
        model=model,
        description = "An agent specialized in stock availability, inventory monitoring, and stock health analysis.",
        instruction = create_inventory_prompt(),
        tools = [
            check_product_availability,
            get_inactive_products,
            search_product_by_name,
            get_product_by_code,
            get_product_stock_and_price_summary,
            get_critical_stock_products,
            get_inventory_overview,
            get_inventory_diff_by_period
        ],
        planner = BuiltInPlanner(
            thinking_config=types.ThinkingConfig(
                include_thoughts=False,
            )
        ),
        generate_content_config = types.GenerateContentConfig(
            temperature = 0.6,
        ),
    )
