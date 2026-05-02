from abc import ABC, abstractmethod
from typing import Callable
from typing import List
from uuid import uuid4
from uuid import UUID


class BaseTool(ABC):
    def __init__(self, name: str):
        self.service_id: UUID = uuid4()
        self.service_name: str = name

    @abstractmethod
    def get_agent_tools(self) -> List[Callable]:
        pass
