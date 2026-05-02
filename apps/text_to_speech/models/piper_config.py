from pydantic import BaseModel


class PiperConfig(BaseModel):
    sample_rate: int = 22050
    channels: int = 1
    sample_width: int = 1
    volume: int = 2
    length_scale: float = 1.2
    noise_scale: float = 1.0
    noise_w_scale: float = 1.0
    normalize_audio: bool = True
