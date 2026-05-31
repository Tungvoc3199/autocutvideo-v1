from pathlib import Path

import pytest

from foreign_video_subtitle_tool.pipeline import run_pipeline
from foreign_video_subtitle_tool.models import ToolOptions
from foreign_video_subtitle_tool.state import COMPLETED, load_state, mark_stage, stage_complete


def test_stage_complete_requires_state_and_output(tmp_path: Path):
    state_path = tmp_path / "state.json"
    output = tmp_path / "output.txt"
    output.write_text("ok", encoding="utf-8")
    mark_stage(state_path, "demo", COMPLETED)
    assert stage_complete(load_state(state_path), "demo", [output])
    assert not stage_complete(load_state(state_path), "demo", [output], force=True)


def test_manual_mode_stops_before_render_when_vietnamese_missing(tmp_path: Path, monkeypatch):
    video = tmp_path / "input video.mp4"
    video.write_bytes(b"fake")

    def fake_metadata(input_path, paths):
        paths.input_metadata.write_text('{"source_path":"' + str(input_path) + '"}', encoding="utf-8")
        return {}

    def fake_extract(input_path, output_wav, log_file=None):
        output_wav.write_bytes(b"wav")
        return ["ffmpeg"]

    def fake_transcribe(audio_path, output_srt, **kwargs):
        output_srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello\n", encoding="utf-8")
        return []

    render_called = False

    def fake_render(*args, **kwargs):
        nonlocal render_called
        render_called = True

    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.write_input_metadata", fake_metadata)
    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.extract_audio", fake_extract)
    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.transcribe_audio", fake_transcribe)
    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.burn_subtitles", fake_render)

    paths = run_pipeline(ToolOptions(input_path=video, output_dir=tmp_path / "output", translation_mode="manual"))
    assert paths.original_srt.exists()
    assert paths.translate_prompt.exists()
    assert not paths.final_video.exists()
    assert not render_called
    state = load_state(paths.state)
    assert state["stages"]["translation"]["status"] == "pending"


def test_manual_resume_rejects_mismatched_vietnamese_srt_before_render(tmp_path: Path, monkeypatch):
    video = tmp_path / "input video.mp4"
    video.write_bytes(b"fake")

    def fake_metadata(input_path, paths):
        paths.input_metadata.write_text('{"source_path":"' + str(input_path) + '"}', encoding="utf-8")
        return {}

    def fake_extract(input_path, output_wav, log_file=None):
        output_wav.write_bytes(b"wav")
        return ["ffmpeg"]

    def fake_transcribe(audio_path, output_srt, **kwargs):
        output_srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello\n", encoding="utf-8")
        return []

    render_called = False

    def fake_render(*args, **kwargs):
        nonlocal render_called
        render_called = True

    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.write_input_metadata", fake_metadata)
    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.extract_audio", fake_extract)
    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.transcribe_audio", fake_transcribe)
    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.burn_subtitles", fake_render)

    paths = run_pipeline(ToolOptions(input_path=video, output_dir=tmp_path / "output", translation_mode="manual"))
    paths.vietnamese_srt.write_text("1\n00:00:00,200 --> 00:00:01,000\nXin chào\n", encoding="utf-8")

    with pytest.raises(ValueError):
        run_pipeline(ToolOptions(input_path=video, output_dir=tmp_path / "output", translation_mode="manual"))
    assert not render_called
