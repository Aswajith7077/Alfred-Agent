import torch
import torchaudio
import numpy as np

torch.set_num_threads(1)


class SpeechDetector:
    def __init__(self, input_sampling_rate: int, threshold: float = 0.5):
        self.original_sampling_rate = input_sampling_rate
        self.target_rate = 16000
        self._vad_chunk_samples = 512 if self.target_rate == 16000 else 256
        self.threshold = threshold

        self.model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad", model="silero_vad"
        )
        self.model.eval()

        # Reset stateful hidden state between utterances if needed
        self._reset_state()

    def _reset_state(self):
        """Call this between independent audio streams if you restart recording."""
        self.model.reset_states()

    def _preprocess(self, audio_data: np.ndarray) -> torch.Tensor:
        # Ensure mono float32
        wav = audio_data.flatten().astype(np.float32)
        wav = torch.from_numpy(wav)

        if self.original_sampling_rate != self.target_rate:
            wav = torchaudio.functional.resample(
                wav,
                orig_freq=self.original_sampling_rate,
                new_freq=self.target_rate,
            )

        # Silero expects shape [1, T] or [T]
        return wav

    def get_speech_probability(self, audio_data: np.ndarray) -> float:
        """
        Returns a float in [0, 1] — the model's speech probability for this block.
        Silero expects fixed-size chunks (512 samples @ 16 kHz); longer blocks are
        stepped with state carried across chunks and calls.
        """
        wav = self._preprocess(audio_data)
        n = wav.numel()
        if n == 0:
            return 0.0

        cs = self._vad_chunk_samples
        max_prob = 0.0
        with torch.no_grad():
            for start in range(0, n, cs):
                chunk = wav[start : start + cs]
                if chunk.numel() < cs:
                    chunk = torch.nn.functional.pad(chunk, (0, cs - chunk.numel()))
                if chunk.dim() == 1:
                    chunk = chunk.unsqueeze(0)
                prob = self.model(chunk, self.target_rate).item()
                max_prob = max(max_prob, prob)
        return max_prob

    def get_speech_detection(self, audio_data: np.ndarray) -> list[dict]:
        """
        Backwards-compatible wrapper used by SilenceGatedSegmenter.
        Returns a list with one entry if speech is detected, empty list otherwise.
        """
        prob = self.get_speech_probability(audio_data)
        if prob >= self.threshold:
            # Fake a single timestamp covering the whole block
            duration = len(audio_data) / self.original_sampling_rate
            return [{"start": 0.0, "end": duration, "probability": prob}]
        return []
