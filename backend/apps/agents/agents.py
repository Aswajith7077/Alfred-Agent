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
from uuid import uuid4
from .memory import EpisodicMemory
from .tools_tracker import ToolUsageTracker
from config import Settings

class Agent:
    def __init__(
        self,
        voice: Voice,
        prompt_manager: PromptManager,
        config: OllamaChatConfig,
        integrations: List[BaseTool],
    ):
        self.thread_id = str(uuid4())
        self.model = ChatOllama(
            model=config.model_name,
            base_url=config.base_url,
            temperature=config.temperature,
            timeout=config.timeout,
            max_tokens=config.max_tokens,
            num_ctx=8192,        # bigger context window = better tool use + memory
            repeat_penalty=1.1,  # reduces repetitive/looping responses
            top_k=40,
            top_p=0.9,
        )
        self.check_pointer = InMemorySaver()
        self.system_prompt = prompt_manager.get_system_prompt(voice)
        self.integrations = integrations
        self.__init_clients()
        self.__sync_tools()

        self.agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=self.system_prompt,
            checkpointer=self.check_pointer,
        )

        settings = Settings()
        self.memory = EpisodicMemory(str(settings.EPISODIC_MEMORY_PATH))
        self.tracker = ToolUsageTracker(str(settings.TOOL_USAGE_TRACKER_PATH))

    def __init_clients(self):
        self.clients = {}
        for integration in self.integrations:
            if hasattr(integration, 'clients'):
                self.clients.update(integration.clients)

    def __sync_tools(self) -> List[Callable]:

        self.tools = []
        for service in self.integrations:
            applicable_tools = service.get_agent_tools()
            self.tools.extend(applicable_tools)


    # def run(self, query: str) -> Generator:
    #     from datetime import datetime

    #     system = self.system_prompt
    #     system += f"\n\nToday is {datetime.now().strftime('%d-%b-%Y, %I:%M %p')}."
    #     system += f"\nAvailable accounts: {list(self.clients.keys())}"

    #     inputs = {
    #         "messages": [
    #             {"role": "system", "content": system},
    #             {"role": "user", "content": query}
    #         ]
    #     }
    #     config = {"configurable": {"thread_id": self.thread_id}}

    #     for chunk in self.agent.stream(inputs, config, stream_mode="updates"):
    #         for node, data in chunk.items():
    #             messages = data.get("messages", [])
    #             if not messages:
    #                 continue

    #             last_msg = messages[-1]
    #             content = getattr(last_msg, "content", "")

    #             if isinstance(content, str) and content:
    #                 yield content
    #             elif isinstance(content, list):
    #                 for block in content:
    #                     if isinstance(block, dict) and block.get("type") == "text":
    #                         yield block.get("text", "")


    def run(self, query: str) -> Generator:
        from datetime import datetime

        system = self.system_prompt
        system += f"\n\nToday is {datetime.now().strftime('%d-%b-%Y, %I:%M %p')}."
        system += f"\nAvailable accounts: {list(self.clients.keys())}"

        # Inject past experience
        recalls = self.memory.recall(query)
        if recalls:
            system += "\n\nRelevant past experiences:"
            for ep in recalls:
                status = "✓" if ep["success"] else "✗"
                system += f"\n{status} '{ep['query']}' → used {ep['tools_used']} → {ep['outcome']}"

        # Inject tool combination hints
        combos = self.tracker.top_combinations()
        if combos:
            system += f"\n\nCommonly combined tools: {', '.join(combos)}"

        inputs = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": query}
            ]
        }
        config = {"configurable": {"thread_id": self.thread_id}}

        tools_used = []
        full_response = ""

        for chunk in self.agent.stream(inputs, config, stream_mode="updates"):
            for node, data in chunk.items():
                # Track tool calls
                if node == "tools":
                    for msg in data.get("messages", []):
                        name = getattr(msg, "name", None)
                        if name:
                            tools_used.append(name)

                messages = data.get("messages", [])
                if not messages:
                    continue

                last_msg = messages[-1]
                content = getattr(last_msg, "content", "")

                if isinstance(content, str) and content:
                    full_response += content
                    yield content
                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text = block.get("text", "")
                            full_response += text
                            yield text

        # Record episode after run
        if tools_used or full_response:
            self.memory.record(
                query=query,
                tools_used=tools_used,
                outcome=full_response[:200],
                success=bool(full_response)
            )
            self.tracker.record(tools_used)