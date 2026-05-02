from sqlmodel import create_engine
from sqlmodel import SQLModel
from config import Settings


class DatabaseEngine:
    def __init__(self, settings: Settings):
        self.sqlite_url = f"sqlite:///{settings.USER_DB_PATH}"
        self.engine = create_engine(self.sqlite_url, echo=True)

        self.__init_db()

    def __init_db(self):

        SQLModel.metadata.create_all(self.engine)
