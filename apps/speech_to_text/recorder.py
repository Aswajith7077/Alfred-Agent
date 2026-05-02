import sounddevice as sd
import numpy as np

from queue import Queue
from faster_whisper import WhisperModel
from .models import ConvertionConfig, SpeakerConfig, WhisperModelConfig
from .pipeline import SpeakerPipeline
from .models import SpeakerResult


class Recorder:
    def __init__(
        self,
        convertion_config: ConvertionConfig,
        model_config: WhisperModelConfig,
        speaker_config: SpeakerConfig,
    ):

        self.frames_per_block = int(
            convertion_config.sample_rate * convertion_config.block_duration
        )
        self.frames_per_chunk = int(
            convertion_config.sample_rate * convertion_config.chunk_duration
        )

        self.audio_queue = Queue()
        self.audio_buffer = []
        self.c_config = convertion_config

        self.model = WhisperModel(
            model_config.model_name,
            device=model_config.device,
            compute_type=model_config.compute_type,
        )

        self.__init_speaker_pipeline(speaker_config=speaker_config,convertion_config = convertion_config)

    def __init_speaker_pipeline(
        self, speaker_config: SpeakerConfig, convertion_config: ConvertionConfig
    ):
        self.speaker = SpeakerPipeline(
            speaker_config, sample_rate=convertion_config.sample_rate
        )
        self.speaker.ask_fn = self._on_unknown_speaker  # wire up resolution callback
        self.speaker.enroll_if_needed()

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.audio_queue.put(indata.copy())

    def record(self):

        with sd.InputStream(
            samplerate=self.c_config.sample_rate,
            channels=self.c_config.channels,
            callback=self.audio_callback,
            blocksize=self.frames_per_block,
        ):
            print("Listening... Say 'Good bye ALFRED' to stop")
            while True:
                sd.sleep(100)

    def transcriber(self):

        while True:
            block = self.audio_queue.get()
            self.audio_buffer.append(block)

            total_frames = sum(len(b) for b in self.audio_buffer)
            if total_frames >= self.frames_per_chunk:
                audio_data = np.concatenate(self.audio_buffer)[: self.frames_per_chunk]
                self.audio_buffer = []

                audio_data = audio_data.flatten().astype(np.float32)
                result: SpeakerResult = self.speaker.process(audio_data)

                if not result.is_owner:
                    # Log the turn but don't transcribe — agent will ask later
                    if result.speaker_name:
                        print(
                            f"\n[Speaker] {result.speaker_name} speaking — not transcribing"
                        )
                    else:
                        print(
                            f"\n[Speaker] Unknown ({result.speaker_id}) — queued for resolution"
                        )
                    continue

                segments, _ = self.model.transcribe(
                    audio_data,
                    language="en",
                    beam_size=5,
                    vad_filter=True,  # ← VAD enabled (new)
                    vad_parameters=dict(
                        min_silence_duration_ms=300,
                        speech_pad_ms=100,
                    ),
                )

                for segment in segments:
                    print(segment.text, end=" ", flush=True)

    def _on_unknown_speaker(self, speaker_id: str, segments):
        """
        Called automatically when enough unknown speaker turns accumulate.
        Replace the input() here with your agent's question mechanism.
        """
        print(f"\n[Agent] I noticed a new voice in the conversation ({speaker_id}).")
        name = input("[Agent] Who was speaking? Enter their name: ").strip()
        if name:
            self.speaker.resolve_speaker(speaker_id, name)
            print(f"[Agent] Got it — I'll remember {name}'s voice from now on.")
