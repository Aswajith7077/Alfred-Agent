from speech_to_text import ConvertionConfig
from speech_to_text import WhisperModelConfig
from speech_to_text import Recorder
from speech_to_text.models import SpeakerConfig
from database import DatabaseEngine
from database import SpeakerRepository
from crypto import FernetEncryption
from config import Settings


if __name__ == "__main__":
    settings = Settings()
    convertion_config = ConvertionConfig()
    model_config = WhisperModelConfig()
    speaker_config = SpeakerConfig()

    database_engine = DatabaseEngine(settings=settings)
    fernet_handler = FernetEncryption(settings=settings)
    speaker_repository = SpeakerRepository(
        engine=database_engine.engine, fernet_handler=fernet_handler
    )

    recorder = Recorder(
        convertion_config=convertion_config,
        model_config=model_config,
        speaker_config=speaker_config,
    )

    try:
        recorder.record()
    except KeyboardInterrupt:
        print("\nStopping...")
