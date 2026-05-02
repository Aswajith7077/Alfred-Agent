from threading import Thread
from speech_to_text import ConvertionConfig
from speech_to_text import WhisperModelConfig
from speech_to_text import Recorder
from speech_to_text.models import SpeakerConfig


convertion_config = ConvertionConfig()
model_config = WhisperModelConfig()
speaker_config = SpeakerConfig()

recorder = Recorder(convertion_config=convertion_config, model_config=model_config,speaker_config=speaker_config)


thread = Thread(target=recorder.record, daemon=True)
thread.start()
recorder.transcriber()
