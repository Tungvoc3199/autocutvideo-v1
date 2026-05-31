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


def test_job_id_changes_when_file_at_same_path_changes(tmp_path: Path):
    from foreign_video_subtitle_tool.pipeline import make_job_id

    video = tmp_path / "video.mp4"
    video.write_bytes(b"first")
    first_job_id = make_job_id(video)
    video.write_bytes(b"second content")
    second_job_id = make_job_id(video)
    assert first_job_id != second_job_id


def test_pipeline_marks_failed_stage_and_report(tmp_path: Path, monkeypatch):
    import json

    video = tmp_path / "input.mp4"
    video.write_bytes(b"fake")

    def fake_metadata(input_path, paths):
        paths.input_metadata.write_text('{"source_path":"' + str(input_path) + '"}', encoding="utf-8")
        return {}

    def failing_extract(*args, **kwargs):
        raise RuntimeError("ffmpeg exploded")

    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.write_input_metadata", fake_metadata)
    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.extract_audio", failing_extract)

    with pytest.raises(RuntimeError, match="ffmpeg exploded"):
        run_pipeline(ToolOptions(input_path=video, output_dir=tmp_path / "output", translation_mode="manual"))

    from foreign_video_subtitle_tool.pipeline import init_job

    paths = init_job(video, tmp_path / "output")
    state = load_state(paths.state)
    assert state["stages"]["audio"]["status"] == "failed"
    report = json.loads(paths.report.read_text(encoding="utf-8"))
    assert report["status"] == "failed"
    assert report["error"]["stage"] == "audio"
    assert "ffmpeg exploded" in report["error"]["message"]


def test_batch_run_continues_after_per_job_failure(tmp_path: Path, monkeypatch):
    from foreign_video_subtitle_tool.pipeline import batch_run

    input_dir = tmp_path / "input"
    input_dir.mkdir()
    bad = input_dir / "bad.mp4"
    good = input_dir / "good.mp4"
    bad.write_bytes(b"bad")
    good.write_bytes(b"good")

    def fake_run_pipeline(options):
        if options.input_path == bad:
            raise RuntimeError("bad video")
        from foreign_video_subtitle_tool.pipeline import init_job

        paths = init_job(options.input_path, options.output_dir)
        paths.job_dir.mkdir(parents=True, exist_ok=True)
        return paths

    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.run_pipeline", fake_run_pipeline)

    summary = batch_run(input_dir, ToolOptions(output_dir=tmp_path / "output"))

    assert len(summary.results) == 2
    assert len(summary.failed) == 1
    assert len(summary.succeeded) == 1
    assert summary.has_failures
    assert summary.results[0].status == "failed"
    assert summary.results[1].status == "success"
