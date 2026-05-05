import numpy as np
from multiprocessing import Queue as MPQueue

from faster_whisper import WhisperModel
from speech_to_text.models import WhisperModelConfig


class Transcriber:
    def __init__(self, model_config: WhisperModelConfig,out_queue:MPQueue):
        self.model = WhisperModel(
            model_config.model_name,
            device=model_config.device,
            compute_type=model_config.compute_type,
        )
        self.out_queue = out_queue

    def handle_segment(self, audio: np.ndarray) -> None:
        """Called with a complete, silence-trimmed utterance."""

        segments, _ = self.model.transcribe(
            audio,
            language="en",
            beam_size=5,
            # vad_filter=True,
            # vad_parameters=dict(
            #     min_silence_duration_ms=300,
            #     speech_pad_ms=100,
            # ),
        )

        full_text = ""
        for segment in segments:
            print(segment.text, end=" ", flush=True)
            full_text += segment.text + ' '

        full_text = full_text.strip()
        if full_text:
            self.out_queue.put({
                "type": "transcript",
                "text": full_text,
            })
        return full_text
