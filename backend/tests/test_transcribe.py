"""Transcriber logic, tested with a fake `faster_whisper` module (the real model needs a download).

What is verified here: language mapping, joining segments, and that the uploaded audio is
ALWAYS deleted from disk afterwards (privacy). What is NOT verified: real Whisper accuracy.
"""
import os
import sys
import types

import pytest

from app import transcribe


class _Segment:
    def __init__(self, text):
        self.text = text


class FakeModel:
    instances = []

    def __init__(self, size, device, compute_type):
        self.args = (size, device, compute_type)
        self.calls = []
        self.seen_path = None
        self.seen_bytes = None
        FakeModel.instances.append(self)

    def transcribe(self, path, **kwargs):
        self.calls.append(kwargs)
        self.seen_path = path
        with open(path, "rb") as fh:
            self.seen_bytes = fh.read()
        if self.fail:
            raise RuntimeError("decode failed")
        return iter([_Segment(" ನಮಸ್ಕಾರ "), _Segment("ನಾನು ರೈತ")]), types.SimpleNamespace(language="kn")

    fail = False


@pytest.fixture()
def fake_whisper(monkeypatch):
    FakeModel.instances.clear()
    FakeModel.fail = False
    module = types.ModuleType("faster_whisper")
    module.WhisperModel = FakeModel
    monkeypatch.setitem(sys.modules, "faster_whisper", module)
    return FakeModel


def test_transcribes_and_joins_segments(fake_whisper):
    out = transcribe.Transcriber("small").transcribe(b"audio-bytes", "kn", ".webm")
    assert out == {"text": "ನಮಸ್ಕಾರ ನಾನು ರೈತ", "language": "kn"}
    model = fake_whisper.instances[0]
    assert model.args == ("small", "cpu", "int8") and model.seen_bytes == b"audio-bytes"
    assert model.calls[0]["language"] == "kn" and model.calls[0]["vad_filter"] is True


def test_audio_file_is_deleted_after_success(fake_whisper):
    transcribe.Transcriber().transcribe(b"x", "hi", ".webm")
    assert not os.path.exists(fake_whisper.instances[0].seen_path)


def test_audio_file_is_deleted_even_when_decoding_fails(fake_whisper):
    fake_whisper.fail = True
    t = transcribe.Transcriber()
    with pytest.raises(RuntimeError):
        t.transcribe(b"x", "hi", ".webm")
    assert not os.path.exists(fake_whisper.instances[0].seen_path)


def test_unknown_language_lets_whisper_detect(fake_whisper):
    transcribe.Transcriber().transcribe(b"x", "fr", ".webm")
    assert fake_whisper.instances[0].calls[0]["language"] is None


def test_model_is_loaded_once_and_lazily(fake_whisper):
    t = transcribe.Transcriber()
    assert fake_whisper.instances == []
    t.transcribe(b"x", "en", ".wav")
    t.transcribe(b"y", "en", ".wav")
    assert len(fake_whisper.instances) == 1


def test_is_available_reflects_the_package(monkeypatch):
    monkeypatch.setattr(transcribe.importlib.util, "find_spec", lambda name: None)
    assert transcribe.is_available() is False
