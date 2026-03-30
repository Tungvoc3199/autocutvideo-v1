from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


class FFmpegNotFoundError(RuntimeError):
    pass


class FFmpegError(RuntimeError):
    pass


def ensure_ffmpeg() -> None:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise FFmpegNotFoundError(
            "ffmpeg/ffprobe not found in PATH. Install FFmpeg and add it to PATH."
        )


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise FFmpegError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result


def probe_video(path: str | Path) -> dict:
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    result = run_cmd(cmd)
    return json.loads(result.stdout)


def extract_subclip(
    src: str | Path,
    dst: str | Path,
    start: float,
    end: float,
    reencode: bool = True,
) -> None:
    duration = max(0.0, end - start)
    cmd = ["ffmpeg", "-y", "-ss", f"{start:.3f}", "-i", str(src), "-t", f"{duration:.3f}"]
    if reencode:
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac"]
    else:
        cmd += ["-c", "copy"]
    cmd.append(str(dst))
    run_cmd(cmd)


def normalize_video(
    src: str | Path,
    dst: str | Path,
    target_resolution: str,
    target_fps: int,
    audio_norm: bool,
) -> None:
    filters = [f"scale={target_resolution.replace('x', ':')}", f"fps={target_fps}"]
    vf = ",".join(filters)
    cmd = ["ffmpeg", "-y", "-i", str(src), "-vf", vf, "-c:v", "libx264", "-crf", "18"]
    if audio_norm:
        cmd += ["-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac"]
    else:
        cmd += ["-c:a", "copy"]
    cmd.append(str(dst))
    run_cmd(cmd)


def concat_videos(file_list_path: str | Path, dst: str | Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(file_list_path),
        "-c",
        "copy",
        str(dst),
    ]
    run_cmd(cmd)
