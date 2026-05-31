from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from typing import Any

from .models import SubtitleEntry
from .srt_utils import seconds_to_srt_timestamp, write_srt


def transcribe_audio(
    audio_path: Path,
    output_srt: Path,
    language: str = "auto",
    model_size: str = "small",
    device: str = "auto",
    compute_type: str = "auto",
) -> list[SubtitleEntry]:
    if importlib.util.find_spec("faster_whisper") is None:
        raise RuntimeError(
            "Chưa cài faster-whisper. Chạy: python -m pip install -r requirements-subtitle-tool.txt"
        )
    faster_whisper = importlib.import_module("faster_whisper")
    model_kwargs: dict[str, Any] = {}
    if device != "auto":
        model_kwargs["device"] = device
    if compute_type != "auto":
        model_kwargs["compute_type"] = compute_type
    model = faster_whisper.WhisperModel(model_size, **model_kwargs)
    transcribe_kwargs: dict[str, Any] = {"vad_filter": True}
    if language != "auto":
        transcribe_kwargs["language"] = language
    segments, _info = model.transcribe(str(audio_path), **transcribe_kwargs)
    entries = [
        SubtitleEntry(
            index=i,
            start=seconds_to_srt_timestamp(float(segment.start)),
            end=seconds_to_srt_timestamp(float(segment.end)),
            text=str(segment.text).strip(),
        )
        for i, segment in enumerate(segments, start=1)
        if str(segment.text).strip()
    ]
    write_srt(output_srt, entries)
    return entries
