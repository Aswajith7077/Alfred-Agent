import importlib

__all__ = [
    "QueryAggregator",
    "VAD",
    "Verifier",
    "Transcriber",
    "SilenceGatedSegmenter",
]

_LAZY = {
    "VAD": ".vad",
    "SilenceGatedSegmenter": ".segmention",
    "Verifier": ".verifier",
    "Transcriber": ".transcriber",
    "QueryAggregator": ".query_aggregator",
}


def __getattr__(name):
    if name in _LAZY:
        module = importlib.import_module(_LAZY[name], __name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
