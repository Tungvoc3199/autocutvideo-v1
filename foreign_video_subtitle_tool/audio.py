from __future__ import annotations

from pathlib import Path

from .ffmpeg_utils import extract_audio_command, run_command


def extract_audio(input_path: Path, output_wav: Path, log_file: Path | None = None) -> list[str]:
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    command = extract_audio_command(input_path, output_wav)
    run_command(command, log_file=log_file)
    return command
