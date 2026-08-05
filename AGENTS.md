# AGENTS.md

Personal AI assistant ("Alfred"). Two independent packages, no wiring between them yet. No CI, no root workspace tooling.

## Repo layout

- `backend/` — Python 3.14 CLI agent (`alfred`), managed by `uv`. All source lives under `apps/`.
- `dynamic-island/` — Tauri 2 + React 19 + TypeScript + Vite desktop UI (pnpm). Self-contained demo, not connected to the backend.

## Backend

### Running (gotcha: entrypoints and CWD)
- `backend/main.py` is **broken** — it imports `apps.bootstrap`, which does not exist. Don't use it.
- The real entrypoint is `backend/apps/main.py`.
- Code uses flat top-level imports (`from orchestrator import ...`, `from config import ...`, `from agents import ...`, `from vector_db import ...`), so you MUST run from inside `backend/apps/` (the `apps/` dir is the import root):
  ```
  cd backend/apps && python main.py
  ```
  And `uv` installs resolve the package from `backend/`.

### Setup & toolchain
- Python must be **3.14** (`backend/.python-version`, `requires-python = ">=3.14"`).
- Install with `uv sync` in `backend/`. `uv.lock` is gitignored, so it will be regenerated.
- Deps are heavy (torch, faster-whisper, pyannote-audio, resemblyzer, speechbrain from cross filename, langchain+, piper). `speechbrain` is pinned `==1.0.0` and sourced from a git `rev="develop"`.
- `ruff` is listed as a regular runtime dependency in `pyproject.toml` (unusual — it's the lint tool; there is no `[tool.ruff]` config and no test runner configured).

### Runtime requirements (verify before running the agent)
- **Ollama** must be running at `http://127.0.0.1:11434` (`apps/config/settings.py:29`); embeddings use the `nomic-embed-text` model.
- Obsidian vault path is **hardcoded to a Windows path** `C:\Users\Aswajith S\...` in `apps/config/settings.py:14` and will fail on Linux.
- Gmail OAuth needs `backend/secrets/gmail/credentials.json` + `token.json` (gitignored).
- `.env` is loaded via python-dotenv; email creds come from `EMAIL_ADDRESS_I/II`, `EMAIL_APP_PASSWORD_I/II`, `HUGGING_FACE_TOKEN` (gitignored).

### Architecture
- `apps/ServiceContainer` wires settings, vector DB, Obsidian, and emails; `apps/agents/utils/create_agent.py` builds the LangGraph agent (Ollama via langchain-ollama).
- `apps/orchestrator.py` spawns `multiprocessing.Process` tasks (registered via `register_agent_tasks`, `register_stt_tasks`) and a watchdog respawns dead ones. The agent task reads queries from stdin (`input(">>> ")`).
- Tools (Obsidian search/sync, email ops) come from integrations' `get_agent_tools()`; system prompts are Jinja2 templates in `backend/templates/system_prompts/*.jinja2` (`ALFRED.jinja2` governs email workflows).
- State/persistence lives under `backend/db/` (gitignored): chroma vector store, sqlite, BM25, episodic memory, encrypted email registry.

### Testing
- No test framework/runner. `apps/tests/obsidian_chroma.py` is a manual script; `apps/text_to_speech/tests/` is empty. No CI.

## Frontend (`dynamic-island`)

### Commands (pnpm)
- `pnpm dev` — Vite, port 1420 strict.
- `pnpm tauri dev` — full Tauri dev (runs `pnpm dev` as `beforeDevCommand`).
- `pnpm build` — `tsc && vite build` (also the Tauri `beforeBuildCommand`).
- `pnpm tauri build` — prod bundle.

### Conventions / gotchas
- **Lint is `oxlint` (`pnpm lint`, `pnpm lint:fix`); formatting is `oxfmt` (`pnpm format`, `pnpm format:check`).** Do NOT use eslint/prettier — `oxlint`/`oxfmt` are the tools. (No earlier `format` name for it.)
- Vite alias `@/` → `src/`.
- Tailwind v4 via `@tailwindcss/vite`; shadcn-style components in `src/components/ui/` (cva + clsx + tailwind-merge; `cn()` in `src/lib/utils.ts`).
- Rust side (`src-tauri/src/lib.rs`) only has a placeholder `greet` command and pure `microphone` permission; the UI is a demo not yet connected to the backend. `src/App.tsx` only renders the DynamicIsland.
- Dead/legacy code to ignore: `src/App.bak.tsx`, `src/components/Sample/` (superseded by `src/components/DynamicIsland/` and `src/components/Alfred/`).