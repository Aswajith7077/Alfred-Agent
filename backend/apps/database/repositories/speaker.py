# repository.py
from sqlmodel import Session, select
from database.schema import Speaker
from database.schema import Role
import numpy as np
import io
from datetime import datetime
from datetime import timezone
from hashlib import sha256
from crypto import FernetEncryption


class SpeakerRepository:
    def __init__(self, engine, fernet_handler: FernetEncryption):
        self.engine = engine
        self.fernet = fernet_handler

    def _hash(self, raw: bytes) -> str:
        return sha256(raw).hexdigest()

    def insert_speaker(self, name: str, embedding: np.ndarray, role: Role):

        encrypted_blob = self.fernet.encrypt_embedding(embedding)
        with Session(self.engine) as session:
            if role == Role.ROOT:
                existing_root = session.exec(
                    select(Speaker).where(Speaker.role == Role.ROOT)
                ).first()

                if existing_root:
                    raise ValueError("Only one ROOT speaker allowed")

            statement = select(Speaker).where(Speaker.name == name)
            speaker = session.exec(statement).first()

            # Speaker Already Exists
            if speaker:
                speaker.name = name
                speaker.embedding = encrypted_blob
                speaker.embedding_hash = self._hash(encrypted_blob)
                speaker.role = role
                speaker.session_count += 1
            else:
                speaker = Speaker(
                    name=name,
                    embedding=encrypted_blob,
                    embedding_hash=self._hash(encrypted_blob),
                    first_seen=datetime.now(timezone.utc),
                    role=role,
                    session_count=1,
                )
                session.add(speaker)

            session.commit()

    def get_speaker_embedding(self, speaker_id: str):
        with Session(self.engine) as session:
            speaker = session.get(Speaker, speaker_id)
            if speaker:
                return np.load(io.BytesIO(speaker.embedding))

            if self._hash(speaker.embedding) != speaker.embedding_hash:
                raise ValueError(f"Voiceprint tampered for '{speaker_id}'.")
            return

    def get_root_embedding(self):
        with Session(self.engine) as session:
            root_user = session.exec(
                select(Speaker).where(Speaker.role == Role.ROOT)
            ).first()

            if not root_user:
                return None

            try:
                decrypted_embedding = self.fernet.decrypt_embedding(root_user.embedding)
                return decrypted_embedding
            except Exception as e:
                print(
                    f"[SpeakerRepository] Warning: Failed to decrypt root embedding: {e}"
                )
                print(
                    "[SpeakerRepository] Root user data may be corrupted or using different encryption key"
                )
                return None

    def get_name(self, speaker_id: str):
        with Session(self.engine) as session:
            speaker = session.get(Speaker, speaker_id)
            return speaker.name if speaker else None

    def all_known_speakers(self):
        with Session(self.engine) as session:
            speakers = session.exec(select(Speaker)).all()

            result = []
            for s in speakers:
                if self._hash(s.embedding) != s.embedding_hash:  # <-- added
                    raise ValueError(f"Voiceprint tampered for '{s.id}'.")
                emb = np.load(io.BytesIO(s.embedding))
                result.append({"id": s.id, "name": s.name, "embedding": emb})

            return result
