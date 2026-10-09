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

## Docker

```sh
cp .env.example .env   # fill in VAULT_PATH, email, and HF token

docker compose build
docker compose up -d ollama frontend   # ollama + static UI demo on :8080
docker compose run --rm backend        # interactive agent (needs a TTY)
```

- `backend/Dockerfile` — the agent, including the heavy ML stack (torch, faster-whisper, pyannote-audio, speechbrain). The agent reads from stdin, so it must be run with a TTY attached (`docker compose run`, not `up -d`).
- `dynamic-island/Dockerfile` — builds the Vite/React UI as a static bundle served by nginx. This is the web build of the demo only; the Tauri/Rust desktop shell isn't containerized (it produces a native binary).
- `docker-compose.yml` wires both to a local `ollama` service. Persistent state (`db/`), `secrets/`, and `keys/` are bind-mounted/volumed so they survive container recreation.
- `.github/workflows/docker-build-check.yml` builds both images on every PR (no push) to catch breakage early; `.github/workflows/docker-publish.yml` builds and pushes to GHCR on every PR merged into `main`.

## Docs

- `AGENTS.md` — operational guide: entrypoint gotchas, setup, runtime requirements.
- `backend/README.md`, `dynamic-island/README.md` — per-package details.

> Not yet implemented: backend ↔ UI connectivity and automated tests. CI is limited to Docker build/publish (see below).