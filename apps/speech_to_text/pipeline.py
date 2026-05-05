from speech_to_text import WhisperModelConfig
from .modules import SilenceGatedSegmenter
from .modules import Transcriber
from .modules import SpeechDetector
from .modules import SpeakerDiarization
from .modules import SpeakerVerifier
from .modules import ParallelQueryAggregator
from database import SpeakerRepository
from multiprocessing import Queue as MPQueue
from config import Settings
import numpy as np


class SpeakerPipeline:
    def __init__(
        self,
        speaker_config,
        sampling_rate: int,
        model_config: WhisperModelConfig,
        repository: SpeakerRepository,
        out_queue:MPQueue
    ):

        settings = Settings()
        self.repository = repository

        self.sampling_rate = sampling_rate
        self.speech_detector = SpeechDetector(sampling_rate)
        self.transcriber = Transcriber(model_config, out_queue)
        self.verifier = SpeakerVerifier(repository=repository, threshold=0.568)
        self.segmenter = SilenceGatedSegmenter(
            speech_detector=self.speech_detector,  # or however you expose it
            sample_rate=self.sampling_rate,
            on_segment=self.process,
            flush_silence_ms=700,
            min_speech_ms=600,
        )

        self.diarizer = SpeakerDiarization(
            sampling_rate=self.sampling_rate, settings=settings
        )
        self.query_aggregator = ParallelQueryAggregator(silence_timeout=1.5)
        self.query_aggregator.start(out_queue)

    def push_audio_for_transcription(self, audio_data: np.ndarray):
        self.segmenter.push(audio_data)

    def _slice_audio(self, audio: np.ndarray, start: float, end: float) -> np.ndarray:
        start_idx = int(start * self.sampling_rate)
        end_idx = int(end * self.sampling_rate)
        return audio[start_idx:end_idx]

    def process(self, audio_data: np.ndarray):
        duration = len(audio_data) / self.sampling_rate
        print(f"[Pipeline] Received segment: {duration:.2f}s")

        if self.diarizer.pipeline is None:
            # No diarization available — verify the whole chunk directly
            if duration < 0.5:
                print(f"  [SPEAKER_00] skipped — too short ({duration:.2f}s)")
                return

            verified, score = self.verifier.is_personal_voice_match(
                audio_data, self.sampling_rate
            )
            if not verified:
                print(f"  [SPEAKER_00] rejected (score={score:.2f})")
                return

            print(f"  [SPEAKER_00] verified (score={score:.2f}) → transcribing")
            self.transcriber.handle_segment(audio_data)
            return

        # Full diarization path
        diarized_results = self.diarizer.diarize(audio_data)
        for segment in diarized_results:
            chunk = self._slice_audio(audio_data, segment["start"], segment["end"])
            chunk_duration = len(chunk) / self.sampling_rate

            if chunk_duration < 1.0:
                print(
                    f"  [{segment['speaker']}] skipped — too short ({chunk_duration:.2f}s)"
                )
                continue

            verified, score = self.verifier.is_personal_voice_match(
                chunk, self.sampling_rate
            )
            if not verified:
                print(f"  [{segment['speaker']}] rejected (score={score:.2f})")
                continue

            print(
                f"  [{segment['speaker']}] verified (score={score:.2f}) → transcribing"
            )
            self.transcriber.handle_segment(chunk)
            # return self.transcriber.handle_segment(audio_data)
