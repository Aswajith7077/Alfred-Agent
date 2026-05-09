from .vad import VAD
import numpy as np
from multiprocessing import Queue as MPQueue

sample_rate = 16000


class SilenceGatedSegmenter:
    def __init__(
        self,
        vad: VAD,
        vad_queue: MPQueue,
        state_queue: MPQueue,
        transcription_queue: MPQueue,
        flush_silence_ms: int = 700,
        min_speech_ms: int = 300,
        max_buffer_s: float = 30.0,
    ):
        self.vad = vad
        self.vad_queue = vad_queue
        self.state_queue = state_queue
        self.transcription_queue = transcription_queue
        self.sample_rate = sample_rate

        self.flush_silence_samples = int(sample_rate * flush_silence_ms / 1000)
        self.min_speech_samples = int(sample_rate * min_speech_ms / 1000)
        self.max_buffer_samples = int(sample_rate * max_buffer_s)
        self.natural_pause_samples = int(sample_rate * 0.25)
        self.pad_samples = int(sample_rate * 0.08)
        self.gap_samples = int(sample_rate * 0.15)
        self.silence_gap = np.zeros(self.gap_samples, dtype=np.float32)

        self._was_speaking = False
        self._post_flush_silence_samples = int(sample_rate * 1.5)  # 1.5s after flush
        self._post_flush_silence_counter = 0
        self._waiting_for_post_flush_silence = False

        self._reset()

    def _emit(self, message_type: str):
        try:
            self.state_queue.put_nowait({"type": message_type})
        except Exception:
            pass

    def push(
        self,
        block: np.ndarray,
    ) -> None:
        block = block.flatten().astype(np.float32)
        timestamps = self.vad.get_speech_detection(block)
        block_has_speech = len(timestamps) > 0

        self._buffer_len += len(block)
        self._block_metadata.append((block, timestamps))

        if block_has_speech:
            self._silence_samples = 0  # ← reset silence counter on speech
            self._has_speech = True
            self._speech_sample_count += sum(
                int((ts["end"] - ts["start"]) * self.sample_rate) for ts in timestamps
            )

            self._emit("vad_speech")
            self._was_speaking = True
            self._waiting_for_post_flush_silence = False
            self._post_flush_silence_counter = 0

        else:
            self._silence_samples += len(block)

            if self._waiting_for_post_flush_silence:
                self._post_flush_silence_counter += len(block)
                if self._post_flush_silence_counter >= self._post_flush_silence_samples:
                    self._emit("silence_detected")
                    print("[Segmenter] silence_detected emitted")
                    self._waiting_for_post_flush_silence = False
                    self._post_flush_silence_counter = 0

        silence_threshold_hit = (
            self._has_speech and self._silence_samples >= self.flush_silence_samples
        )
        buffer_exceed_hit = self._buffer_len >= self.max_buffer_samples

        if silence_threshold_hit or buffer_exceed_hit:
            self._flush()

    def start(self):
        while True:
            audio = self.vad_queue.get()
            self.push(audio)

    def _flush(self):
        if not self._block_metadata:
            self._reset()
            return

        block_offset = 0
        speech_regions: list[tuple[int, int]] = []
        for block, timestamps in self._block_metadata:
            for ts in timestamps:
                start = block_offset + int(ts["start"] * self.sample_rate)
                end = block_offset + int(ts["end"] * self.sample_rate)
                speech_regions.append((start, end))
            block_offset += len(block)

        if not speech_regions or self._speech_sample_count < self.min_speech_samples:
            self._reset()
            return

        audio = np.concatenate([b for b, _ in self._block_metadata])
        merged: list[tuple[int, int]] = [speech_regions[0]]
        for start, end in speech_regions[1:]:
            prev_start, prev_end = merged[-1]
            if (start - prev_end) <= self.natural_pause_samples:
                merged[-1] = (prev_start, max(prev_end, end))
            else:
                merged.append((start, end))

        chunks = []
        for i, (start, end) in enumerate(merged):
            s = max(0, start - self.pad_samples)
            e = min(len(audio), end + self.pad_samples)
            chunks.append(audio[s:e])
            if i < len(merged) - 1:
                chunks.append(self.silence_gap)

        self._emit("processing_start")
        self.transcription_queue.put_nowait(np.concatenate(chunks))

        # Start counting post-flush silence for the silence_detected signal
        self._waiting_for_post_flush_silence = True
        self._post_flush_silence_counter = 0
        self._reset()

    def _reset(self) -> None:
        self.vad.model.reset_states()
        self._block_metadata = []
        self._buffer_len = 0
        self._silence_samples = 0
        self._has_speech = False
        self._speech_sample_count = 0
