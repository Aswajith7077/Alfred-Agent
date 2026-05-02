from agents import Orchestrator
from config import Settings
from container import ServiceContainer


def create_orchestrator() -> Orchestrator:
    container: ServiceContainer = ServiceContainer()
    settings: Settings = container.settings

    orchestrator: Orchestrator = Orchestrator(
        voice=settings.VOICE,
        prompt_manager=container.prompt_manager,
        config=container.ollama_config,
        integrations=container.get_tools(),
    )

    return orchestrator
