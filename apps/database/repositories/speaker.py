# repository.py
from sqlmodel import Session, select
from database.schema import Speaker
import numpy as np
import io
from datetime import datetime


class SpeakerRepository:
    def __init__(self, engine):
        self.engine = engine

    def save(self, speaker_id: str, name: str, embedding: np.ndarray):
        buf = io.BytesIO()
        np.save(buf, embedding)
        blob = buf.getvalue()

        with Session(self.engine) as session:
            statement = select(Speaker).where(Speaker.id == speaker_id)
            speaker = session.exec(statement).first()

            # Speaker Already Exists
            if speaker:
                speaker.name = name
                speaker.embedding = blob
                speaker.session_count += 1
            else:
                speaker = Speaker(
                    id=speaker_id,
                    name=name,
                    embedding=blob,
                    first_seen=datetime.utcnow(),
                    session_count=1,
                )
                session.add(speaker)

            session.commit()

    def load_embedding(self, speaker_id: str):
        with Session(self.engine) as session:
            speaker = session.get(Speaker, speaker_id)
            if speaker:
                return np.load(io.BytesIO(speaker.embedding))
            return None

    def get_name(self, speaker_id: str):
        with Session(self.engine) as session:
            speaker = session.get(Speaker, speaker_id)
            return speaker.name if speaker else None

    def all_known(self):
        with Session(self.engine) as session:
            speakers = session.exec(select(Speaker)).all()

            result = []
            for s in speakers:
                emb = np.load(io.BytesIO(s.embedding))
                result.append({"id": s.id, "name": s.name, "embedding": emb})

            return result
