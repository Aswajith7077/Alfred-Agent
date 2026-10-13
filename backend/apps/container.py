from config import Settings
from agents import PromptManager, OllamaChatConfig


class ServiceContainer:
    def __init__(self):
        self.settings = Settings()
        self.prompt_manager = PromptManager(str(self.settings.TEMPLATES_PATH))
        self.ollama_config = OllamaChatConfig()

        self.__init_vector_db()
        self.__init_obsidian()
        self.__init_email()
        self.__init_speaker()
        self.__init_diarization()

    def __init_vector_db(self):
        from vector_db import VectorDB, BM25Ranker

        self.bm25 = BM25Ranker(persist_path=str(self.settings.BM25_INDEX_PATH))
        self.vector_db = VectorDB(
            settings=self.settings,
            bm25_ranker=self.bm25,
        )

    def __init_obsidian(self):
        from obsidian import Obsidian

        self.obsidian = Obsidian(
            vault_path=str(self.settings.VAULT_PATH), db_service=self.vector_db
        )
        self.obsidian.sync_to_vector_db()

    def __init_email(self):
        if not (self.settings.EMAIL_ADDRESS_I and self.settings.EMAIL_APP_PASSWORD_I):
            print("[ServiceContainer] No email credentials configured - skipping email integration")
            self.emails = None
            return

        from emails import register_emails

        self.emails = register_emails()

    def __init_speaker(self):
        from database import DatabaseEngine, SpeakerRepository
        from crypto import FernetEncryption
        from speech_to_text.modules import Verifier

        try:
            db_engine = DatabaseEngine(self.settings)
            fernet = FernetEncryption(self.settings.ENROLLMENT_KEY_PATH)
            repository = SpeakerRepository(db_engine.engine, fernet)
            self.speaker_module = Verifier(repository)
        except Exception as e:
            print(f"[ServiceContainer] Speaker module unavailable - skipping: {e}")
            self.speaker_module = None

    def __init_diarization(self):
        if not self.settings.DIARIZATION_ENABLED:
            self.diarization_module = None
            return

        from diarization import DiarizationManager

        self.diarization_module = DiarizationManager(
            segmentation_model=self.settings.DIARIZATION_SEGMENTATION_MODEL,
            embedding_model=self.settings.DIARIZATION_EMBEDDING_MODEL,
        )

    def get_tools(self):
        return [tool for tool in [self.obsidian, self.emails] if tool is not None]
