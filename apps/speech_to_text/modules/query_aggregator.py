import time
import threading
from multiprocessing import Queue as MPQueue


class ParallelQueryAggregator:
    """
    Thread-based aggregator — safe to use inside a daemon process.
    Uses threading (not multiprocessing) since all work is I/O-bound:
      - _worker:  reads out_queue, appends to buffer
      - _watcher: polls for silence, drains buffer → calls on_query
    No Manager(), no child processes, no GIL issues for this workload.
    """

    def __init__(self, on_query=None, silence_timeout: float = 1.5, poll_interval: float = 0.05):
        self.on_query = on_query
        self.silence_timeout = silence_timeout
        self.poll_interval = poll_interval

        self._buffer: list[str] = []
        self._buffer_lock = threading.Lock()
        self._last_push_time: float = time.time()
        self._stop_event = threading.Event()
        self._threads: list[threading.Thread] = []

    # ── public API ────────────────────────────────────────────────────────────

    def start(self, out_queue: MPQueue):
        if self._threads:
            raise RuntimeError("Already started. Call stop() first.")

        self._threads = [
            threading.Thread(target=self._worker,  args=(out_queue,), daemon=True),
            threading.Thread(target=self._watcher, daemon=True),
        ]
        for t in self._threads:
            t.start()

    def stop(self, timeout: float = 2.0):
        self._stop_event.set()
        for t in self._threads:
            t.join(timeout=timeout)
        self._threads.clear()

    # ── thread targets ────────────────────────────────────────────────────────

    def _worker(self, out_queue: MPQueue):
        """Reads transcript chunks from out_queue, updates buffer + timestamp."""
        while not self._stop_event.is_set():
            try:
                item = out_queue.get(timeout=0.1)
            except Exception:
                continue

            if item is None:
                break
            if item.get("type") == "transcript":
                with self._buffer_lock:
                    self._buffer.append(item["text"].strip())
                    self._last_push_time = time.time()

    def _watcher(self):
        """Polls for silence; drains buffer and fires on_query when gap detected."""
        fired_at = self._last_push_time

        while not self._stop_event.is_set():
            time.sleep(self.poll_interval)
            now = time.time()

            with self._buffer_lock:
                last = self._last_push_time
                has_data = bool(self._buffer)
                silence_elapsed = (now - last) >= self.silence_timeout
                not_fired = last != fired_at

                if has_data and silence_elapsed and not_fired:
                    query = " ".join(self._buffer)
                    self._buffer.clear()
                    fired_at = last

            # Call on_query outside the lock so it can't block the watcher
            if has_data and silence_elapsed and not_fired and self.on_query:
                self.on_query(query)