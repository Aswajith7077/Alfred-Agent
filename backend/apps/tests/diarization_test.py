"""Manual check for the optional sherpa-onnx diarization module (no agent/LLM involved).
Run from backend/apps: `python tests/diarization_test.py`
"""
import sys
from pathlib import Path

sys.path.insert(0, ".")

from config import Settings
from diarization import Diarizer

FIXTURE = Path(__file__).parent / "fixtures" / "two-speakers.wav"


def fail(stage: str, msg: str):
    print(f"✗ [{stage}] {msg}")
    sys.exit(1)


def ok(stage: str, msg: str):
    print(f"✓ [{stage}] {msg}")


settings = Settings()
diarizer = Diarizer(
    segmentation_model=settings.DIARIZATION_SEGMENTATION_MODEL,
    embedding_model=settings.DIARIZATION_EMBEDDING_MODEL,
)

if "sherpa_onnx" in sys.modules:
    fail("lazy-import", "sherpa_onnx got imported before diarize() was ever called")
ok("lazy-import", "sherpa_onnx not imported until first diarize() call")

segments = diarizer.diarize(FIXTURE)

if not segments:
    fail("diarize", "no segments returned for the two-speaker fixture")

for s in segments:
    if not (s.start >= 0 and s.end > s.start):
        fail("diarize", f"malformed segment: {s}")

speakers = {s.speaker for s in segments}
if len(speakers) < 2:
    fail("diarize", f"expected >= 2 distinct speakers on a two-speaker fixture, got {speakers}")

ok("diarize", f"{len(segments)} well-formed segments, {len(speakers)} speakers detected")
print("\nDiarizer checks passed.")
