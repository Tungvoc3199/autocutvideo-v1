import pytest

from foreign_video_subtitle_tool.models import SubtitleEntry
from foreign_video_subtitle_tool.translation import batch_entries, normalize_translated_entries, validate_translation


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
