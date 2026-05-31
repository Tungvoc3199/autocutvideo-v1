from __future__ import annotations

import importlib
import importlib.util
import os
from pathlib import Path

from .models import SubtitleEntry
from .srt_utils import parse_srt, read_srt, serialize_srt, wrap_subtitle_text, write_srt

PROMPT_HEADER = """Bạn là biên dịch phụ đề chuyên nghiệp sang tiếng Việt.
Yêu cầu:
- Giữ nguyên số thứ tự và timestamp của SRT.
- Chỉ dịch nội dung thoại sang tiếng Việt tự nhiên, ngắn gọn.
- Không thêm giải thích ngoài SRT.
- Chia dòng dễ đọc, tối đa khoảng 2 dòng mỗi phụ đề.

Hãy dịch SRT sau:
"""


def create_translate_prompt(original_srt: Path, prompt_path: Path) -> None:
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(PROMPT_HEADER + "\n" + original_srt.read_text(encoding="utf-8"), encoding="utf-8")


def batch_entries(entries: list[SubtitleEntry], batch_size: int = 40) -> list[list[SubtitleEntry]]:
    return [entries[i : i + batch_size] for i in range(0, len(entries), batch_size)]


def validate_translation(original: list[SubtitleEntry], translated: list[SubtitleEntry]) -> None:
    if len(original) != len(translated):
        raise ValueError("Bản dịch không giữ nguyên số lượng subtitle.")
    for source, target in zip(original, translated, strict=True):
        if source.index != target.index or source.start != target.start or source.end != target.end:
            raise ValueError(f"Bản dịch không giữ nguyên index/timestamp tại subtitle #{source.index}.")
        if source.text.strip() and not target.text.strip():
            raise ValueError(f"Bản dịch thiếu nội dung tại subtitle #{source.index}.")


def normalize_translated_entries(entries: list[SubtitleEntry]) -> list[SubtitleEntry]:
    return [SubtitleEntry(e.index, e.start, e.end, wrap_subtitle_text(e.text)) for e in entries]


def validate_and_normalize_srt_files(original_srt: Path, translated_srt: Path) -> list[SubtitleEntry]:
    """Validate a user/API translation file and normalize subtitle line wrapping in place."""
    original_entries = read_srt(original_srt)
    translated_entries = read_srt(translated_srt)
    validate_translation(original_entries, translated_entries)
    normalized_entries = normalize_translated_entries(translated_entries)
    write_srt(translated_srt, normalized_entries)
    return normalized_entries


def load_dotenv_file(env_path: Path = Path(".env")) -> None:
    """Load simple KEY=VALUE pairs from .env without overriding existing variables."""
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def translate_openai(
    original_entries: list[SubtitleEntry], output_srt: Path, batch_size: int = 40
) -> list[SubtitleEntry]:
    load_dotenv_file()
    api_key = os.environ.get("OPENAI_API_KEY")
    model_name = os.environ.get("OPENAI_MODEL")
    if not api_key:
        raise RuntimeError("Thiếu OPENAI_API_KEY. Hãy thêm vào .env hoặc dùng --translation-mode manual.")
    if not model_name:
        raise RuntimeError("Thiếu OPENAI_MODEL. Hãy khai báo model trong biến môi trường OPENAI_MODEL.")
    if importlib.util.find_spec("openai") is None:
        raise RuntimeError("Chưa cài package openai. Chạy: python -m pip install -r requirements-subtitle-tool.txt")

    openai_module = importlib.import_module("openai")
    client = openai_module.OpenAI(api_key=api_key)
    translated_all: list[SubtitleEntry] = []
    for batch in batch_entries(original_entries, batch_size=batch_size):
        content = PROMPT_HEADER + "\n" + serialize_srt(batch)
        response = client.responses.create(
            model=model_name,
            input=[{"role": "user", "content": content}],
        )
        translated_text = getattr(response, "output_text", "")
        translated_batch = parse_srt(translated_text)
        validate_translation(batch, translated_batch)
        translated_all.extend(normalize_translated_entries(translated_batch))
    validate_translation(original_entries, translated_all)
    write_srt(output_srt, translated_all)
    return translated_all
