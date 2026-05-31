from __future__ import annotations

import importlib.util
from dataclasses import dataclass

from .ffmpeg_utils import find_binary

REQUIRED_CHECKS = {"ffmpeg", "ffprobe", "faster_whisper"}
OPTIONAL_CHECKS = {"openai", "yaml"}


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
    missing_required = [check.name for check in checks if check.name in REQUIRED_CHECKS and not check.ok]
    if missing_required:
        lines.append("Lỗi bắt buộc: thiếu " + ", ".join(missing_required) + ". Hãy cài trước khi chạy pipeline.")
    missing_optional = [check.name for check in checks if check.name in OPTIONAL_CHECKS and not check.ok]
    if missing_optional:
        lines.append("Tùy chọn: " + ", ".join(missing_optional) + " chỉ cần khi dùng OpenAI/style YAML.")
    return "\n".join(lines)
