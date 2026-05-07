"""Listens Indefinitely to the Microphone and saves the audio to a file when the user stops talking."""

from multiprocessing import Queue as MPQueue
import sounddevice as sd
import numpy as np

sample_rate: int = 16000
block_duration: float = 0.1
chunk_duration: float = 5
channels: int = 1

model_name: str = "small.en"
device: str = "cpu"
compute_type: str = "int8"


class Recorder:
    def __init__(self, audio_queue: MPQueue, vad_queue: MPQueue):
        self.frames_per_block: int = int(sample_rate * block_duration)
        self.audio_queue: MPQueue = audio_queue
        self.vad_queue: MPQueue = vad_queue

    def audio_callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status)
        try:
            self.audio_queue.put_nowait(indata.copy())
        except Exception:
            # Queue is full, skip this audio block
            pass

    def record(self):
        with sd.InputStream(
            samplerate=sample_rate,
            channels=channels,
            callback=self.audio_callback,
            blocksize=self.frames_per_block,
        ):
            print("Listening... Say 'Good bye ALFRED' to stop")
            while True:
                sd.sleep(10)

    def preprocess(self):
        buffer = []
        while True:
            audio_data = self.audio_queue.get()

            buffer.append(audio_data)
            total_frames = sum(len(chunk) for chunk in buffer)

            if total_frames >= sample_rate * chunk_duration:
                data = np.concatenate(buffer)
                buffer = []

                audio = data.flatten().astype(np.float32)
                self.vad_queue.put_nowait(audio)
