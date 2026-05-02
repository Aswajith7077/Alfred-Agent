from typing import Optional
from piper import PiperVoice
from piper import SynthesisConfig

from pathlib import Path
from threading import Event
from .models import PiperConfig
from .voices import Voice

import sounddevice as sd


BASE_DIR = Path(__file__).parent


class PiperService:
    def __init__(self, voice: Voice, config: Optional[PiperConfig] = None):
        voice_path = BASE_DIR / "voices" / f"{voice.value}" / f"{voice.value}.onnx"
        self.voice = PiperVoice.load(voice_path)
        self.stop_flag = Event()
        self.config = config

    def synthesize(self, text: str):

        syn_config = SynthesisConfig(
            volume=self.config.volume,
            length_scale=self.config.length_scale,
            noise_scale=self.config.noise_scale,
            noise_w_scale=self.config.noise_w_scale,
            normalize_audio=self.config.normalize_audio,
        )

        self.stop_flag.clear()
        self.is_speaking_flag = True

        for chunk in self.voice.synthesize(text, syn_config):
            audio = chunk.audio_float_array
            sd.play(audio, samplerate=chunk.sample_rate)
            sd.wait()
