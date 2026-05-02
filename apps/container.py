from config import Settings
from agents import PromptManager, OllamaChatConfig


class ServiceContainer:
    def __init__(self):
        self.settings = Settings()
        self.prompt_manager = PromptManager(str(self.settings.TEMPLATES_PATH))
        self.ollama_config = OllamaChatConfig()

        self.__init_vector_db()
        self.__init_obsidian()

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

    def get_tools(self):
        return [self.obsidian]
