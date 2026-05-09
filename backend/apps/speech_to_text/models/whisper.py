from pydantic import BaseModel


class ConvertionConfig(BaseModel):
    sample_rate: int = 16000
    block_duration: float = 0.1
    chunk_duration: float = 5
    channels: int = 1


class WhisperModelConfig(BaseModel):
    model_name: str = "small.en"
    device: str = "cpu"
    compute_type: str = "int8"
