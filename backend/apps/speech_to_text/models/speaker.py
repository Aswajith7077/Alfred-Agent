from pydantic import BaseModel, ConfigDict
from typing import Optional
import numpy as np


class SpeakerResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    is_owner: bool  # True → send to STT + agent
    speaker_id: str  # "OWNER" | "SPEAKER_00" | "UNKNOWN"
    speaker_name: Optional[str]  # resolved name from DB, or None
    verification_score: float  # cosine similarity vs your voiceprint
    audio: np.ndarray


class SpeakerConfig(BaseModel):
    # Voiceprint enrollment
    voiceprint_path: str = "voiceprint.wav"  # saved after first enrollment
    enrollment_duration: int = 8  # seconds to record for enrollment
    verification_threshold: float = 0.75  # cosine similarity cutoff (tune up/down)

    # Unknown speaker resolution
    segments_before_asking: int = 3  # how many turns before agent asks "who is this?"
    db_path: str = "speakers.db"  # SQLite file

    # Model paths (downloaded automatically by SpeechBrain)
    ecapa_model_dir: str = "models/ecapa"
    pyannote_model: str = "pyannote/speaker-diarization-3.1"
