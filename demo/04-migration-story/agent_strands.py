from strands import Agent
from strands.models import BedrockModel
from strands.tools import tool


@tool
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    return f"72°F in {city}"


agent = Agent(
    model=BedrockModel(model_id="anthropic.claude-sonnet-4-20250514"),
    tools=[get_weather],
    system_prompt="You are a helpful weather assistant.",
)
