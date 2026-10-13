"""Worker that owns the sherpa_onnx import/model in its own process."""
from multiprocessing import Queue as MPQueue

from .diarizer import Diarizer

STOP = "__stop__"


def run_diarizer(
    request_queue: MPQueue,
    response_queue: MPQueue,
    segmentation_model: str,
    embedding_model: str,
):
    diarizer = Diarizer(segmentation_model, embedding_model)

    while True:
        request = request_queue.get()
        if request == STOP:
            break

        audio, num_speakers = request
        try:
            segments = diarizer.diarize(audio, num_speakers=num_speakers)
            response_queue.put(("ok", segments))
        except Exception as e:
            response_queue.put(("error", str(e)))
