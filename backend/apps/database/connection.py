from sqlmodel import create_engine
from sqlmodel import SQLModel
from config import Settings
from pathlib import Path


class DatabaseEngine:
    def __init__(self, settings: Settings):
        self.db_url = settings.USER_DB_PATH
        if self.db_url.startswith("sqlite:///"):
            Path(self.db_url.removeprefix("sqlite:///")).parent.mkdir(
                parents=True, exist_ok=True
            )
        self.engine = create_engine(self.db_url, echo=True)

        self.__init_db()

    def __init_db(self):
        SQLModel.metadata.create_all(self.engine)
