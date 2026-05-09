from multiprocessing import Queue as MPQueue

# from .models import ProcessSpec
# from typing import Optional, List
from basemanager import BaseManager


class AgentPipeline(BaseManager):
    def __init__(self):
        super().__init__(self.__class__.__name__)

    def setup(self, maxsize: int = 100):
        self.llm_queue = MPQueue(maxsize=maxsize)
