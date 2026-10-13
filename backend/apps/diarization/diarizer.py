"""sherpa-onnx speaker diarization. No heavy import happens at module import
time - sherpa_onnx is only imported inside _load(), on first diarize() call."""
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import List, Optional, Union

import numpy as np

from .models import Segment

TARGET_SR = 16000


class Diarizer:
    def __init__(self, segmentation_model: Union[str, Path], embedding_model: Union[str, Path]):
        self._segmentation_model = str(segmentation_model)
        self._embedding_model = str(embedding_model)
        self._pipeline = None

    def _build_config(self, num_clusters: int):
        import sherpa_onnx

        return sherpa_onnx.OfflineSpeakerDiarizationConfig(
            segmentation=sherpa_onnx.OfflineSpeakerSegmentationModelConfig(
                pyannote=sherpa_onnx.OfflineSpeakerSegmentationPyannoteModelConfig(
                    model=self._segmentation_model
                )
            ),
            embedding=sherpa_onnx.SpeakerEmbeddingExtractorConfig(
                model=self._embedding_model
            ),
            clustering=sherpa_onnx.FastClusteringConfig(num_clusters=num_clusters),
        )

    def _load(self):
        if self._pipeline is not None:
            return
        import sherpa_onnx

        self._pipeline = sherpa_onnx.OfflineSpeakerDiarization(self._build_config(-1))

    def _load_audio(self, audio: Union[str, Path, np.ndarray]) -> np.ndarray:
        if isinstance(audio, np.ndarray):
            return audio.astype(np.float32)

        path = Path(audio)
        with wave.open(str(path)) as w:
            needs_conversion = w.getframerate() != TARGET_SR or w.getnchannels() != 1

        if needs_conversion:
            with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
                subprocess.run(
                    [
                        "ffmpeg", "-y", "-i", str(path),
                        "-ar", str(TARGET_SR), "-ac", "1", "-c:a", "pcm_s16le",
                        tmp.name,
                    ],
                    check=True,
                    capture_output=True,
                )
                with wave.open(tmp.name) as w:
                    data = w.readframes(w.getnframes())
        else:
            with wave.open(str(path)) as w:
                data = w.readframes(w.getnframes())

        return np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

    def diarize(
        self, audio: Union[str, Path, np.ndarray], num_speakers: Optional[int] = None
    ) -> List[Segment]:
        self._load()

        if num_speakers is not None:
            self._pipeline.set_config(self._build_config(num_speakers))

        samples = self._load_audio(audio)
        result = self._pipeline.process(samples)
        return [
            Segment(start=seg.start, end=seg.end, speaker=str(seg.speaker))
            for seg in result.sort_by_start_time()
        ]
