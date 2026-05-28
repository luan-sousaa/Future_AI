from google.adk.agents import LlmAgent
from google.genai import types

from src.prompts.retailer_prompt import create_prompt

from src.factories.model_factory import create_model
from src.factories.planner_factory import create_planner

from src.callbacks.sanitize_callback import (
    hide_reasoning_callback,
)

from src.tools.mongo_tools import (
    search_product_by_name,
    get_product_by_code,
    get_product_stock_and_price_summary,
    check_product_availability,
)

from src.tools.payment_tools import processar_pagamento

from src.bootstrap import bootstrap_app

def create_agent() -> LlmAgent:
    return LlmAgent(
        name="retailer_agent",

        model=create_model(),

        planner=create_planner(),

        description=(
            "Retail sales agent specialized in product discovery, "
            "stock validation, and payment flow."
        ),

        instruction=create_prompt(),

        tools=[
            search_product_by_name,
            get_product_by_code,
            get_product_stock_and_price_summary,
            check_product_availability,
            processar_pagamento,
        ],

        generate_content_config=types.GenerateContentConfig(
            temperature=0.2,
        ),

        after_model_callback=[
            hide_reasoning_callback,
        ],
    )
    

bootstrap_app(project_name="retailer_agent")
root_agent = create_agent()
