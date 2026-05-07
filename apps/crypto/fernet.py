from cryptography.fernet import Fernet
import numpy as np
import io
import os


class FernetEncryption:
    def __init__(self, key_path:str):
        self.key_path = key_path
        self.fernet = self._get_or_create_key()

    def _get_or_create_key(self) -> Fernet:
        if os.path.exists(self.key_path):
            with open(self.key_path, "rb") as f:
                return Fernet(f.read())

        # Create directory if it doesn't exist
        key_dir = os.path.dirname(self.key_path)
        if key_dir:
            os.makedirs(key_dir, exist_ok=True)

        key = Fernet.generate_key()
        with open(self.key_path, "wb") as f:
            f.write(key)
        os.chmod(self.key_path, 0o600)  # owner read-only
        return Fernet(key)

    def encrypt(self,context:bytes) -> bytes:
        encrypted = self.fernet.encrypt(context)
        return encrypted

    def decrypt(self,context:bytes) -> bytes:
        decrypted = self.fernet.decrypt(context)
        return decrypted
    
    def encrypt_embedding(self, raw_embedding: np.ndarray) -> bytes:
        buf = io.BytesIO()
        np.save(buf, raw_embedding)
        encrypted_blob = self.fernet.encrypt(buf.getvalue())

        return encrypted_blob

    def decrypt_embedding(self, encrypted_blob: bytes) -> np.ndarray:
        decrypted_bytes = self.fernet.decrypt(encrypted_blob)

        buf = io.BytesIO(decrypted_bytes)
        buf.seek(0)
        decrypted_embedding = np.load(buf, allow_pickle=False)

        return decrypted_embedding
