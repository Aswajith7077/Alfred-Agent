from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from dotenv import load_dotenv


load_dotenv()


def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


llm = ChatOllama(model="gemma4:e2b", base_url="http://127.0.0.1:11434")

agent = create_agent(
    model=llm,
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What's the weather in San Francisco?"}]}
)
print(result["messages"][-1].content_blocks)
