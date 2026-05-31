from pathlib import Path

from foreign_video_subtitle_tool.config import SubtitleStyle
from foreign_video_subtitle_tool.doctor import check_environment, format_doctor_report
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


def test_burn_subtitles_command_transcodes_mp4_audio_and_faststart(monkeypatch):
    monkeypatch.setattr("foreign_video_subtitle_tool.rendering.require_binary", lambda name: name)
    command = burn_subtitles_command(Path("input.webm"), Path("vi.srt"), Path("final.mp4"), SubtitleStyle())
    assert command[command.index("-c:a") + 1] == "aac"
    assert command[command.index("-b:a") + 1] == "192k"
    assert command[command.index("-movflags") + 1] == "+faststart"
    assert "copy" not in command


def test_escape_subtitle_path_for_filter_handles_apostrophe(monkeypatch):
    monkeypatch.setattr("foreign_video_subtitle_tool.rendering.require_binary", lambda name: name)
    command = burn_subtitles_command(
        Path("input.mp4"),
        Path(r"C:\Users\O'Connor\Job Folder\vietnamese.srt"),
        Path("final.mp4"),
        SubtitleStyle(),
    )
    vf = command[command.index("-vf") + 1]
    assert "O'\\''Connor" in vf


def test_doctor_report_marks_faster_whisper_required(monkeypatch):
    monkeypatch.setattr("foreign_video_subtitle_tool.doctor.find_binary", lambda name: f"C:/ffmpeg/bin/{name}.exe")
    monkeypatch.setattr(
        "foreign_video_subtitle_tool.doctor.importlib.util.find_spec",
        lambda name: None if name == "faster_whisper" else object(),
    )
    checks = check_environment()
    report = format_doctor_report(checks)
    assert any(check.name == "faster_whisper" and not check.ok for check in checks)
    assert "Lỗi bắt buộc" in report


def test_cli_doctor_exits_nonzero_without_required_faster_whisper(monkeypatch, capsys):
    from foreign_video_subtitle_tool.cli import main

    monkeypatch.setattr("foreign_video_subtitle_tool.doctor.find_binary", lambda name: f"C:/ffmpeg/bin/{name}.exe")
    monkeypatch.setattr(
        "foreign_video_subtitle_tool.doctor.importlib.util.find_spec",
        lambda name: None if name == "faster_whisper" else object(),
    )

    assert main(["doctor"]) == 2
    assert "faster_whisper" in capsys.readouterr().out
