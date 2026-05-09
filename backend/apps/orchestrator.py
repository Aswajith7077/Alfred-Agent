from agents import register_agent_tasks
from agents import PromptManager
from agents import AgentPipeline

from speech_to_text import register_stt_tasks
from speech_to_text import AudioPipelineManager

from schema import ProcessSpec
from typing import Dict
from multiprocessing import Process
import time
import signal
import sys


class Orchestrator:
    def __init__(self, template_dir: str):
        self.templates_dir = template_dir
        self._running = False
        self.specs: Dict[str, ProcessSpec] = {}  # all specs flat
        self.processes: Dict[str, Process] = {}  # all processes flat
        self.__init_pipeline()

    def __init_pipeline(self):
        self.agent_manager = AgentPipeline()
        self.stt_manager = AudioPipelineManager(self.agent_manager.llm_queue)
        self.prompt_manager = PromptManager(str(self.templates_dir))

    def register(self):
        # just registration, nothing starts yet
        register_agent_tasks(self.agent_manager)
        # register_stt_tasks(self.stt_manager, self.prompt_manager.build_prompt)

    def _collect_specs(self):
        """Pull all specs from all managers into one flat dict."""
        for name, spec in self.agent_manager.specs.items():
            self.specs[name] = spec
        for name, spec in self.stt_manager.specs.items():
            self.specs[name] = spec

    def _spawn(self, name: str):
        process = self.specs[name].build()
        process.start()
        self.processes[name] = process
        print(f"[ORCHESTRATOR] Started: {name} (pid={process.pid})")

    def _start_all(self):
        for name in self.specs:
            self._spawn(name)

    def _monitor(self):
        """Single watchdog loop for ALL processes."""
        while self._running:
            for name, process in list(self.processes.items()):
                if not process.is_alive():
                    print(
                        f"[ORCHESTRATOR] Dead: {name} (exit={process.exitcode}), respawning..."
                    )
                    process.close()
                    self._spawn(name)
            time.sleep(2)

    def _handle_exit(self, sig, frame):
        print("[ORCHESTRATOR] Shutting down...")
        self._running = False
        for name, process in self.processes.items():
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
        sys.exit(0)

    def run(self):
        self.register()
        self._collect_specs()

        signal.signal(signal.SIGINT, self._handle_exit)
        signal.signal(signal.SIGTERM, self._handle_exit)

        self._running = True
        self._start_all()
        self._monitor()  # blocks here, watching everything
