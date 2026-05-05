
from database import DatabaseEngine
from database import SpeakerRepository
from speech_to_text.pipeline import SpeakerPipeline
from crypto import FernetEncryption
from config import Settings

from multiprocessing import Queue as MPQueue
import warnings
import logging

def _suppress():
    warnings.filterwarnings("ignore")
    logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
    logging.getLogger("torch").setLevel(logging.ERROR)


def _pipeline_worker(
    mp_queue: MPQueue, out_queue: MPQueue, convertion_config, model_config, speaker_config
):
    try:
        _suppress()
        """Runs in a separate process — owns all ML inference."""
        import warnings
        import logging
        warnings.filterwarnings("ignore")
        logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)

        # Reconstruct unpicklable objects fresh inside the process
        settings = Settings()
        fernet = FernetEncryption(settings)
        db_engine = DatabaseEngine(settings)
        repository = SpeakerRepository(engine=db_engine.engine, fernet_handler=fernet)

        pipeline = SpeakerPipeline(
            speaker_config,
            sampling_rate=convertion_config.sample_rate,
            model_config=model_config,
            repository=repository,
            out_queue=out_queue,
        )

        while True:
            try:
                block = mp_queue.get(timeout=1.0)
                if block is None:  # poison pill — shut down
                    break
                pipeline.push_audio_for_transcription(block)
            except Exception:
                continue
    except Exception as e:
        import traceback
        print(f"[WORKER CRASH] {e}")
        traceback.print_exc()