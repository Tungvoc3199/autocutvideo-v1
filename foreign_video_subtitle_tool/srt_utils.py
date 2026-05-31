from __future__ import annotations

import re
import textwrap
from pathlib import Path

from .models import SubtitleEntry

TIMESTAMP_RE = re.compile(r"^(\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2},\d{3})")


def parse_srt(text: str) -> list[SubtitleEntry]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []
    entries: list[SubtitleEntry] = []
    for block in re.split(r"\n{2,}", normalized):
        lines = [line.rstrip() for line in block.split("\n")]
        if len(lines) < 2:
            continue
        try:
            index = int(lines[0].strip())
        except ValueError as exc:
            raise ValueError(f"Khối SRT thiếu số thứ tự hợp lệ: {block[:80]}") from exc
        match = TIMESTAMP_RE.match(lines[1].strip())
        if not match:
            raise ValueError(f"Khối SRT #{index} thiếu timestamp hợp lệ")
        text_body = "\n".join(lines[2:]).strip()
        entries.append(SubtitleEntry(index=index, start=match.group(1), end=match.group(2), text=text_body))
    return entries


def serialize_srt(entries: list[SubtitleEntry]) -> str:
    blocks = []
    for entry in entries:
        text_body = entry.text.strip()
        blocks.append(f"{entry.index}\n{entry.start} --> {entry.end}\n{text_body}")
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def read_srt(path: Path) -> list[SubtitleEntry]:
    return parse_srt(path.read_text(encoding="utf-8-sig"))


def write_srt(path: Path, entries: list[SubtitleEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_srt(entries), encoding="utf-8")


def seconds_to_srt_timestamp(seconds: float) -> str:
    total_ms = max(0, int(round(seconds * 1000)))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, millis = divmod(rem, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def wrap_subtitle_text(text: str, width: int = 42, max_lines: int = 2) -> str:
    cleaned = " ".join(text.split())
    if not cleaned:
        return ""
    lines = textwrap.wrap(cleaned, width=width, break_long_words=False, break_on_hyphens=False)
    if len(lines) <= max_lines:
        return "\n".join(lines)
    merged = " ".join(lines[max_lines - 1 :])
    return "\n".join(lines[: max_lines - 1] + [merged])
