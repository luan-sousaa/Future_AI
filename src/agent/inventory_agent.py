from google.adk.agents import LlmAgent
from google.genai import types

from src.prompts.inventory_prompt import create_inventory_prompt

from src.factories.model_factory import create_model
from src.factories.planner_factory import create_planner

from src.callbacks.sanitize_callback import (
    hide_reasoning_callback,
)

from src.callbacks.social_callback import (
    social_callback,
)

from src.tools.mongo_tools import (
    search_product_by_name,
    get_product_commercial_context,
    get_inventory_overview,
    get_inventory_diff_by_period,
    list_low_stock_products,
    list_out_of_stock_products,
    list_overstocked_products,
    list_inactive_products,
    list_top_selling_products,
    list_slow_moving_products,
)

from src.bootstrap import bootstrap_app

def create_inventory_agent() -> LlmAgent:
    return LlmAgent(
        name="inventory_agent",

        model=create_model(),

        planner=create_planner(),

        description=(
            "Inventory operations agent specialized "
            "in stock analysis and replenishment."
        ),

        instruction=create_inventory_prompt(),

        tools=[
            search_product_by_name,
            get_product_commercial_context,
            get_inventory_overview,
            get_inventory_diff_by_period,
            list_low_stock_products,
            list_out_of_stock_products,
            list_overstocked_products,
            list_inactive_products,
            list_top_selling_products,
            list_slow_moving_products,
        ],

        generate_content_config=types.GenerateContentConfig(
            temperature=0.05,
        ),

        before_model_callback=social_callback,

        after_model_callback=[
            hide_reasoning_callback,
        ],
    )


bootstrap_app(project_name="inventory_agent")
root_agent = create_inventory_agent()
