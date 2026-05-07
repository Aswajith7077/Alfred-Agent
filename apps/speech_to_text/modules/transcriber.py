import numpy as np
from multiprocessing import Queue as MPQueue
from faster_whisper import WhisperModel
from speech_to_text.models import WhisperModelConfig
from database import SpeakerRepository
from .verifier import Verifier


class Transcriber:
    def __init__(
        self,
        model_config: WhisperModelConfig,
        repository: SpeakerRepository,
        transcription_queue: MPQueue,
        state_queue: MPQueue,
        query_queue: MPQueue,
    ):
        self.model = WhisperModel(
            model_config.model_name,
            device=model_config.device,
            compute_type=model_config.compute_type,
        )
        print("[Transcriber] Loaded Successfully")
        self.transcription_queue = transcription_queue
        self.state_queue = state_queue
        self.query_queue = query_queue
        self.verifier = Verifier(repository)

    def handle_segment(self, audio: np.ndarray) -> None:
        """Called with a complete, silence-trimmed audio chunk."""

        try:
            root_user_hit, score = self.verifier.verify_fast(audio)

            if not root_user_hit:
                print(
                    f"Transcription skipped - root user not detected (score: {score})"
                )
                return

            segments, _ = self.model.transcribe(
                audio, language="en", beam_size=5, vad_filter=False
            )

            full_text = ""
            for segment in segments:
                print(segment.text, end=" ", flush=True)
                full_text += segment.text + " "

            full_text = full_text.strip()
            if full_text:
                self.query_queue.put_nowait(
                    {
                        "type": "transcript",
                        "text": full_text,
                    }
                )
            return full_text
        finally:
            self.state_queue.put_nowait({"type": "processing_done"})

    def start(self):
        while True:
            audio = self.transcription_queue.get()
            self.handle_segment(audio)
