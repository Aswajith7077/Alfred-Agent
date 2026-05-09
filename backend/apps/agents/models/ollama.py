from pydantic import BaseModel


class OllamaChatConfig(BaseModel):
    model_name: str = "gemma4:e2b"
    base_url: str = "http://127.0.0.1:11434"
    temperature: float = 0.5
    timeout: int = 300
    max_tokens: int = 25000
