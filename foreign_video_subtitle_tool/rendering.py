from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from .config import SubtitleStyle
from .ffmpeg_utils import require_binary, run_command


def load_style(path: Path | None) -> SubtitleStyle:
    if path is None:
        return SubtitleStyle()
    if importlib.util.find_spec("yaml") is None:
        raise RuntimeError("Chưa cài PyYAML để đọc subtitle style. Chạy: python -m pip install PyYAML")
    import yaml

    data: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    valid = {field for field in SubtitleStyle.__dataclass_fields__}
    filtered = {key: value for key, value in data.items() if key in valid}
    return SubtitleStyle(**filtered)


def escape_subtitle_path_for_filter(path: Path) -> str:
    value = str(path).replace("\\", "/")
    value = value.replace("'", r"\'").replace(":", r"\:")
    return value


def burn_subtitles_command(
    input_video: Path, vietnamese_srt: Path, output_video: Path, style: SubtitleStyle
) -> list[str]:
    subtitles_path = escape_subtitle_path_for_filter(vietnamese_srt)
    vf = f"subtitles='{subtitles_path}':force_style='{style.to_force_style()}'"
    return [
        require_binary("ffmpeg"),
        "-y",
        "-i",
        str(input_video),
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-crf",
        "20",
        "-preset",
        "medium",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        str(output_video),
    ]


def burn_subtitles(
    input_video: Path,
    vietnamese_srt: Path,
    output_video: Path,
    style_path: Path | None = None,
    log_file: Path | None = None,
) -> list[str]:
    output_video.parent.mkdir(parents=True, exist_ok=True)
    command = burn_subtitles_command(input_video, vietnamese_srt, output_video, load_style(style_path))
    run_command(command, log_file=log_file)
    return command
