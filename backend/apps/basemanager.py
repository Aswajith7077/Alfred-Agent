from abc import ABC
from abc import abstractmethod
from schema import ProcessSpec
from typing import Dict


class BaseManager(ABC):
    def __init__(self, name: str):
        self.name = name
        self.specs: Dict[str, ProcessSpec] = {}
        self.setup()

    @abstractmethod
    def setup(self):
        pass

    def register(self, spec: ProcessSpec):
        self.specs[spec.name] = spec
