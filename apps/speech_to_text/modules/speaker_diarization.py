# from pyannote.audio import Pipeline
# from config import Settings
# import numpy as np
# import torch


# class SpeakerDiarization:
#     def __init__(self, sampling_rate: int, settings: Settings):

#         self.sampling_rate = sampling_rate
#         try:
#             self.pipeline = Pipeline.from_pretrained(
#                 "pyannote/speaker-diarization-community-1",
#                 token=settings.HUGGING_FACE_TOKEN,
#             )
#             print(
#                 "[SpeakerDiarization] Pyannote diarization pipeline loaded successfully"
#             )
#         except Exception as e:
#             print(
#                 f"[SpeakerDiarization] Warning: Could not load diarization pipeline: {e}"
#             )
#             print("[SpeakerDiarization] Falling back to single speaker mode")
#             self.pipeline = None

#     def _preprocess(self, audio_data: np.ndarray):

#         audio_data = audio_data.astype("float32")
#         waveform = torch.from_numpy(audio_data)

#         if waveform.ndim == 1:
#             waveform = waveform.unsqueeze(0)

#         return {"waveform": waveform, "sample_rate": self.sampling_rate}

#     def diarize(self, audio_data: np.ndarray):
#         if self.pipeline is None:
#             # Fallback: treat entire audio as single speaker segment
#             duration = len(audio_data) / self.sampling_rate
#             return [
#                 {
#                     "start": 0.0,
#                     "end": duration,
#                     "speaker": "SPEAKER_00",
#                 }
#             ]

#         processed_audio = self._preprocess(audio_data)
#         output = self.pipeline(processed_audio)

#         results = []

#         # pyannote "speaker-diarization" pipelines return an Annotation-like object,
#         # not an iterable of (segment, track, speaker) tuples. Use itertracks.
#         if hasattr(output, "itertracks"):
#             for segment, _, speaker in output.itertracks(yield_label=True):
#                 results.append(
#                     {
#                         "start": float(segment.start),
#                         "end": float(segment.end),
#                         "speaker": speaker,
#                     }
#                 )
#             return results

#         # Fallback for unexpected pipeline outputs (avoid crashing the whole pipeline).
#         try:
#             for segment, _, speaker in output:  # type: ignore[assignment]
#                 results.append(
#                     {
#                         "start": float(segment.start),
#                         "end": float(segment.end),
#                         "speaker": speaker,
#                     }
#                 )
#         except TypeError:
#             return []
#         return results
