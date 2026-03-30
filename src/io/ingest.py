from __future__ import annotations

from pathlib import Path

from src.core.models import VideoMetadata
from src.utils.ffmpeg_utils import probe_video

SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".mkv"}


def discover_videos(input_dir: str | Path) -> list[Path]:
    base = Path(input_dir)
    files = [p for p in base.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS]
    return sorted(files)


def read_video_metadata(video_path: str | Path) -> VideoMetadata:
    data = probe_video(video_path)
    streams = data.get("streams", [])
    v_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
    fps_raw = v_stream.get("avg_frame_rate", "0/1")
    num, den = fps_raw.split("/")
    fps = float(num) / max(float(den), 1.0)
    duration = float(v_stream.get("duration") or data.get("format", {}).get("duration", 0.0))
    return VideoMetadata(
        path=str(video_path),
        filename=Path(video_path).name,
        duration=duration,
        fps=fps,
        width=int(v_stream.get("width", 0)),
        height=int(v_stream.get("height", 0)),
        has_audio=bool(a_stream),
    )
