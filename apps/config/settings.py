from pathlib import Path

from text_to_speech import Voice

from dotenv import load_dotenv

import os


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    VAULT_PATH = "C:\\Users\\Aswajith S\\OneDrive\\Documents\\ObsidianVault"

    TEMPLATES_PATH = BASE_DIR / "agents" / "templates"

    VECTOR_DB_PATH = BASE_DIR.parent / "db" / "vector" / "obsidian-db"

    USER_DB_PATH = os.environ.get("DATABASE_URL")

    HUGGING_FACE_TOKEN = os.environ.get("HUGGING_FACE_TOKEN")

    STATE_DIR = BASE_DIR.parent / "db" / "states"

    INDEX_STATE_PATH = STATE_DIR / "index_state.json"

    BM25_INDEX_PATH = STATE_DIR / "bm25_index.pkl"

    # Backwards-compatible alias (older code expects STATE_PATH to be the index state file)

    STATE_PATH = INDEX_STATE_PATH

    KEY_PATH = "keys/.enrollment.key"

    OLLAMA_URL = "http://127.0.0.1:11434"

    COLLECTION_NAME = "obsidian_documents"

    EMBEDDING_MODEL = "nomic-embed-text"

    VOICE = Voice.ALFRED
