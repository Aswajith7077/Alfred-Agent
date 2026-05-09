from pydantic import BaseModel
from pydantic import ConfigDict
from multiprocessing import Process
from typing import Callable, Dict, Any


class ProcessSpec(BaseModel):
    name: str
    target: Callable
    kwargs: Dict[str, Any]
    daemon: bool = True

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def build(self):
        return Process(
            name=self.name, target=self.target, kwargs=self.kwargs, daemon=self.daemon
        )
