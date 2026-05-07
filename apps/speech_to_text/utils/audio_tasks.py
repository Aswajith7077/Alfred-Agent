from speech_to_text.recorder import Recorder
from speech_to_text.modules import VAD
from speech_to_text.modules import SilenceGatedSegmenter
from speech_to_text.modules import Transcriber
from speech_to_text.modules import QueryAggregator
from speech_to_text.models import WhisperModelConfig

from database import SpeakerRepository
from database import DatabaseEngine
from crypto import FernetEncryption
from config import Settings

from multiprocessing import Queue as MPQueue
from typing import Optional, Callable


def run_recorder(audio_queue: MPQueue, vad_queue: MPQueue):
    recorder = Recorder(audio_queue, vad_queue)
    recorder.record()


def run_preprocessor(audio_queue: MPQueue, vad_queue: MPQueue):
    recorder = Recorder(audio_queue, vad_queue)
    recorder.preprocess()


def run_vad(vad_queue: MPQueue, state_queue: MPQueue, transcription_queue: MPQueue):
    vad = VAD(input_sampling_rate=16000)
    segmenter = SilenceGatedSegmenter(
        vad=vad,
        vad_queue=vad_queue,
        state_queue=state_queue,
        transcription_queue=transcription_queue,
    )
    segmenter.start()


def run_transcriber(
    model_config: WhisperModelConfig,
    transcription_queue: MPQueue,
    state_queue: MPQueue,
    query_queue: MPQueue,
):
    settings = Settings()
    db_engine = DatabaseEngine(settings)
    fernet = FernetEncryption(settings.ENROLLMENT_KEY_PATH)
    repository = SpeakerRepository(db_engine.engine, fernet)

    transcriber = Transcriber(
        model_config=model_config,
        repository=repository,
        transcription_queue=transcription_queue,
        state_queue=state_queue,
        query_queue=query_queue,
    )
    transcriber.start()


def run_query_aggregator(
    query_queue: MPQueue,
    state_queue: MPQueue,
    llm_queue: MPQueue,
    build_prompt_callback: Optional[Callable] = None,
):

    query_aggregator = QueryAggregator(
        query_queue=query_queue,
        state_queue=state_queue,
        llm_queue=llm_queue,
        build_prompt_callback=build_prompt_callback,
    )
    query_aggregator.start()
