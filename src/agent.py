from google.adk.agents import LlmAgent

from src.agent.retailer_agent import create_agent


def get_agent() -> LlmAgent:
    return create_agent()