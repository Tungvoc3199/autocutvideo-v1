from __future__ import annotations

import importlib.util
from dataclasses import dataclass

from .ffmpeg_utils import find_binary


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def check_environment() -> list[CheckResult]:
    checks = []
    for binary in ("ffmpeg", "ffprobe"):
        path = find_binary(binary)
        checks.append(
            CheckResult(
                name=binary,
                ok=path is not None,
                detail=path or f"Không tìm thấy {binary}. Cài FFmpeg và thêm vào PATH.",
            )
        )
    for package in ("faster_whisper", "openai", "yaml"):
        found = importlib.util.find_spec(package) is not None
        checks.append(
            CheckResult(
                name=package,
                ok=found,
                detail="Đã cài" if found else "Chưa cài; xem requirements-subtitle-tool.txt",
            )
        )
    return checks


def format_doctor_report(checks: list[CheckResult]) -> str:
    lines = ["Foreign Video → Vietnamese Subtitle Tool doctor"]
    for check in checks:
        status = "OK" if check.ok else "FAIL"
        lines.append(f"[{status}] {check.name}: {check.detail}")
    required = {"ffmpeg", "ffprobe", "faster_whisper"}
    if not all(check.ok for check in checks if check.name in required):
        lines.append("Lỗi bắt buộc: FFmpeg/FFprobe/faster-whisper chưa sẵn sàng. Hãy cài trước khi chạy pipeline.")
    lines.append("Tuỳ chọn: openai chỉ cần cho OpenAI mode; PyYAML chỉ cần khi dùng --subtitle-style YAML.")
    return "\n".join(lines)
