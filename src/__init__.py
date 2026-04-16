from src.agent.retailer_agent import create_agent
from google.adk.agents import LlmAgent

def get_agent() -> LlmAgent:
    return create_agent()

root_agent = get_agent()