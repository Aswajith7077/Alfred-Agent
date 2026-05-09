from speech_to_text.pipeline import AudioPipelineManager
from speech_to_text.models import ProcessSpec
from .audio_tasks import run_preprocessor
from .audio_tasks import run_recorder
from .audio_tasks import run_vad
from .audio_tasks import run_transcriber
from .audio_tasks import run_query_aggregator
from speech_to_text.models import WhisperModelConfig
from typing import Optional, Callable


def register_stt_tasks(
    manager: AudioPipelineManager,
    build_prompt_callback: Optional[Callable] = None,
):

    manager.register(
        ProcessSpec(
            name="Preprocessor",
            target=run_preprocessor,
            kwargs={
                "audio_queue": manager.recorder_queue,
                "vad_queue": manager.vad_queue,
            },
            daemon=True,
        )
    )

    manager.register(
        ProcessSpec(
            name="Recorder",
            target=run_recorder,
            kwargs={
                "audio_queue": manager.recorder_queue,
                "vad_queue": manager.vad_queue,
            },
            daemon=False,
        )
    )

    manager.register(
        ProcessSpec(
            name="VAD",
            target=run_vad,
            kwargs={
                "vad_queue": manager.vad_queue,
                "state_queue": manager.state_queue,
                "transcription_queue": manager.transcription_queue,
            },
        )
    )

    manager.register(
        ProcessSpec(
            name="Transcriber",
            target=run_transcriber,
            kwargs={
                "model_config": WhisperModelConfig(),
                "transcription_queue": manager.transcription_queue,
                "state_queue": manager.state_queue,
                "query_queue": manager.query_queue,
            },
        )
    )

    manager.register(
        ProcessSpec(
            name="QueryAggregator",
            target=run_query_aggregator,
            kwargs={
                "query_queue": manager.query_queue,
                "state_queue": manager.state_queue,
                "llm_queue": manager.llm_queue,
                "build_prompt_callback": build_prompt_callback,
            },
        )
    )
