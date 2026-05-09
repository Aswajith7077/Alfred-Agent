# email_registry.py
import json
import logging
from pathlib import Path

from schema import EmailAccount
from config import Settings
from crypto import FernetEncryption
from typing import List
from typing import Optional
from typing import Dict

logger = logging.getLogger(__name__)


class EmailRegistry:
    def __init__(
        self,
        settings:Settings,
        root_accounts: Optional[List[EmailAccount]] = None,
    ):

        self.registry_path = Path(settings.EMAIL_REGISTRY_JSON_PATH)
        self.key_path = Path(settings.EMAIL_REGISTRY_KEY_PATH)
        self._fernet = FernetEncryption(self.key_path)
        self._accounts: Dict[str, EmailAccount] = {}  # name → EmailAccount

        # load persisted state first
        self._load()

        # seed root accounts if registry is fresh
        if root_accounts:
            for acc in root_accounts:
                acc.protected = True   # enforce protection on roots
                if acc.name not in self._accounts:
                    self._accounts[acc.name] = acc
            self._save()


    # ── Persistence ──────────────────────────────────────────────────

    def _save(self):
        data = {name: acc.model_dump() for name, acc in self._accounts.items()}
        raw = json.dumps(data, indent=2).encode()
        encrypted = self._fernet.encrypt(raw)
        self.registry_path.write_bytes(encrypted)
        logger.debug(f"[Registry] Saved {len(self._accounts)} accounts")

    def _load(self):
        if not self.registry_path.exists():
            logger.info("[Registry] No registry found, starting fresh")
            return

        try:
            encrypted = self.registry_path.read_bytes()
            raw = self._fernet.decrypt(encrypted)
            data = json.loads(raw.decode())
            self._accounts = {
                name: EmailAccount.model_validate(acc)
                for name, acc in data.items()
            }
            logger.info(f"[Registry] Loaded {len(self._accounts)} accounts")
        except Exception as e:
            logger.error(f"[Registry] Failed to load registry: {e}")

    # ── Registry actions ─────────────────────────────────────────────

    def add(self, account: EmailAccount) -> bool:
        if account.name in self._accounts:
            logger.warning(f"[Registry] '{account.name}' already exists")
            return False

        self._accounts[account.name] = account
        self._save()
        logger.info(f"[Registry] Added: {account.name} ({account.address})")
        return True

    def remove(self, name: str) -> bool:
        if name not in self._accounts:
            logger.warning(f"[Registry] '{name}' not found")
            return False

        if self._accounts[name].protected:
            logger.warning(f"[Registry] '{name}' is protected and cannot be removed")
            return False

        del self._accounts[name]
        self._save()
        logger.info(f"[Registry] Removed: {name}")
        return True

    def update(self, name: str, **kwargs) -> bool:
        """Update fields on an existing account."""
        if name not in self._accounts:
            logger.warning(f"[Registry] '{name}' not found")
            return False

        acc = self._accounts[name]
        for key, value in kwargs.items():
            if hasattr(acc, key) and key != "protected":  # protect flag immutable
                setattr(acc, key, value)

        self._save()
        logger.info(f"[Registry] Updated: {name}")
        return True

    def get(self, name: str) -> Optional[EmailAccount]:
        return self._accounts.get(name)

    def list_accounts(self) -> List[dict]:
        return [
            {
                "name":      acc.name,
                "address":   acc.address,
                "protected": acc.protected,
                "imap_host": acc.imap_host,
            }
            for acc in self._accounts.values()
        ]

    def all(self) -> List[EmailAccount]:
        return list(self._accounts.values())