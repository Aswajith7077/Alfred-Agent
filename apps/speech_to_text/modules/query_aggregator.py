import time
import queue
from multiprocessing import Queue as MPQueue

SILENCE_TIMEOUT = 1.5
MIN_FLUSH_CHARS = 5


class QueryAggregator:
    def __init__(
        self,
        query_queue: MPQueue,
        state_queue: MPQueue,
        llm_queue: MPQueue,
        build_prompt_callback,
    ):
        self.query_queue = query_queue
        self.state_queue = state_queue
        self.llm_queue = llm_queue
        self._fragments: list[str] = []
        self._in_flight = 0
        self._silence_detected = False
        self.build_prompt_callback = build_prompt_callback

    def _drain_state_queue(self):
        while True:
            try:
                msg = self.state_queue.get_nowait()
                t = msg.get("type")
                if t == "processing_start":
                    self._in_flight += 1
                    self._silence_detected = False  # new chunk arrived, reset
                    print(f"[QueryAggregator] in_flight={self._in_flight}")
                elif t == "processing_done":
                    self._in_flight = max(0, self._in_flight - 1)
                    print(f"[QueryAggregator] in_flight={self._in_flight}")
                elif t == "vad_speech":
                    self._silence_detected = False  # user still speaking, reset
                elif t == "silence_detected":
                    self._silence_detected = True  # VAD confirmed 1.5s silence
                    print("[QueryAggregator] VAD silence confirmed")
            except queue.Empty:
                break

    def _flush(self):
        if not self._fragments:
            return
        combined = " ".join(self._fragments)
        if len(combined.replace(" ", "")) < MIN_FLUSH_CHARS:
            self._fragments.clear()
            self._silence_detected = False
            return
        prompt = self.build_prompt_callback(self._fragments)
        print(f"\n[QueryAggregator] Flushing → {combined!r}")
        self.llm_queue.put_nowait({"type": "prompt", "text": prompt})
        self._fragments.clear()
        self._silence_detected = False

    def _silence_expired(self) -> bool:
        """True only if nothing has happened for silence_timeout seconds."""
        if self._last_activity is None:
            return False
        return (time.monotonic() - self._last_activity) >= self.silence_timeout

    def start(self):
        print("[QueryAggregator] Running")
        while True:
            self._drain_state_queue()

            try:
                item = self.query_queue.get(timeout=0.05)
                if isinstance(item, dict) and item.get("type") == "transcript":
                    text = item.get("text", "").strip()
                    if text:
                        print(f"[QueryAggregator] +fragment: {text!r}")
                        self._fragments.append(text)
            except queue.Empty:
                pass

            # Flush when: VAD confirmed silence AND nothing still processing
            if self._fragments and self._silence_detected and self._in_flight == 0:
                self._flush()
