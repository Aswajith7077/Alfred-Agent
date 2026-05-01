from pathlib import Path
import json


class IndexState:
    def __init__(self, path: str):
        self.path = Path(path)
        self.state = self._load()

    def _load(self):

        if not self.path.exists():
            return {}

        with open(self.path, "r") as f:
            return json.load(f)

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.state, f, indent=2)
