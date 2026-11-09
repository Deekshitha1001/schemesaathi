"""Speech-to-text with Whisper (via faster-whisper), loaded lazily.

Install with `pip install faster-whisper`. The first call downloads the model
(`small` is a good accuracy/speed balance for Hindi and Kannada on CPU).
If the package is missing, the API reports transcription as unavailable and the
frontend falls back to the browser's built-in speech recognition.
"""

from __future__ import annotations

import importlib.util
import os
import tempfile

SUPPORTED = {"en": "en", "hi": "hi", "kn": "kn"}


def is_available() -> bool:
    return importlib.util.find_spec("faster_whisper") is not None


class Transcriber:
    def __init__(self, model_size: str = "small"):
        self.model_size = model_size
        self._model = None

    def _load(self):
        if self._model is None:
            from faster_whisper import WhisperModel  # lazy: heavy optional dependency

            self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
        return self._model

    def transcribe(self, audio_bytes: bytes, lang: str | None = None, suffix: str = ".webm") -> dict:
        """Returns {"text": str, "language": str}. Audio is written to a temp file and deleted immediately."""
        model = self._load()
        fd, path = tempfile.mkstemp(suffix=suffix)
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(audio_bytes)
            segments, info = model.transcribe(path, language=SUPPORTED.get(lang or ""), vad_filter=True, beam_size=5)
            text = " ".join(segment.text.strip() for segment in segments).strip()
            return {"text": text, "language": info.language}
        finally:
            try:
                os.remove(path)
            except OSError:
                pass
