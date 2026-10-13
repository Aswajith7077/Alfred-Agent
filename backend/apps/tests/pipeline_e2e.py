"""Manual, rerunnable check for the 4-stage pipeline: Obsidian -> LLM -> summary -> Piper TTS.
Run from backend/apps: `python tests/pipeline_e2e.py`
"""
import sys

sys.path.insert(0, ".")

from agents.utils.create_agent import create_agent
from text_to_speech import PiperService, PiperConfig
from config import Settings

RAW_RETRIEVAL_MARKERS = ("[Document", "Source:")


def fail(stage: str, msg: str):
    print(f"✗ [{stage}] {msg}")
    sys.exit(1)


def ok(stage: str, msg: str):
    print(f"✓ [{stage}] {msg}")


# Stage 0 — speaker module wired onto the agent, pluggable (present even with no root enrolled)
agent = create_agent()
if not hasattr(agent, "speaker_module"):
    fail("speaker-module", "Agent has no speaker_module attribute — wiring broke")
ok("speaker-module", f"wired: {type(agent.speaker_module).__name__}")

# Stage 0b — diarization module defaults to disabled (flag off) and never touches sherpa_onnx
if not hasattr(agent, "diarization_module"):
    fail("diarization-module", "Agent has no diarization_module attribute — wiring broke")
if agent.diarization_module is not None:
    fail("diarization-module", f"expected None with DIARIZATION_ENABLED off, got {agent.diarization_module!r}")
if "sherpa_onnx" in sys.modules:
    fail("diarization-module", "sherpa_onnx leaked into the agent process")
ok("diarization-module", "disabled by default, sherpa_onnx not imported into the agent process")

# Stage 1 — Obsidian vault integration
obsidian = next((t for t in agent.integrations if type(t).__name__ == "Obsidian"), None)
if obsidian is None:
    fail("obsidian", "Obsidian integration not wired into agent.integrations")
results = obsidian.db_service.query("Obsidian", k=5)
if not results:
    fail("obsidian", "vault search returned 0 results — vault path/sync likely broken")
ok("obsidian", f"vault search returned {len(results)} result(s)")

# Stage 2 + 3 — LLM grounded in Obsidian, returning a clean summary (not raw tool dump)
query = "Summarize what my Obsidian notes say, in two sentences."
full_response = "".join(agent.run(query))
if not full_response.strip():
    fail("llm-summary", "agent.run() returned an empty response")
for marker in RAW_RETRIEVAL_MARKERS:
    if marker in full_response:
        fail("llm-summary", f"response leaks raw retrieved-document content (found {marker!r}) instead of a summary")
ok("llm-summary", f"got a clean {len(full_response)}-char summary")

# Stage 4 — Piper TTS
settings = Settings()
piper = PiperService(voice=settings.VOICE, config=PiperConfig())
piper.synthesize(full_response[:300])
ok("piper-tts", "synthesized without crashing")

print("\nAll 4 stages passed.")
