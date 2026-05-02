from __future__ import annotations

__all__ = ["Obsidian"]


def __getattr__(name: str):
    if name == "Obsidian":
        from .service import Obsidian

        return Obsidian
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
