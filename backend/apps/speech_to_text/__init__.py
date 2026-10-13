import importlib

__all__ = [
    "AudioPipelineManager",
    "register_stt_tasks",
]

_LAZY = {
    "register_stt_tasks": (".utils", "register_stt_tasks"),
    "AudioPipelineManager": (".pipeline", "AudioPipelineManager"),
}


def __getattr__(name):
    if name in _LAZY:
        module_name, attr = _LAZY[name]
        module = importlib.import_module(module_name, __name__)
        return getattr(module, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
