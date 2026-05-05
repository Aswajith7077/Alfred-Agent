from cryptography.fernet import Fernet
from config import Settings
import numpy as np
import io
import os


class FernetEncryption:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.fernet = self._get_or_create_key()

    def _get_or_create_key(self) -> Fernet:
        if os.path.exists(self.settings.KEY_PATH):
            with open(self.settings.KEY_PATH, "rb") as f:
                return Fernet(f.read())

        # Create directory if it doesn't exist
        key_dir = os.path.dirname(self.settings.KEY_PATH)
        if key_dir:
            os.makedirs(key_dir, exist_ok=True)

        key = Fernet.generate_key()
        with open(self.settings.KEY_PATH, "wb") as f:
            f.write(key)
        os.chmod(self.settings.KEY_PATH, 0o600)  # owner read-only
        return Fernet(key)

    def encrypt(self, raw_embedding: np.ndarray) -> bytes:
        buf = io.BytesIO()
        np.save(buf, raw_embedding)
        encrypted_blob = self.fernet.encrypt(buf.getvalue())

        return encrypted_blob

    def decrypt(self, encrypted_blob: bytes) -> np.ndarray:
        decrypted_bytes = self.fernet.decrypt(encrypted_blob)

        buf = io.BytesIO(decrypted_bytes)
        buf.seek(0)
        decrypted_embedding = np.load(buf, allow_pickle=False)

        return decrypted_embedding
