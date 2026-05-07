import time
from basemanager import BaseManager
from multiprocessing import Queue as MPQueue


class AudioPipelineManager(BaseManager):
    def __init__(self, llm_queue: MPQueue):
        super().__init__(self.__class__.__name__)
        self.llm_queue = llm_queue

    def setup(self):

        self.recorder_queue = MPQueue(maxsize=50)
        self.vad_queue = MPQueue(maxsize=50)
        self.transcription_queue = MPQueue(maxsize=50)
        self.query_queue = MPQueue(maxsize=50)

        self.state_queue = MPQueue(maxsize=50)

    def monitor(self):
        while True:
            for process in self.processes:
                if not process.is_alive():
                    print(f"[Manager] Process died: {process.name}")

            time.sleep(2)


"""

Process(target=run_preprocessor, args=[recorder_queue, vad_queue], daemon=True),
Process(target=run_recorder, args=[recorder_queue, vad_queue], daemon=False),
Process(target=run_vad, args=[vad_queue, state_queue, transcription_queue], daemon=True),
Process(
    target=run_transcriber,
    args=[transcription_queue, state_queue, query_queue],
    daemon=True,
),
Process(
    target=run_query_aggregator,
    args=[query_queue, state_queue ,llm_queue],
    daemon=True,
),
Process(
    target=consume_llm,
    args=[llm_queue],
    daemon=True,
)

"""
