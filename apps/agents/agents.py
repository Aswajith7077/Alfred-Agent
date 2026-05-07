from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from text_to_speech import Voice
from .prompt_manger import PromptManager
from .models import OllamaChatConfig
from .base import BaseTool
from typing import Callable
from typing import Generator
from typing import List


class Agent:
    def __init__(
        self,
        voice: Voice,
        prompt_manager: PromptManager,
        config: OllamaChatConfig,
        integrations: List[BaseTool],
    ):
        self.model = ChatOllama(
            model=config.model_name,
            base_url=config.base_url,
            temperature=config.temperature,
            timeout=config.timeout,
            max_tokens=config.max_tokens,
        )
        self.check_pointer = InMemorySaver()
        self.system_prompt = prompt_manager.get_system_prompt(voice)
        self.integrations = integrations
        self.__sync_tools()

        self.agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=self.system_prompt,
            # checkpointer=self.check_pointer,
        )

    def __sync_tools(self) -> List[Callable]:

        self.tools = []
        for service in self.integrations:
            applicable_tools = service.get_agent_tools()
            self.tools.extend(applicable_tools)

    def run(self, query: str) -> Generator:

        stream_arguments = {
            "messages": [{"role": "user", "content": query}],
            "config": {"configurable": {"thread_id": "great-gatsby-lc"}},
            "stream_mode": "updates",
            "version": "v2",
        }

        for chunk in self.agent.stream(stream_arguments):
            # 🔹 Case 1: LangGraph "updates"
            if isinstance(chunk, dict) and chunk.get("type") == "updates":
                for _, data in chunk.get("data", {}).items():
                    messages = data.get("messages", [])
                    if not messages:
                        continue

                    last_msg = messages[-1]

                    for block in getattr(last_msg, "content_blocks", []):
                        if block.get("type") == "text":
                            yield block.get("text", "")

            # 🔹 Case 2: direct model output (YOUR CASE)
            elif isinstance(chunk, dict) and "model" in chunk:
                messages = chunk["model"].get("messages", [])
                if not messages:
                    continue

                last_msg = messages[-1]

                # AIMessage.content is usually a string
                content = getattr(last_msg, "content", "")

                if content:
                    yield content
