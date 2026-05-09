from database import SpeakerRepository
from resemblyzer import VoiceEncoder, preprocess_wav
import numpy as np

TARGET_SR = 16000
MIN_SAMPLES = TARGET_SR


class Verifier:
    def __init__(self, repository: SpeakerRepository, threshold: float = 0.75):
        # resemblyzer uses cosine similarity natively — scores are higher (0-1)
        # so threshold moves from ~0.25 to ~0.75
        self.threshold = threshold
        self.repository = repository
        self.stored_embeddings = []
        self.personal_embedding = None
        self.__load_embedding_model()

    def __load_embedding_model(self):
        try:
            self.model = VoiceEncoder(device="cpu")
            print("[SpeakerVerifier] resemblyzer loaded successfully")
        except Exception as e:
            print(f"[SpeakerVerifier] Warning: Could not load model: {e}")
            self.model = None

    def _adaptive_threshold(self, audio: np.ndarray) -> float:
        duration = len(audio) / TARGET_SR
        if duration < 1.5:
            return self.threshold - 0.06
        elif duration > 4.0:
            return self.threshold + 0.04
        return self.threshold

    def _score_against_stored(self, live_emb: np.ndarray) -> float:
        if self.personal_embedding is None:
            return 0.0
        # Both are already L2-normalised by resemblyzer → dot = cosine sim
        return float(np.dot(self.personal_embedding, live_emb))

    def verify(self, audio: np.ndarray):
        self._load_personal_embedding()

        if self.personal_embedding is None:
            print("[Diarizer] Personal embedding not found")
            return False, 0.0

        try:
            live_emb = self._embed_with_augmentation(audio)
            score = self._score_against_stored(live_emb)
            threshold = self._adaptive_threshold(audio)

            print(f"[SpeakerVerifier] score={score:.3f} threshold={threshold:.3f}")
            return score >= threshold, score

        except Exception as e:
            print(f"[SpeakerVerifier] Error: {e}")
            return False, 0.0

    def verify_fast(self, audio: np.ndarray):
        """Single embed — no augmentation. Use at inference time."""
        self._load_personal_embedding()
        if self.personal_embedding is None:
            return False, 0.0
        try:
            live_emb = self.embed(audio)  # single pass, no augmentation
            score = float(np.dot(self.personal_embedding, live_emb))
            threshold = self._adaptive_threshold(audio)
            print(f"[SpeakerVerifier] score={score:.3f} threshold={threshold:.3f}")
            return score >= threshold, score
        except Exception as e:
            print(f"[SpeakerVerifier] Error: {e}")
            return False, 0.0

    def embed(self, audio: np.ndarray) -> np.ndarray:
        """Returns normalised 256-dim embedding."""
        if self.model is None:
            return np.random.randn(256)

        if len(audio) < MIN_SAMPLES:
            audio = np.pad(audio, (0, MIN_SAMPLES - len(audio)), mode="constant")

        # preprocess_wav handles resampling + normalisation
        wav = preprocess_wav(audio, source_sr=TARGET_SR)
        emb = self.model.embed_utterance(wav)  # already L2-normalised
        return emb

    def _load_personal_embedding(self, override: bool = False):
        if not override and self.personal_embedding is not None:
            return

        embedding = self.repository.get_root_embedding()
        if embedding is not None:
            self.personal_embedding = (
                embedding if isinstance(embedding, np.ndarray) else np.array(embedding)
            )
            self.stored_embeddings = [self.personal_embedding]
        else:
            self.personal_embedding = None
            self.stored_embeddings = []

    def _add_noise(self, audio: np.ndarray, snr_db: float = 25) -> np.ndarray:
        signal_power = np.mean(audio**2)
        noise_power = signal_power / (10 ** (snr_db / 10))
        noise = np.random.normal(0, np.sqrt(noise_power), audio.shape)
        return audio + noise

    def _time_shift(self, audio: np.ndarray, shift_ms: float = 80) -> np.ndarray:
        shift_samples = int((shift_ms / 1000) * TARGET_SR)
        if shift_samples == 0:
            return audio
        shifted = np.pad(audio, (shift_samples, 0), mode="constant")[:-shift_samples]
        return shifted

    def _embed_with_augmentation(self, audio: np.ndarray) -> np.ndarray:
        variants = [
            audio,
            self._add_noise(audio, snr_db=25),
            self._time_shift(audio, shift_ms=80),
        ]
        embs = np.stack([self.embed(v) for v in variants])  # [3, 256]
        mean = embs.mean(axis=0)
        return mean / np.linalg.norm(mean)  # re-normalise after averaging
