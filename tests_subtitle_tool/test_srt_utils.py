from foreign_video_subtitle_tool.models import SubtitleEntry
from foreign_video_subtitle_tool.srt_utils import parse_srt, seconds_to_srt_timestamp, serialize_srt, wrap_subtitle_text


def test_parse_and_serialize_srt_roundtrip():
    text = "1\n00:00:01,000 --> 00:00:03,500\nHello world\n\n2\n00:00:04,000 --> 00:00:05,000\nSecond line\n"
    entries = parse_srt(text)
    assert entries[0].index == 1
    assert entries[0].start == "00:00:01,000"
    assert entries[1].text == "Second line"
    assert serialize_srt(entries) == text


def test_timestamp_and_wrap():
    assert seconds_to_srt_timestamp(65.4321) == "00:01:05,432"
    wrapped = wrap_subtitle_text("Đây là một câu phụ đề tiếng Việt khá dài cần được chia dòng", width=30)
    assert "\n" in wrapped


def test_serialize_empty():
    assert serialize_srt([]) == ""
