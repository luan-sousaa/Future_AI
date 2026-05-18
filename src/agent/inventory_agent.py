import os
import re
from typing import Optional

from dotenv import load_dotenv

from google.adk.agents import LlmAgent  
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from google.adk.planners import BuiltInPlanner
from google.genai import types  

from src.prompts.inventory_prompt import create_inventory_prompt
from src.repositories.custom_gemini import CustomGemini

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

from src.services.adk_evaluator import ADKEvaluatorWebService

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL = os.getenv("MODEL")
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "gemini").lower()

THINKING_BLOCK_PATTERN = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
HARMONY_ANALYSIS_PATTERN = re.compile(
    r"<\|start\|>assistant\s*<\|channel\|>analysis.*?<\|end\|>",
    re.DOTALL | re.IGNORECASE,
)
HARMONY_FINAL_PATTERN = re.compile(
    r"<\|start\|>assistant\s*<\|channel\|>final(?:\s+\w+)?\s*<\|message\|>(.*?)(?:<\|end\|>|$)",
    re.DOTALL | re.IGNORECASE,
)


def _create_model():
    if MODEL_PROVIDER in {"openai", "litellm"}:
        from src.repositories.custom_gpt import CustomModel

        return CustomModel()

    if MODEL_PROVIDER in {"gemini", "google"}:
        return CustomGemini(
            api_key=GOOGLE_API_KEY,
            model=MODEL,
        )

    raise ValueError(
        "MODEL_PROVIDER must be one of: gemini, google, openai, litellm."
    )


def _create_planner() -> Optional[BuiltInPlanner]:
    if MODEL_PROVIDER not in {"gemini", "google"}:
        return None

    return BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=False,
        )
    )


def _sanitize_model_text(text: str) -> str:
    final_messages = HARMONY_FINAL_PATTERN.findall(text)

    if final_messages:
        text = final_messages[-1]

    text = THINKING_BLOCK_PATTERN.sub("", text)
    text = HARMONY_ANALYSIS_PATTERN.sub("", text)

    return text.strip()


def hide_reasoning_callback(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> Optional[LlmResponse]:
    if not llm_response.content or not llm_response.content.parts:
        return None

    changed = False
    for part in llm_response.content.parts:
        if not getattr(part, "text", None):
            continue

        sanitized_text = _sanitize_model_text(part.text)
        if sanitized_text != part.text:
            part.text = sanitized_text
            changed = True

    return llm_response if changed else None


def create_inventory_agent() -> LlmAgent:
    model = _create_model()
    
    eval_service = ADKEvaluatorWebService("inventory_agent")
    
    agent = LlmAgent(
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
        planner = _create_planner(),
        generate_content_config = types.GenerateContentConfig(
            temperature = 1.0,
        ),
        after_model_callback = hide_reasoning_callback,
    )
    
    agent._eval_service = eval_service
    
    return agent

root_agent = create_inventory_agent()
