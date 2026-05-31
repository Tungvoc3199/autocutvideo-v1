import pytest

from foreign_video_subtitle_tool.models import SubtitleEntry
from foreign_video_subtitle_tool.translation import (
    batch_entries,
    normalize_translated_entries,
    validate_and_normalize_srt_files,
    validate_translation,
)


def test_batch_entries_preserves_order():
    entries = [SubtitleEntry(i, "00:00:00,000", "00:00:01,000", f"Text {i}") for i in range(1, 6)]
    batches = batch_entries(entries, batch_size=2)
    assert [[entry.index for entry in batch] for batch in batches] == [[1, 2], [3, 4], [5]]


def test_validate_translation_preserves_indices_and_timestamps():
    original = [SubtitleEntry(1, "00:00:00,000", "00:00:01,000", "Hello")]
    translated = [SubtitleEntry(1, "00:00:00,000", "00:00:01,000", "Xin chào")]
    validate_translation(original, translated)


def test_validate_translation_rejects_timestamp_change():
    original = [SubtitleEntry(1, "00:00:00,000", "00:00:01,000", "Hello")]
    translated = [SubtitleEntry(1, "00:00:00,100", "00:00:01,000", "Xin chào")]
    with pytest.raises(ValueError):
        validate_translation(original, translated)


def test_normalize_wraps_text_without_changing_timing():
    entry = SubtitleEntry(7, "00:00:00,000", "00:00:02,000", "Một câu rất dài cần được chia dòng để dễ đọc trên video ngắn")
    normalized = normalize_translated_entries([entry])[0]
    assert normalized.index == 7
    assert normalized.start == entry.start
    assert "\n" in normalized.text


def test_validate_and_normalize_srt_files_rewrites_wrapped_text(tmp_path):
    original_srt = tmp_path / "original.srt"
    translated_srt = tmp_path / "vietnamese.srt"
    original_srt.write_text("1\n00:00:00,000 --> 00:00:02,000\nHello world\n", encoding="utf-8")
    translated_srt.write_text(
        "```srt\n1\n00:00:00,000 --> 00:00:02,000\nMột câu phụ đề tiếng Việt rất dài cần được chia dòng để đọc rõ hơn trên video ngắn\n```",
        encoding="utf-8",
    )
    entries = validate_and_normalize_srt_files(original_srt, translated_srt)
    assert entries[0].index == 1
    assert entries[0].start == "00:00:00,000"
    assert "\n" in entries[0].text
    assert not translated_srt.read_text(encoding="utf-8").startswith("```")


def test_validate_and_normalize_srt_files_rejects_manual_timestamp_change(tmp_path):
    original_srt = tmp_path / "original.srt"
    translated_srt = tmp_path / "vietnamese.srt"
    original_srt.write_text("1\n00:00:00,000 --> 00:00:02,000\nHello\n", encoding="utf-8")
    translated_srt.write_text("1\n00:00:00,100 --> 00:00:02,000\nXin chào\n", encoding="utf-8")
    with pytest.raises(ValueError):
        validate_and_normalize_srt_files(original_srt, translated_srt)
