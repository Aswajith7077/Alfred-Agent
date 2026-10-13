"""
One-time voice enrollment for the root user.

Records a short sample from the microphone, embeds it with the same
resemblyzer model the Verifier uses at inference time, and stores it as the
ROOT speaker. Without this, Verifier.get_root_embedding() always returns
None and every transcription is silently dropped.

Run with: cd backend/apps && python enroll_speaker.py
"""

import sounddevice as sd
import numpy as np

from database import SpeakerRepository, DatabaseEngine, Role
from crypto import FernetEncryption
from config import Settings
from speech_to_text.modules import Verifier

ENROLL_SECONDS = 6
SAMPLE_RATE = 16000


def record_sample() -> np.ndarray:
    print(f"Recording {ENROLL_SECONDS}s - speak naturally after the beep...")
    audio = sd.rec(int(ENROLL_SECONDS * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1)
    sd.wait()
    return audio.flatten().astype(np.float32)


def main():
    settings = Settings()
    db_engine = DatabaseEngine(settings)
    fernet = FernetEncryption(settings.ENROLLMENT_KEY_PATH)
    repository = SpeakerRepository(db_engine.engine, fernet)

    if repository.get_root_embedding() is not None:
        print("A root speaker is already enrolled. Re-enrolling will overwrite it.")

    verifier = Verifier(repository)
    audio = record_sample()
    embedding = verifier.embed(audio)

    repository.insert_speaker(name="Owner", embedding=embedding, role=Role.ROOT)
    print("Enrollment complete - root voiceprint stored.")


if __name__ == "__main__":
    main()
