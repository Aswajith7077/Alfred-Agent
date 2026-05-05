# import torch
# import torch.nn.functional as F
# import numpy as np
# from speechbrain.inference.speaker import SpeakerRecognition
# from typing import Optional, Tuple
# from database import SpeakerRepository

# TARGET_SR = 16000


# class SpeakerVerifier:
#     def __init__(self, repository: SpeakerRepository, threshold: float = 0.75):
#         self.threshold = threshold
#         self.repository = repository
#         self.personal_voice_embedding: Optional[torch.Tensor] = None
#         self.MIN_SAMPLES = TARGET_SR  # 1 second

#         try:
#             self.model = SpeakerRecognition.from_hparams(
#                 source="speechbrain/spkrec-ecapa-voxceleb", savedir="pretrained/ecapa"
#             )
#             print("[SpeakerVerifier] Model loaded successfully")
#         except Exception as e:
#             print(f"[SpeakerVerifier] Warning: Could not load model: {e}")
#             self.model = None

#     def _load_voice_embedding(self, override: bool = False):
#         if not override and self.personal_voice_embedding is not None:
#             return

#         raw = self.repository.get_root_embedding()  # np.ndarray [192]
#         if raw is not None:
#             # Just restore the flat embedding vector — shape [1, 192]
#             self.personal_voice_embedding = torch.from_numpy(raw).float().unsqueeze(0)
#         else:
#             self.personal_voice_embedding = None

#     def embed(self, audio: np.ndarray) -> torch.Tensor:
#         """Returns normalised embedding of shape [1, 192]."""
#         if len(audio) < self.MIN_SAMPLES:
#             audio = np.pad(audio, (0, self.MIN_SAMPLES - len(audio)), mode="constant")

#         waveform = torch.from_numpy(audio).unsqueeze(0).float()  # [1, T]
#         emb = self.model.encode_batch(waveform)  # [1, 1, 192]
#         emb = emb.squeeze(1)  # [1, 192]
#         return F.normalize(emb, dim=-1)

#     def is_personal_voice_match(
#         self, audio: np.ndarray, sample_rate: int
#     ) -> Tuple[bool, float]:
#         if self.model is None:
#             return False, 0.0

#         if len(audio) < int(sample_rate * 1.0):
#             return False, 0.0

#         self._load_voice_embedding()
#         if self.personal_voice_embedding is None:
#             print("[SpeakerVerifier] No voiceprint enrolled")
#             return False, 0.0

#         try:
#             live_emb = self.embed(audio)  # [1, 192]
#             stored = F.normalize(self.personal_voice_embedding, dim=-1)  # [1, 192]
#             similarity = F.cosine_similarity(stored, live_emb).item()
#             print(
#                 f"[SpeakerVerifier] similarity={similarity:.3f} threshold={self.threshold}"
#             )
#             return similarity >= self.threshold, similarity
#         except Exception as e:
#             print(f"[SpeakerVerifier] Error: {e}")
#             return False, 0.0


import torch
import torch.nn.functional as F
import numpy as np
from speechbrain.inference.speaker import SpeakerRecognition
from typing import Optional, Tuple
from database import SpeakerRepository

TARGET_SR = 16000
MIN_SAMPLES = TARGET_SR  # 1 second


class SpeakerVerifier:
    def __init__(self, repository: SpeakerRepository, threshold: float = 0.75):
        self.threshold = threshold
        self.repository = repository
        self.stored_embeddings: list[torch.Tensor] = []  # multiple reference embeddings

        try:
            self.model = SpeakerRecognition.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                savedir="pretrained/ecapa"
            )
            print("[SpeakerVerifier] Model loaded successfully")
        except Exception as e:
            print(f"[SpeakerVerifier] Warning: Could not load model: {e}")
            self.model = None

    # ── embedding loading ─────────────────────────────────────────────────────

    def _load_voice_embeddings(self, override: bool = False):
        """Load all stored embeddings, not just one root."""
        if not override and self.stored_embeddings:
            return

        raw_list = self.repository.get_all_embeddings()  # return list[np.ndarray]
        if raw_list:
            self.stored_embeddings = [
                F.normalize(torch.from_numpy(r).float().unsqueeze(0), dim=-1)
                for r in raw_list
            ]
        else:
            self.stored_embeddings = []

    # ── core embedding ────────────────────────────────────────────────────────

    def embed(self, audio: np.ndarray) -> torch.Tensor:
        """Returns normalised embedding [1, 192]."""
        if len(audio) < MIN_SAMPLES:
            audio = np.pad(audio, (0, MIN_SAMPLES - len(audio)), mode="constant")

        waveform = torch.from_numpy(audio).unsqueeze(0).float()  # [1, T]
        emb = self.model.encode_batch(waveform).squeeze(1)       # [1, 192]
        return F.normalize(emb, dim=-1)

    def _embed_with_augmentation(self, audio: np.ndarray) -> torch.Tensor:
        """
        Embed 3 versions of the audio and average them.
        Averages out mic/noise variability without retraining.
        """
        variants = [
            audio,
            self._add_noise(audio, snr_db=25),
            self._time_shift(audio, shift_ms=80),
        ]
        embs = torch.stack([self.embed(v) for v in variants])  # [3, 1, 192]
        mean = embs.mean(dim=0)                                 # [1, 192]
        return F.normalize(mean, dim=-1)

    # ── similarity strategies ─────────────────────────────────────────────────

    def _score_against_stored(self, live_emb: torch.Tensor) -> float:
        """
        Compare live embedding against ALL stored embeddings.
        Returns the top-k average score rather than best-match,
        which is robust against outlier embeddings in the database.
        """
        if not self.stored_embeddings:
            return 0.0

        scores = [
            F.cosine_similarity(stored, live_emb).item()
            for stored in self.stored_embeddings
        ]

        # Top-k average: ignore worst matches (noise sessions),
        # don't over-rely on single best match
        k = max(1, len(scores) // 2)
        top_k = sorted(scores, reverse=True)[:k]
        return float(np.mean(top_k))

    # ── adaptive threshold ────────────────────────────────────────────────────

    def _adaptive_threshold(self, audio: np.ndarray) -> float:
        """
        Relax threshold for short clips — they're inherently noisier.
        Tighten it when we have a long, clean clip.
        """
        duration = len(audio) / TARGET_SR
        if duration < 1.5:
            return self.threshold - 0.06   # more lenient for short clips
        elif duration > 4.0:
            return self.threshold + 0.04   # tighter for long clips (less excuse)
        return self.threshold

    # ── public API ────────────────────────────────────────────────────────────

    def is_personal_voice_match(
        self, audio: np.ndarray, sample_rate: int
    ) -> Tuple[bool, float]:
        if self.model is None:
            return False, 0.0
        if len(audio) < int(sample_rate * 1.0):
            return False, 0.0

        self._load_voice_embeddings()
        if not self.stored_embeddings:
            print("[SpeakerVerifier] No voiceprints enrolled")
            return False, 0.0

        try:
            live_emb = self._embed_with_augmentation(audio)
            score = self._score_against_stored(live_emb)
            threshold = self._adaptive_threshold(audio)

            print(
                f"[SpeakerVerifier] score={score:.3f} "
                f"threshold={threshold:.3f} "
                f"refs={len(self.stored_embeddings)}"
            )
            return score >= threshold, score

        except Exception as e:
            print(f"[SpeakerVerifier] Error: {e}")
            return False, 0.0

    # ── augmentation helpers ──────────────────────────────────────────────────

    @staticmethod
    def _add_noise(audio: np.ndarray, snr_db: float = 25) -> np.ndarray:
        signal_power = np.mean(audio ** 2) + 1e-9
        noise_power = signal_power / (10 ** (snr_db / 10))
        noise = np.random.normal(0, np.sqrt(noise_power), len(audio))
        return (audio + noise).astype(np.float32)

    @staticmethod
    def _time_shift(audio: np.ndarray, shift_ms: float = 80) -> np.ndarray:
        shift = int(TARGET_SR * shift_ms / 1000)
        return np.roll(audio, shift).astype(np.float32)