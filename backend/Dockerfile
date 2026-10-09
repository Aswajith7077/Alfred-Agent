# syntax=docker/dockerfile:1

# --- Builder: resolve & install dependencies with uv ---
FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    portaudio19-dev \
    libsndfile1-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-install-project

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev

# --- Runtime: slim image with only what's needed to run the agent ---
FROM python:3.14-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libportaudio2 \
    libsndfile1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 alfred

WORKDIR /app

COPY --from=builder --chown=alfred:alfred /build/.venv /app/.venv
COPY --chown=alfred:alfred . .

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    OLLAMA_URL="http://ollama:11434"

# Persistent state (chroma/sqlite/bm25/episodic memory/registry), secrets, and keys.
# Mount these as volumes in deployment so data survives container recreation.
VOLUME ["/app/db", "/app/secrets", "/app/keys"]

USER alfred
WORKDIR /app/apps

# The orchestrator reads queries from stdin, so run with `docker run -it` /
# `stdin_open: true` + `tty: true` in compose.
ENTRYPOINT ["python", "main.py"]
