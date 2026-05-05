import sounddevice as sd

from queue import Queue
from queue import Empty
from multiprocessing import Queue as MPQueue
from multiprocessing import Process
from .models import ConvertionConfig, SpeakerConfig, WhisperModelConfig
from threading import Thread
from threading import Event

from .utils import _pipeline_worker


class Recorder:
    def __init__(
        self,
        convertion_config: ConvertionConfig,
        model_config: WhisperModelConfig,
        speaker_config: SpeakerConfig,
    ):

        self.frames_per_block = int(
            convertion_config.sample_rate * convertion_config.block_duration
        )
        self.frames_per_chunk = int(
            convertion_config.sample_rate * convertion_config.chunk_duration
        )
        self.c_config = convertion_config
        self._stop_event = Event()

        self.audio_queue:Queue = Queue()
        self._mp_queue:MPQueue = MPQueue()
        self._out_queue:MPQueue = MPQueue()

        self._inference_process = Process(
            target=_pipeline_worker,
            args=(self._mp_queue, self._out_queue, convertion_config, model_config, speaker_config),
            daemon=True,
        )
        self.audio_buffer = []


    def audio_callback(self, indata, frames, time, status):
        if status:
            pass
        self.audio_queue.put(indata.copy())

    def _feeder_worker(self):
        """Bridges the thread queue → multiprocessing queue."""
        while not self._stop_event.is_set():
            try:
                block = self.audio_queue.get(timeout=1.0)
                self._mp_queue.put(block)
            except Empty:
                continue

    def record(self):
        self._inference_process.start()

        feeder = Thread(target=self._feeder_worker, daemon=True)
        feeder.start()

        # InputStream must be open BEFORE we block — use a keep-alive loop
        with sd.InputStream(
            samplerate=self.c_config.sample_rate,
            channels=self.c_config.channels,
            callback=self.audio_callback,
            blocksize=self.frames_per_block,
        ):
            print("Listening... Say 'Good bye ALFRED' to stop")
            try:
                while self._inference_process.is_alive():
                    self._inference_process.join(timeout=0.5)
            except KeyboardInterrupt:
                self._stop()

    def _transcription_worker(self):
        """Runs on its own thread — pulls from queue and processes."""
        while not self._stop_event.is_set():
            try:
                block = self.audio_queue.get(timeout=1.0)
                self.speaker.push_audio_for_transcription(block)
                self.audio_queue.task_done()
            except Exception:
                continue

    def _stop(self):
        self._stop_event.set()
        self._mp_queue.put(None)  # poison pill
        self._inference_process.join(timeout=5)
        print("\nStopped.")
