import json
from pathlib import Path
from datetime import datetime

class EpisodicMemory:
    def __init__(self, path: str = "memory/episodes.json"):
        self.path = Path(path)
        self.path.parent.mkdir(exist_ok=True)
        self.episodes = json.loads(self.path.read_text()) if self.path.exists() else []

    def record(self, query: str, tools_used: list, outcome: str, success: bool):
        self.episodes.append({
            "query": query,
            "tools_used": tools_used,
            "outcome": outcome,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
        self.path.write_text(json.dumps(self.episodes, indent=2))

    def recall(self, query: str, top_k: int = 3) -> list:
        """Return most relevant past episodes by keyword overlap."""
        query_words = set(query.lower().split())
        scored = []
        for ep in self.episodes:
            overlap = query_words & set(ep["query"].lower().split())
            if overlap:
                scored.append((len(overlap), ep))
        scored.sort(reverse=True)
        return [ep for _, ep in scored[:top_k]]