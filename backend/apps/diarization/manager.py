"""Lazily-started diarization process: spawned on first diarize() call,
torn down after idle_timeout of no use or at process exit. The caller's
process never imports sherpa_onnx - only the spawned child does."""
import atexit
import threading
from multiprocessing import Process
from multiprocessing import Queue as MPQueue
from pathlib import Path
from typing import List, Optional, Union

import numpy as np

from .models import Segment
from .process import STOP, run_diarizer


class DiarizationManager:
    def __init__(
        self,
        segmentation_model: Union[str, Path],
        embedding_model: Union[str, Path],
        idle_timeout: float = 60.0,
    ):
        self._segmentation_model = str(segmentation_model)
        self._embedding_model = str(embedding_model)
        self._idle_timeout = idle_timeout
        self._process: Optional[Process] = None
        self._request_queue: Optional[MPQueue] = None
        self._response_queue: Optional[MPQueue] = None
        self._idle_timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()
        atexit.register(self.stop)

    def _ensure_started(self):
        if self._process is not None and self._process.is_alive():
            return
        self._request_queue = MPQueue()
        self._response_queue = MPQueue()
        self._process = Process(
            target=run_diarizer,
            args=(
                self._request_queue,
                self._response_queue,
                self._segmentation_model,
                self._embedding_model,
            ),
            daemon=True,
        )
        self._process.start()

    def _reset_idle_timer(self):
        if self._idle_timer is not None:
            self._idle_timer.cancel()
        self._idle_timer = threading.Timer(self._idle_timeout, self.stop)
        self._idle_timer.daemon = True
        self._idle_timer.start()

    def diarize(
        self,
        audio: Union[str, Path, np.ndarray],
        num_speakers: Optional[int] = None,
        timeout: float = 300.0,
    ) -> List[Segment]:
        # shortcut: one in-flight request at a time, enforced by _lock
        with self._lock:
            self._ensure_started()
            self._request_queue.put((audio, num_speakers))
            status, payload = self._response_queue.get(timeout=timeout)
            self._reset_idle_timer()
            if status == "error":
                raise RuntimeError(f"Diarization failed: {payload}")
            return payload

    def stop(self):
        with self._lock:
            if self._idle_timer is not None:
                self._idle_timer.cancel()
                self._idle_timer = None
            if self._process is not None and self._process.is_alive():
                self._request_queue.put(STOP)
                self._process.join(timeout=5)
                if self._process.is_alive():
                    self._process.terminate()
            self._process = None
