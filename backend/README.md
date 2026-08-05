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

- Ollama running at `http://127.0.0.1:11434` with the `nomic-embed-text` embedding model.
- An Obsidian vault at the hardcoded Windows path in `apps/config/settings.py` (change it for
  Linux).
- Gmail OAuth files in `secrets/gmail/` (`credentials.json` + `token.json`).
- `.env` with `EMAIL_ADDRESS_I/II`, `EMAIL_APP_PASSWORD_I/II`, `HUGGING_FACE_TOKEN`.

## Layout (`apps/`)

- `agents/` — LangGraph agent build, prompt manager, pipeline, memory, tool tracking.
- `config/` — `Settings` (paths, secrets, model config).
- `container.py` — `ServiceContainer` wiring settings, vector DB, Obsidian, and emails.
- `orchestrator.py` — spawns `multiprocessing.Process` agent/STT tasks with a watchdog.
- `vector_db/` — Chroma + BM25 retrieval.
- `obsidian/` — vault loader + incremental indexing + `search`/`sync` tools.
- `emails/` — Gmail/IMAP+SMTP integration and encrypted account registry.
- `speech_to_text/`, `text_to_speech/` — Whisper + pyannote + piper voice pipelines.

System prompts are Jinja2 templates in `templates/system_prompts/`. Persistence lives in
`db/` (gitignored).

## Testing

No test runner is configured. `apps/tests/obsidian_chroma.py` is a manual script; lint tool is
`ruff` (listed as a project dependency).