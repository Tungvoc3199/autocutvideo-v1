from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class DependencyError(RuntimeError):
    """Raised when an external command dependency is unavailable."""


def find_binary(name: str) -> str | None:
    return shutil.which(name)


def require_binary(name: str) -> str:
    binary = find_binary(name)
    if not binary:
        raise DependencyError(
            f"Không tìm thấy {name}. Hãy cài FFmpeg cho Windows, thêm thư mục bin vào PATH, "
            "mở terminal mới rồi chạy lại lệnh doctor."
        )
    return binary


def run_command(args: list[str], log_file: Path | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if log_file:
        with log_file.open("a", encoding="utf-8") as handle:
            handle.write("\n$ " + " ".join(args) + "\n")
            handle.write(result.stdout or "")
            handle.write(result.stderr or "")
    if result.returncode != 0:
        raise RuntimeError(f"Lệnh thất bại ({result.returncode}): {' '.join(args)}\n{result.stderr}")
    return result


def ffprobe_metadata_command(input_path: Path) -> list[str]:
    return [
        require_binary("ffprobe"),
        "-v",
        "error",
        "-show_format",
        "-show_streams",
        "-of",
        "json",
        str(input_path),
    ]


def extract_audio_command(input_path: Path, output_wav: Path) -> list[str]:
    return [
        require_binary("ffmpeg"),
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-f",
        "wav",
        str(output_wav),
    ]
