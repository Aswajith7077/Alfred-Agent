from pathlib import Path
from text_to_speech import Voice
from dotenv import load_dotenv
import os


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings:
    VAULT_PATH = os.environ.get(
        "VAULT_PATH", "C:\\Users\\Aswajith S\\OneDrive\\Documents\\ObsidianVault"
    )
    TEMPLATES_PATH = BASE_DIR / "templates"
    VECTOR_DB_PATH = BASE_DIR / "db" / "vector" / "obsidian-db"
    # USER_DB_PATH = os.environ.get("DATABASE_URL")
    USER_DB_PATH = "sqlite:///" + str(BASE_DIR / "db" / "functional" / "alfred_local.db")
    HUGGING_FACE_TOKEN = os.environ.get("HUGGING_FACE_TOKEN")
    STATE_DIR = BASE_DIR / "db" / "states"
    INDEX_STATE_PATH = STATE_DIR / "index_state.json"

    BM25_INDEX_PATH = STATE_DIR / "bm25_index.pkl"

    # Backwards-compatible alias (older code expects STATE_PATH to be the index state file)

    STATE_PATH = INDEX_STATE_PATH
    ENROLLMENT_KEY_PATH = BASE_DIR / "keys" / ".enrollment.key"
    OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
    COLLECTION_NAME = "obsidian_documents"
    EMBEDDING_MODEL = "nomic-embed-text"

    VOICE = Voice.ALFRED

    # Gmail Settings

    GMAIL_SCOPE_URL = "https://mail.google.com/"
    GMAIL_TOKEN_FILE = BASE_DIR / "secrets" / "gmail" / "token.json"
    GMAIL_CLIENT_SECRETS_FILE = BASE_DIR / "secrets" / "gmail" / "credentials.json"


    # Email Accounts
    EMAIL_NAME_I = "Personal"
    EMAIL_NAME_II = "Work"

    EMAIL_ADDRESS_I = os.environ.get("EMAIL_ADDRESS_I")
    EMAIL_ADDRESS_II = os.environ.get("EMAIL_ADDRESS_II")
    
    EMAIL_APP_PASSWORD_I = os.environ.get("EMAIL_APP_PASSWORD_I")
    EMAIL_APP_PASSWORD_II = os.environ.get("EMAIL_APP_PASSWORD_II")



    # Email Registry

    EMAIL_REGISTRY_JSON_PATH: str = BASE_DIR / "db" / "states" / "email" / "registry.json.enc"
    EMAIL_REGISTRY_KEY_PATH: str = BASE_DIR / "keys" / "email" / "registry.key"


    # Memory Paths

    EPISODIC_MEMORY_PATH: str = BASE_DIR / "db" / "states" / "agents" / "episodic_memory.json"
    TOOL_USAGE_TRACKER_PATH: str = BASE_DIR / "db" / "states" / "agents" / "tool_usage_tracker.json"


"""

EMAIL_ACCOUNTS: List[EmailAccount] = field(default_factory=lambda: [
    EmailAccount(
        name="Personal",
        address="you@gmail.com",
        app_password="xxxx xxxx xxxx xxxx",
    ),
    EmailAccount(
        name="Client",
        address="you@outlook.com",
        app_password="xxxx xxxx xxxx xxxx",
        imap_host="outlook.office365.com",
        smtp_host="smtp.office365.com",
    ),
])
"""