from agents import Agent
from config import Settings
from container import ServiceContainer


def create_agent() -> Agent:
    container: ServiceContainer = ServiceContainer()
    settings: Settings = container.settings

    agent: Agent = Agent(
        voice=settings.VOICE,
        prompt_manager=container.prompt_manager,
        config=container.ollama_config,
        integrations=container.get_tools(),
    )

    return agent
