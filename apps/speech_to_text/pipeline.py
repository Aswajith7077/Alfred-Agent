from .models import SpeakerResult
from .models import SpeakerConfig
from database import SpeakerRepository

from typing import Callable
from typing import Optional
import sounddevice as sd
import soundfile as sf
import numpy as np
import threading
import torch
import os


class SpeakerPipeline:
    """
    Plugs between your audio buffer and STT.

    Usage:
        pipeline = SpeakerPipeline(config, sample_rate=16000)
        pipeline.enroll_if_needed()          # once on startup

        # Inside your transcriber loop:
        result = pipeline.process(audio_chunk_float32)
        if result.is_owner:
            # send to STT
        else:
            # log unknown turn, agent will ask later
    """

    def __init__(self, config: SpeakerConfig, sample_rate: int = 16000):
        self.config = config
        self.sample_rate = sample_rate
        self.db = SpeakerRepository(config.db_path)

        # Unknown speaker accumulator: speaker_id → list of audio segments
        self._unknown_queue: dict[str, list[np.ndarray]] = {}
        self._lock = threading.Lock()

        # Lazy-loaded models (heavy — only load once)
        self._verifier = None
        self._diarizer = None
        self._owner_embedding: Optional[torch.Tensor] = None

        # Callback: when agent should ask "who is this?" — set from outside
        # Signature: ask_fn(speaker_id: str, segments: list[np.ndarray])
        self.ask_fn: Optional[Callable] = None

    # ── Model loading ─────────────────────────────────────────────────────────

    def _load_verifier(self):
        if self._verifier is None:
            from speechbrain.inference.speaker import SpeakerRecognition

            self._verifier = SpeakerRecognition.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                savedir=self.config.ecapa_model_dir,
            )
            print("[SpeakerPipeline] ECAPA-TDNN loaded")

    def _load_diarizer(self):
        if self._diarizer is None:
            from pyannote.audio import Pipeline

            hf_token = os.environ.get("HF_TOKEN")
            self._diarizer = Pipeline.from_pretrained(
                self.config.pyannote_model,
                use_auth_token=hf_token,
            )
            print("[SpeakerPipeline] Pyannote diarizer loaded")

    # ── Enrollment ────────────────────────────────────────────────────────────

    def enroll_if_needed(self):
        """
        If voiceprint.wav exists → load embedding.
        If not → record enrollment audio now, save, load.
        Call once on startup before any processing.
        """
        self._load_verifier()

        if os.path.exists(self.config.voiceprint_path):
            print(
                f"[SpeakerPipeline] Loading voiceprint from {self.config.voiceprint_path}"
            )
            self._owner_embedding = self._embed_file(self.config.voiceprint_path)
            print("[SpeakerPipeline] Voiceprint ready")
            return

        # Record enrollment
        dur = self.config.enrollment_duration
        print(f"\n[Enrollment] Speak clearly for {dur} seconds after the prompt...")
        input("  Press ENTER when ready, then speak: ")

        audio = sd.rec(
            int(dur * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
        )
        sd.wait()
        print("[Enrollment] Done. Saving voiceprint...")

        sf.write(self.config.voiceprint_path, audio, self.sample_rate)
        self._owner_embedding = self._embed_file(self.config.voiceprint_path)
        print(f"[Enrollment] Voiceprint saved to {self.config.voiceprint_path}")

    def _embed_file(self, wav_path: str) -> torch.Tensor:
        """Get ECAPA embedding from a wav file."""
        embedding = self._verifier.encode_batch(
            self._verifier.load_audio(wav_path).unsqueeze(0)
        )
        return embedding.squeeze(0)

    def _embed_array(self, audio: np.ndarray) -> torch.Tensor:
        """Get ECAPA embedding from a float32 numpy array."""
        tensor = torch.tensor(audio, dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            embedding = self._verifier.encode_batch(tensor)
        return embedding.squeeze(0)

    # ── Verification ─────────────────────────────────────────────────────────

    def _cosine_similarity(self, a: torch.Tensor, b: torch.Tensor) -> float:
        return torch.nn.functional.cosine_similarity(
            a.unsqueeze(0), b.unsqueeze(0)
        ).item()

    def verify(self, audio: np.ndarray) -> tuple[bool, float]:
        """
        Returns (is_owner, similarity_score).
        True if this audio matches your enrolled voiceprint.
        """
        if self._owner_embedding is None:
            raise RuntimeError("Call enroll_if_needed() before verify()")
        embedding = self._embed_array(audio)
        score = self._cosine_similarity(embedding, self._owner_embedding)
        return score >= self.config.verification_threshold, score

    # ── Diarization ───────────────────────────────────────────────────────────

    def diarize(self, audio: np.ndarray) -> list[dict]:
        """
        Returns list of speaker turns:
        [{"speaker": "SPEAKER_00", "start": 0.0, "end": 2.3}, ...]
        """
        self._load_diarizer()

        # pyannote needs a dict with waveform tensor + sample rate
        waveform = torch.tensor(audio).unsqueeze(0)  # (1, samples)
        audio_dict = {"waveform": waveform, "sample_rate": self.sample_rate}

        diarization = self._diarizer(audio_dict)
        turns = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            turns.append(
                {
                    "speaker": speaker,
                    "start": turn.start,
                    "end": turn.end,
                }
            )
        return turns

    # ── Unknown speaker resolution ────────────────────────────────────────────

    def _handle_unknown(self, speaker_id: str, segment: np.ndarray):
        """
        Accumulate unknown speaker segments.
        After N segments, trigger ask_fn so agent can query the user.
        """
        with self._lock:
            self._unknown_queue.setdefault(speaker_id, []).append(segment)
            count = len(self._unknown_queue[speaker_id])

        if count >= self.config.segments_before_asking and self.ask_fn:
            segments = self._unknown_queue.get(speaker_id, [])
            threading.Thread(
                target=self.ask_fn, args=(speaker_id, segments), daemon=True
            ).start()

    def resolve_speaker(self, speaker_id: str, name: str):
        """
        Call this after the user tells the agent who the unknown speaker is.
        Saves name + embedding to DB for future auto-recognition.
        """
        segments = self._unknown_queue.get(speaker_id, [])
        if not segments:
            return
        combined = np.concatenate(segments)
        embedding = self._embed_array(combined).detach().numpy()
        self.db.save(speaker_id, name, embedding)
        print(f"[SpeakerPipeline] Resolved {speaker_id} → '{name}' and saved to DB")

        with self._lock:
            self._unknown_queue.pop(speaker_id, None)

    def _match_known_db(self, audio: np.ndarray) -> Optional[str]:
        """
        Check if audio matches any previously resolved speaker in the DB.
        Returns their name if matched, else None.
        """
        embedding = self._embed_array(audio)
        for known in self.db.all_known():
            known_emb = torch.tensor(known["embedding"])
            score = self._cosine_similarity(embedding, known_emb)
            if score >= self.config.verification_threshold:
                return known["name"]
        return None

    # ── Main entry point ──────────────────────────────────────────────────────

    def process(self, audio: np.ndarray) -> "SpeakerResult":
        """
        Run full pipeline on one audio chunk.
        Returns SpeakerResult with is_owner flag and speaker info.

        Call this inside your transcriber() loop before sending to STT.
        """
        self._load_verifier()

        # 1. Quick owner verification on the whole chunk
        is_owner, score = self.verify(audio)

        if is_owner:
            return SpeakerResult(
                is_owner=True,
                speaker_id="OWNER",
                speaker_name="You",
                verification_score=score,
                audio=audio,
            )

        # 2. Not owner — diarize to find speaker turns
        turns = self.diarize(audio)

        # 3. Check each turn against DB + unknown queue
        for turn in turns:
            start = int(turn["start"] * self.sample_rate)
            end = int(turn["end"] * self.sample_rate)
            segment = audio[start:end]

            if len(segment) < 1600:  # skip very short segments (<0.1s)
                continue

            known_name = self._match_known_db(segment)
            if known_name:
                return SpeakerResult(
                    is_owner=False,
                    speaker_id=turn["speaker"],
                    speaker_name=known_name,
                    verification_score=score,
                    audio=segment,
                )

            # Unknown — accumulate and maybe trigger ask
            self._handle_unknown(turn["speaker"], segment)

        return SpeakerResult(
            is_owner=False,
            speaker_id="UNKNOWN",
            speaker_name=None,
            verification_score=score,
            audio=audio,
        )
