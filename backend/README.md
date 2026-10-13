# backend — `alfred` agent

Python 3.14 CLI agent built with LangGraph over Ollama. Managed with `uv`.

## Installation

```bash
uv sync
```

`uv.lock` is gitignored and will be regenerated. Deps are heavy (torch, faster-whisper,
pyannote-audio, resemblyzer, speechbrain from git, langchain+, piper).

## Running

```bash
cd apps && python main.py
```

- `apps/` is the import root — code uses flat top-level imports (`from orchestrator import ...`,
  `from config import ...`), so you MUST run from inside `apps/`.
- `backend/main.py` is **broken** (imports a nonexistent `apps.bootstrap`); use `apps/main.py`.

## Prerequisites

- **Ollama daemon running** (`ollama serve`) at `http://127.0.0.1:11434`, with:
  - `nomic-embed-text` pulled (Obsidian embeddings).
  - A tool-capable chat model matching `apps/agents/models/ollama.py` (`gemma4:e2b` by default).
- **Voice enrollment** — `cd apps && python enroll_speaker.py` once, before first run. It records
  6s from the mic and stores a root voiceprint. Without it, `Verifier.get_root_embedding()` stays
  `None` and every transcription is **silently dropped** (no error, no response, no TTS).
- An Obsidian vault — path defaults to a hardcoded Windows path in `apps/config/settings.py`, but
  is overridden by `VAULT_PATH` in `.env` (set this on Linux/macOS).
- Gmail OAuth files in `secrets/gmail/` (`credentials.json` + `token.json`) — optional, email tools
  are skipped if `EMAIL_ADDRESS_I`/`EMAIL_APP_PASSWORD_I` aren't set.
- `.env` with `VAULT_PATH`, `EMAIL_ADDRESS_I/II`, `EMAIL_APP_PASSWORD_I/II`, `HUGGING_FACE_TOKEN`,
  and optionally `OLLAMA_URL` / `DIARIZATION_ENABLED`.
- First run only: the VAD process downloads `silero-vad` via `torch.hub` (needs internet access
  once; cached after in `~/.cache/torch/hub`).

## Layout (`apps/`)

- `agents/` — LangGraph agent build, prompt manager, pipeline, memory, tool tracking.
- `config/` — `Settings` (paths, secrets, model config).
- `container.py` — `ServiceContainer` wiring settings, vector DB, Obsidian, and emails.
- `orchestrator.py` — spawns `multiprocessing.Process` agent/STT tasks with a watchdog.
- `vector_db/` — Chroma + BM25 retrieval.
- `obsidian/` — vault loader + incremental indexing + `search`/`sync` tools.
- `emails/` — Gmail/IMAP+SMTP integration and encrypted account registry.
- `speech_to_text/` — recorder → VAD (silero) → segmenter → speaker verify (resemblyzer) →
  Whisper transcription → query aggregation. Optional sherpa-onnx diarization is separate, gated
  by `DIARIZATION_ENABLED`, and lazy-loaded only in its own worker process.
- `text_to_speech/` — Piper TTS.

System prompts are Jinja2 templates in `templates/system_prompts/`. Persistence lives in
`db/` (gitignored).

## Testing

No test runner is configured. `apps/tests/` has manual, rerunnable scripts (run with
`python tests/<name>.py` from `apps/`):
- `pipeline_e2e.py` — the 4-stage check: Obsidian search → LLM summary → Piper TTS.
- `obsidian_chroma.py` — vault sync / vector search only.
- `diarization_test.py` — sherpa-onnx diarization against `tests/fixtures/two-speakers.wav`.

Lint tool is `ruff` (`dev` dependency group, not installed by a plain `uv sync` — use
`uv sync --group dev`).