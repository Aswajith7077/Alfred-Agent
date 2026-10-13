# Pipeline Audit: Speech → VAD → Speaker Auth → Query → Obsidian RAG → LLM → TTS

**Requested pipeline:** Speech to text → VAD/silence rejection → speaker diarization + voice auth/authorization → query processing → Obsidian KB retrieval → LLM-summarized text → text-to-speech (Piper)

**Verdict: No. This pipeline has never run end-to-end and cannot, as currently written.** Every stage exists as *code*, but the wiring between stages is either commented out, silently disconnected, or guarded by a dependency that was never set up. Below is each stage's real status, followed by the blockers in the order you'd hit them if you tried to run it right now (no Docker, local machine).

Environment checked (this machine): Ollama reachable at `127.0.0.1:11434` with `llama3.1:8b` and `llama3.2:latest` pulled; `nomic-embed-text` **not** pulled; `backend/.venv` has all declared dependencies installed; no `.env` file present (only the root `.env.example` template); no `backend/secrets/gmail/` directory.

---

## 1. Stage-by-stage status

| # | Stage | Code location | Status |
|---|-------|---------------|--------|
| 1 | Speech to text | `speech_to_text/recorder.py`, `modules/transcriber.py` | ⚠️ Works in isolation, but gated by #3 below |
| 2 | VAD / silence rejection | `modules/vad.py`, `modules/segmention.py` | ✅ Works, looks solid |
| 3 | Speaker diarization | `modules/speaker_diarization.py` | ⛔ **Does not exist** — entire file is commented out |
| 3b | Voice authentication (1:1 verify) | `modules/verifier.py`, `database/repositories/speaker.py` | ❌ Permanently blocks all audio — no enrollment path exists |
| 4 | Query processing | `modules/query_aggregator.py`, `agents/prompt_manger.py` | ✅ Logic is fine, but never reaches the agent (see #2 below) |
| 5 | Obsidian KB retrieval | `obsidian/service.py`, `vector_db/vector_db.py` | ❌ Returns 0 documents (wrong vault path + missing embedding model) |
| 6 | LLM summarization | `agents/agents.py`, `create_agent.py` | ❌ Agent can't even be constructed (see #1 below) |
| 7 | Text to speech (Piper) | `text_to_speech/service.py` | ⚠️ Works standalone, never called from the pipeline |

---

## 2. Critical blockers, in the order you'd hit them

### Blocker 1 — Agent creation hard-crashes without Gmail credentials
`container.py:5-13` (`ServiceContainer.__init__`) unconditionally calls `self.__init_email()` → `register_emails()` (`emails/utils/register_emails.py:10-20`), which builds two `EmailAccount` pydantic models from `EMAIL_ADDRESS_I/II` and `EMAIL_APP_PASSWORD_I/II`. Those fields are typed `address: str` / `app_password: str` with **no `Optional`** (`schema/email.py:5-8`). With no `.env`, `Settings.EMAIL_ADDRESS_I` is `None`, and `EmailAccount(address=None, ...)` raises a `pydantic.ValidationError` immediately.

**Effect:** `create_agent()` → `ServiceContainer()` throws before the LLM, Obsidian, or anything else is touched. Email is unrelated to the requested pipeline but is a mandatory, unconditional dependency of agent construction — there's no way to opt out.

### Blocker 2 — The orchestrator never starts the speech pipeline
`orchestrator.py:32`:
```python
def register(self):
    register_agent_tasks(self.agent_manager)
    # register_stt_tasks(self.stt_manager, self.prompt_manager.build_prompt)
```
The STT registration call is commented out. Running `main.py` only ever spawns the `Agent` process — `Preprocessor`, `Recorder`, `VAD`, `Transcriber`, and `QueryAggregator` are never registered, so `Orchestrator._start_all()` never spawns them. The microphone never opens.

### Blocker 3 — Even if started, STT output can't reach the agent
`agents/utils/agent_tasks.py:8-11`:
```python
def run_agent(llm_queue: MPQueue):
    orchestrator = create_agent()
    while True:
        # query_dict = llm_queue.get()
        query_text = input(">>> ")
```
The agent process takes its queries from **stdin**, not from `llm_queue` — the queue parameter is accepted but never read (the line that would read it is commented out). This means the STT pipeline and the agent pipeline are two parallel, unconnected systems: `QueryAggregator` would push finished prompts into `llm_queue` (`query_aggregator.py:55`), and nothing on the other end ever drains it. Fixing Blocker 2 alone would not connect voice input to the agent.

### Blocker 4 — Voice authentication permanently rejects all audio (no enrollment exists)
`modules/transcriber.py:33-39` requires `Verifier.verify_fast()` to return `True` before transcribing anything:
```python
root_user_hit, score = self.verifier.verify_fast(audio)
if not root_user_hit:
    print(f"Transcription skipped - root user not detected (score: {score})")
    return
```
`Verifier.verify_fast` (`verifier.py:60-73`) compares the live embedding against `self.personal_embedding`, loaded via `SpeakerRepository.get_root_embedding()` (`database/repositories/speaker.py:66-85`), which returns `None` if no `Speaker` row has `role == Role.ROOT`.

`SpeakerRepository.insert_speaker()` (`repositories/speaker.py:21-54`) is the only code path that could ever create that row — and it is **never called anywhere in the codebase** (confirmed by repo-wide grep). There is no enrollment script, CLI command, or process spec for it. `speech_to_text/models/speaker.py` even defines a `SpeakerConfig` with `voiceprint_path`, `enrollment_duration`, etc. — but nothing instantiates or uses it either.

**Effect:** `personal_embedding` is always `None`; `verify_fast` always returns `(False, 0.0)`; every single audio segment is silently dropped, forever. This is a hard, unconditional block independent of everything else on this list.

### Blocker 5 — "Speaker diarization" is dead code
`modules/speaker_diarization.py` is **entirely commented out**, top to bottom (pyannote.audio `Pipeline`, `SpeakerDiarization` class, `diarize()` — all of it). It is not imported anywhere, not registered as a process, not referenced from `transcriber.py`. What the pipeline actually implements under "speaker" handling is 1:1 **voice verification** (Blocker 4), not **diarization** (multi-speaker segmentation/labeling). If multi-speaker diarization is actually wanted, it needs to be written from scratch, not just re-enabled — the commented code also has a known bug noted in its own comments about `pipeline()` output shape.

### Blocker 6 — Wrong/missing Ollama models
- `agents/models/ollama.py:5`: `OllamaChatConfig.model_name` defaults to `"gemma4:e2b"` — not a real, pulled model on this machine (only `llama3.1:8b` and `llama3.2:latest` are available; "gemma4" isn't even a published Ollama tag family — likely a typo for `gemma3`).
- `config/settings.py:33`: `EMBEDDING_MODEL = "nomic-embed-text"` — confirmed **not pulled** (`ollama list` / `/api/tags` has no `nomic` entry). `VectorDB.__init__` (`vector_db/vector_db.py:27-29`) builds `OllamaEmbeddings(model="nomic-embed-text", ...)` unconditionally in the constructor, and `ServiceContainer.__init_obsidian()` immediately calls `sync_to_vector_db()` on every agent startup (`container.py:30`) — so even past Blockers 1–3, agent construction would fail the first time it tries to embed a document.

### Blocker 7 — Obsidian vault path is hardcoded to a Windows path
`config/settings.py:14-16`:
```python
VAULT_PATH = os.environ.get(
    "VAULT_PATH", "C:\\Users\\Aswajith S\\OneDrive\\Documents\\ObsidianVault"
)
```
No `VAULT_PATH` env var is set on this machine, so it falls back to a Windows path that doesn't exist on Linux. `Obsidian.__recursive_load_documents` (`obsidian/service.py:35-39`) catches the resulting `OSError` and prints a warning, so it won't crash — but it silently yields zero documents, meaning Obsidian KB retrieval has nothing to search even after every other blocker is fixed. (Already flagged as a known gotcha in `AGENTS.md`, confirmed here as a live pipeline blocker, not just a README note.)

### Blocker 8 — TTS (Piper) is never called by anything in the pipeline
`Agent.run()` (`agents/agents.py:100-165`) `yield`s response text chunks — the only consumer is `run_agent` (`agent_tasks.py:17-20`), which just `print()`s them to stdout. **Nothing in the entire codebase calls `PiperService.synthesize()` except `backend/apps/sample.py`**, a standalone demo script that is not part of any registered process or pipeline stage. There is no "LLM text → TTS" handoff at all — `text_to_speech/main.py` (the would-be entrypoint) is an **empty file**, and no `register_tts_tasks`-equivalent exists anywhere (confirmed against `register_agent_tasks` / `register_stt_tasks`, which do exist).

### Blocker 9 — `PiperService.synthesize()` crashes on its own default
`text_to_speech/service.py:17,23-31`:
```python
def __init__(self, voice: Voice, config: Optional[PiperConfig] = None):
    ...
    self.config = config
def synthesize(self, text: str):
    syn_config = SynthesisConfig(volume=self.config.volume, ...)
```
If `config` is omitted (its own documented default), `self.config` is `None` and `self.config.volume` raises `AttributeError`. The only reason the standalone demo (`sample.py:11`) works is that it happens to pass `config=PiperConfig()` explicitly. Any future wiring that constructs `PiperService(voice)` the "default" way will crash immediately.

---

## 3. Secondary bugs (latent — won't block the current dead pipeline, but will surface once the above are fixed)

- **`SpeakerRepository.get_speaker_embedding`** (`repositories/speaker.py:56-64`): the tamper-check (`if self._hash(speaker.embedding) != speaker.embedding_hash`) sits *after* the `if speaker:` branch already returned — so it only runs when `speaker is None`, where `speaker.embedding` raises `AttributeError` instead of returning `None`/raising a sane error. (Currently unused by any caller, so dormant.)
- **`QueryAggregator._silence_expired`** (`query_aggregator.py:59-63`) references `self._last_activity` and `self.silence_timeout`, neither of which is ever set in `__init__`. Dead method — `start()` never calls it — but it's a landmine if someone wires it in later.
- **`VectorDB`** (`vector_db/vector_db.py:30-34`) passes `settings.VECTOR_DB_PATH` (a `pathlib.Path`) directly as `Chroma(persist_directory=...)`, which generally expects a `str`. Likely tolerated by the current `chromadb` version, but untyped and worth a `str()` cast.

---

## 4. Net assessment

Nothing here is a "small misconfiguration" — the pipeline stages were each built and appear individually reasonable (VAD/segmenter, Whisper transcription, resemblyzer verification, BM25+Chroma hybrid retrieval, Piper synthesis), but **the stages were never connected to each other**, and three of the connections (`orchestrator.register`, `run_agent`'s queue read, and any STT→TTS handoff) are explicitly commented out or simply absent. On top of that, one stage (voice auth) has no way to ever succeed because its setup step (enrollment) doesn't exist, and one stage (speaker diarization) doesn't exist at all beyond a commented-out file.

To get a flawless, Docker-free run of the requested pipeline, each of the 9 blockers above needs an explicit fix or decision (e.g., make email optional, write an enrollment flow, rewire the queue, set `VAULT_PATH`, pull `nomic-embed-text`, fix the default chat model, wire STT output → agent → TTS). This report only documents what's broken; no code has been changed yet.

---

## 5. Fixes applied (after this report, per user decisions)

Decisions: voice **authorization only** (no diarization rebuild), email made **optional**, chat model **`llama3.1:8b`**, vault path **`~/Documents/ObsidianVault`**.

| Blocker | Fix |
|---|---|
| 1. Email hard-crash | `container.py`: skip email registration when `EMAIL_ADDRESS_I`/`EMAIL_APP_PASSWORD_I` aren't set; `get_tools()` filters out `None` |
| 2. STT never started | `orchestrator.py`: uncommented `register_stt_tasks(...)` |
| 3. STT output discarded | `agent_tasks.py`: `run_agent` now reads `llm_queue.get()` instead of `input()` |
| 4. Voice auth never passes | Added `enroll_speaker.py` (records mic sample, stores root voiceprint via existing `SpeakerRepository.insert_speaker`) |
| 5. Diarization | Left as dead/commented code per decision — out of scope |
| 6. Wrong Ollama models | `agents/models/ollama.py`: default model → `llama3.1:8b`; pulled `nomic-embed-text` into local Ollama |
| 7. Hardcoded Windows vault path | `backend/.env`: `VAULT_PATH=/home/aswajiths/Documents/ObsidianVault` |
| 8/9. TTS never called / crashes on default | `agent_tasks.py` now synthesizes the full agent response via `PiperService` after each turn; `PiperService.__init__` defaults `config` to `PiperConfig()` instead of `None` |
| (new) `build_prompt` duplicated system prompt into the user message | `prompt_manger.py`: `build_prompt` now returns just the cleaned transcript; the system prompt is injected once, by `Agent.run()` |
| (new, found while testing) `IndexState.save()` crashed — never created its parent dir | `obsidian/index.py`: added `mkdir(parents=True, exist_ok=True)` |
| (new, found while testing) `DatabaseEngine` crashed — never created the SQLite file's parent dir | `database/connection.py`: creates the parent dir for `sqlite:///` URLs before connecting |
| Minor | `vector_db.py`: `Chroma(persist_directory=...)` now passed `str(...)` instead of a `Path` |

### Verified by actually running the code in this environment

- `create_agent()` → `ServiceContainer()`: email skipped cleanly, Obsidian vault (130 notes under `~/Documents/ObsidianVault`) synced to Chroma + BM25, agent built with tools `['sync_to_vector_db', 'search']`. ✅
- Full chain **query → Obsidian search tool → BM25+Chroma retrieval → LLM response**: ran a real query end-to-end and got a grounded answer citing vault notes. ✅ (used `llama3.2:latest` for this run — see caveat below)
- `PiperService` synthesis: constructs and synthesizes without the `None`-config crash. ✅
- Enrollment → verification round-trip: `insert_speaker()` → `Verifier.verify_fast()` on a fresh `Verifier` instance correctly loads and matches the stored embedding. ✅ (synthetic test audio, not a real voice — see caveat below)
- `Orchestrator().register()`: all 6 process specs now register (`Agent`, `Preprocessor`, `Recorder`, `VAD`, `Transcriber`, `QueryAggregator`) — previously only `Agent`. ✅

### Caveats — not fully verifiable in this sandbox

- **`llama3.1:8b` vs. available RAM**: this machine has 15 GiB total but only ~2.3–2.6 GiB free at the time of testing (other processes using the rest); Ollama refused to load `llama3.1:8b` ("requires more system memory... than is available"). The config was left at `llama3.1:8b` per your choice since it's a resource contention issue, not a hardware ceiling — free up memory (close other apps) before running, or switch `OllamaChatConfig.model_name` to `llama3.2:latest` if this persists.
- **No real microphone in this sandbox**: `Recorder`, live `VAD`→`Transcriber`→`QueryAggregator` flow, and `enroll_speaker.py`'s actual recording step could not be exercised with real audio hardware. The enrollment→verification *mechanism* was validated with synthetic audio (random noise) standing in for a voice sample — confirms the plumbing, not resemblyzer's real-world discrimination accuracy. Run `cd backend/apps && python enroll_speaker.py` yourself once, speaking normally, before the first real session.
- **Known rough edge, not fixed (out of scope)**: `SpeakerRepository.insert_speaker()` raises `ValueError("Only one ROOT speaker allowed")` on any second call once a ROOT exists, even to re-enroll the same name with a better sample. To re-enroll, delete `backend/db/functional/alfred_local.db` first.
- A test enrollment row was written and then deleted during verification — `backend/db/functional/alfred_local.db` was removed so your first real `enroll_speaker.py` run starts clean.
