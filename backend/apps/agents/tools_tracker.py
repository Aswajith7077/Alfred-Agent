from pathlib import Path
import json

class ToolUsageTracker:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(exist_ok=True)
        self.stats = json.loads(self.path.read_text()) if self.path.exists() else {
            "counts": {},
            "combinations": {}
        }

    def record(self, tools_used: list):
        # Individual counts
        for t in tools_used:
            self.stats["counts"][t] = self.stats["counts"].get(t, 0) + 1

        # Pair combinations
        for i, a in enumerate(tools_used):
            for b in tools_used[i+1:]:
                key = f"{a}+{b}"
                self.stats["combinations"][key] = self.stats["combinations"].get(key, 0) + 1

        self.path.write_text(json.dumps(self.stats, indent=2))

    def top_combinations(self, top_k=3) -> list:
        combos = self.stats["combinations"]
        return sorted(combos, key=combos.get, reverse=True)[:top_k]