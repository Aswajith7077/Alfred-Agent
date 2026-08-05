# Personal Agent ("Alfred")

A personal AI assistant that combines a local voice + LLM agent backend with a macOS-style "dynamic island" desktop UI. The two halves are developed independently and are **not yet wired together**.

## Repo layout

| Path | What it is |
|------|------------|
| `backend/` | Python 3.14 agent (`alfred`) — LangGraph agent over Ollama, Obsidian knowledge base, email, speech-to-text / text-to-speech. Managed with `uv`. |
| `dynamic-island/` | Tauri 2 + React 19 + Vite Desktop UI (pnpm) — a self-contained dynamic-island demo. |

## Quick start

```sh
# Backend agent (from repo root)
cd backend && uv sync
cd apps && python main.py        # runs from apps/ as the import root

# Frontend UI
cd dynamic-island && pnpm install
pnpm dev                         # Vite on :1420
pnpm tauri dev                   # full Tauri app
```

## Docs

- `AGENTS.md` — operational guide: entrypoint gotchas, setup, runtime requirements.
- `backend/README.md`, `dynamic-island/README.md` — per-package details.

> Not yet implemented: backend ↔ UI connectivity, CI, and automated tests.