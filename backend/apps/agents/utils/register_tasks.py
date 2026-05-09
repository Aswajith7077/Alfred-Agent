from agents.pipeline import AgentPipeline
from schema import ProcessSpec
from .agent_tasks import run_agent


def register_agent_tasks(manager: AgentPipeline):

    manager.register(
        ProcessSpec(
            name="Agent",
            target=run_agent,
            kwargs={
                "llm_queue": manager.llm_queue,
            },
            daemon=True,
        )
    )
