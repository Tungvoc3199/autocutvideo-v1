import io
from pathlib import Path

from foreign_video_subtitle_tool.cli import configure_console_encoding
from foreign_video_subtitle_tool.config import SubtitleStyle
from foreign_video_subtitle_tool.doctor import CheckResult, check_environment, format_doctor_report
from foreign_video_subtitle_tool.ffmpeg_utils import extract_audio_command
from foreign_video_subtitle_tool.rendering import burn_subtitles_command, escape_subtitle_path_for_filter


def test_extract_audio_command_keeps_windows_paths_as_single_args(monkeypatch):
    monkeypatch.setattr("foreign_video_subtitle_tool.ffmpeg_utils.require_binary", lambda name: name)
    command = extract_audio_command(Path(r"C:\Users\Me\Input Videos\clip one.mp4"), Path(r"C:\Out Folder\audio.wav"))
    assert command[-1] == r"C:\Out Folder\audio.wav"
    assert r"C:\Users\Me\Input Videos\clip one.mp4" in command
    assert command[command.index("-ac") + 1] == "1"
    assert command[command.index("-ar") + 1] == "16000"


def test_burn_subtitles_command_contains_style_and_single_path_args(monkeypatch):
    monkeypatch.setattr("foreign_video_subtitle_tool.rendering.require_binary", lambda name: name)
    command = burn_subtitles_command(
        Path(r"C:\Input Videos\clip one.mp4"),
        Path(r"C:\Job Folder\vietnamese.srt"),
        Path(r"C:\Job Folder\final.mp4"),
        SubtitleStyle(font_name="Arial", margin_v=80),
    )
    assert command[0] == "ffmpeg"
    assert command[command.index("-i") + 1] == r"C:\Input Videos\clip one.mp4"
    vf = command[command.index("-vf") + 1]
    assert "subtitles=" in vf
    assert "MarginV=80" in vf
    assert command[-1] == r"C:\Job Folder\final.mp4"


def test_escape_subtitle_path_for_filter_windows_drive():
    escaped = escape_subtitle_path_for_filter(Path(r"C:\Job Folder\vietnamese.srt"))
    assert "C\\:" in escaped
    assert "/" in escaped


def test_doctor_behavior_with_mocked_binaries_and_packages(monkeypatch):
    monkeypatch.setattr("foreign_video_subtitle_tool.doctor.find_binary", lambda name: f"C:/ffmpeg/bin/{name}.exe")
    monkeypatch.setattr("foreign_video_subtitle_tool.doctor.importlib.util.find_spec", lambda name: object())
    checks = check_environment()
    assert all(check.ok for check in checks)
    report = format_doctor_report(checks)
    assert "[OK] ffmpeg" in report


def test_burn_subtitles_transcodes_audio_to_aac_for_mp4(monkeypatch):
    monkeypatch.setattr("foreign_video_subtitle_tool.rendering.require_binary", lambda name: name)
    command = burn_subtitles_command(Path("input.webm"), Path("vi.srt"), Path("final.mp4"), SubtitleStyle())
    assert command[command.index("-c:a") + 1] == "aac"
    assert command[command.index("-b:a") + 1] == "192k"
    assert command[command.index("-movflags") + 1] == "+faststart"


def test_doctor_requires_faster_whisper_for_success_exit_logic(monkeypatch):
    monkeypatch.setattr("foreign_video_subtitle_tool.doctor.find_binary", lambda name: f"C:/ffmpeg/bin/{name}.exe")
    monkeypatch.setattr(
        "foreign_video_subtitle_tool.doctor.importlib.util.find_spec",
        lambda name: None if name == "faster_whisper" else object(),
    )
    checks = check_environment()
    assert not next(check for check in checks if check.name == "faster_whisper").ok
    assert "faster_whisper" in format_doctor_report(checks)


def test_console_encoding_is_utf8_for_vietnamese_doctor_output():
    buffer = io.BytesIO()
    stream = io.TextIOWrapper(buffer, encoding="cp1252")
    configure_console_encoding(stream)
    stream.write(format_doctor_report([CheckResult("ffmpeg", False, "Không tìm thấy ffmpeg")]))
    stream.flush()
    assert stream.encoding == "utf-8"
    assert "Foreign Video →".encode() in buffer.getvalue()
