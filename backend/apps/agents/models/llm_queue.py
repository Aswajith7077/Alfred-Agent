from pydantic import BaseModel


class LLMQueueItem(BaseModel):
    type: str
    text: str
    