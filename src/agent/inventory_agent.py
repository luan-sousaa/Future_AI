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
    check_product_availability,
    get_inactive_products,
    search_product_by_name,
    get_product_by_code,
    get_product_stock_and_price_summary,
    get_product_commercial_context,
    get_critical_stock_products,
    get_inventory_overview,
    get_inventory_diff_by_period,
    get_products_by_stock_status,
    get_top_selling_products,
    get_slow_moving_products,
    get_overstocked_products,
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
            check_product_availability,
            get_inactive_products,
            search_product_by_name,
            get_product_by_code,
            get_product_stock_and_price_summary,
            get_product_commercial_context,
            get_critical_stock_products,
            get_inventory_overview,
            get_inventory_diff_by_period,
            get_products_by_stock_status,
            get_top_selling_products,
            get_slow_moving_products,
            get_overstocked_products,
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
