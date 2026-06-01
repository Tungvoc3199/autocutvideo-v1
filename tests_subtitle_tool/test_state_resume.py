import json
import os
from pathlib import Path

import pytest

from foreign_video_subtitle_tool.pipeline import input_fingerprint, resume_job, run_pipeline, validate_resume_source
from foreign_video_subtitle_tool.models import ToolOptions
from foreign_video_subtitle_tool.state import COMPLETED, load_state, mark_stage, stage_complete


def write_fake_metadata(input_path, paths, fingerprint=None):
    fingerprint = fingerprint or input_fingerprint(input_path)
    paths.input_metadata.write_text(
        json.dumps({"source_path": str(input_path), "input_fingerprint": fingerprint.to_dict()}),
        encoding="utf-8",
    )
    return {}


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

    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.write_input_metadata", write_fake_metadata)
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

    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.write_input_metadata", write_fake_metadata)
    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.extract_audio", fake_extract)
    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.transcribe_audio", fake_transcribe)
    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.burn_subtitles", fake_render)

    paths = run_pipeline(ToolOptions(input_path=video, output_dir=tmp_path / "output", translation_mode="manual"))
    paths.vietnamese_srt.write_text("1\n00:00:00,200 --> 00:00:01,000\nXin chào\n", encoding="utf-8")

    with pytest.raises(ValueError):
        run_pipeline(ToolOptions(input_path=video, output_dir=tmp_path / "output", translation_mode="manual"))
    assert not render_called


def test_job_id_changes_when_same_path_file_content_fingerprint_changes(tmp_path: Path):
    from foreign_video_subtitle_tool.pipeline import make_job_id

    video = tmp_path / "same.mp4"
    video.write_bytes(b"first")
    first_id = make_job_id(video)
    video.write_bytes(b"second larger")
    second_id = make_job_id(video)
    assert first_id != second_id


def test_job_id_does_not_change_when_only_mtime_changes(tmp_path: Path):
    from foreign_video_subtitle_tool.pipeline import make_job_id

    video = tmp_path / "same.mp4"
    video.write_bytes(b"same content")
    first_id = make_job_id(video)
    stat = video.stat()
    os.utime(video, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
    assert make_job_id(video) == first_id


def test_manual_resume_uses_requested_job_after_mtime_change(tmp_path: Path, monkeypatch):
    video = tmp_path / "input video.mp4"
    video.write_bytes(b"fake")

    def fake_extract(input_path, output_wav, log_file=None):
        output_wav.write_bytes(b"wav")
        return ["ffmpeg"]

    def fake_transcribe(audio_path, output_srt, **kwargs):
        output_srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello\n", encoding="utf-8")
        return []

    def fake_render(input_path, vietnamese_srt, final_video, *args):
        final_video.write_bytes(b"rendered")

    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.write_input_metadata", write_fake_metadata)
    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.extract_audio", fake_extract)
    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.transcribe_audio", fake_transcribe)
    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.burn_subtitles", fake_render)

    paths = run_pipeline(ToolOptions(input_path=video, output_dir=tmp_path / "output", translation_mode="manual"))
    paths.vietnamese_srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nXin chào\n", encoding="utf-8")
    stat = video.stat()
    os.utime(video, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))

    resumed_paths = resume_job(paths.job_dir, ToolOptions(translation_mode="manual"))
    assert resumed_paths.job_dir == paths.job_dir
    assert paths.final_video.read_bytes() == b"rendered"
    assert len(list((tmp_path / "output").iterdir())) == 1


def test_manual_resume_rejects_changed_source_content(tmp_path: Path, monkeypatch):
    video = tmp_path / "input.mp4"
    video.write_bytes(b"original")

    def fake_extract(input_path, output_wav, log_file=None):
        output_wav.write_bytes(b"wav")
        return ["ffmpeg"]

    def fake_transcribe(audio_path, output_srt, **kwargs):
        output_srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello\n", encoding="utf-8")
        return []

    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.write_input_metadata", write_fake_metadata)
    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.extract_audio", fake_extract)
    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.transcribe_audio", fake_transcribe)

    paths = run_pipeline(ToolOptions(input_path=video, output_dir=tmp_path / "output", translation_mode="manual"))
    paths.vietnamese_srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nXin chào\n", encoding="utf-8")
    video.write_bytes(b"replaced content")

    with pytest.raises(ValueError, match="Video gốc đã thay đổi nội dung"):
        resume_job(paths.job_dir, ToolOptions(translation_mode="manual"))


def test_validate_resume_source_rejects_legacy_metadata_without_content_sha256(tmp_path: Path):
    video = tmp_path / "input.mp4"
    video.write_bytes(b"original")
    legacy_metadata = {
        "input_fingerprint": {
            "resolved_path": str(video.resolve()),
            "size_bytes": video.stat().st_size,
            "mtime_ns": video.stat().st_mtime_ns,
        }
    }

    with pytest.raises(ValueError, match=r"thiếu input_fingerprint\.content_sha256.*chạy lệnh run mới"):
        validate_resume_source(legacy_metadata, video)


def test_failed_stage_is_persisted_to_state_and_report(tmp_path: Path, monkeypatch):
    video = tmp_path / "input.mp4"
    video.write_bytes(b"fake")

    def fail_extract(input_path, output_wav, log_file=None):
        raise RuntimeError("ffmpeg failed")

    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.write_input_metadata", write_fake_metadata)
    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.extract_audio", fail_extract)

    with pytest.raises(RuntimeError, match="ffmpeg failed"):
        run_pipeline(ToolOptions(input_path=video, output_dir=tmp_path / "output"))

    paths = next((tmp_path / "output").iterdir())
    state = load_state(paths / "state.json")
    assert state["stages"]["audio"]["status"] == "failed"
    assert "ffmpeg failed" in state["stages"]["audio"]["detail"]
    report = (paths / "report.json").read_text(encoding="utf-8")
    assert '"status": "failed"' in report
    assert '"failed_stage": "audio"' in report


def test_batch_continues_after_one_job_fails(tmp_path: Path, monkeypatch):
    from foreign_video_subtitle_tool.pipeline import batch_run

    good = tmp_path / "good.mp4"
    bad = tmp_path / "bad.mp4"
    good.write_bytes(b"good")
    bad.write_bytes(b"bad")

    def fake_run_pipeline(options):
        if options.input_path == bad:
            raise RuntimeError("bad video")
        job_dir = options.output_dir / "good_job"
        job_dir.mkdir(parents=True, exist_ok=True)
        return type("Paths", (), {"job_dir": job_dir})()

    monkeypatch.setattr("foreign_video_subtitle_tool.pipeline.run_pipeline", fake_run_pipeline)
    result = batch_run(tmp_path, ToolOptions(output_dir=tmp_path / "output"))
    assert len(result.succeeded) == 1
    assert len(result.failed) == 1
    assert result.has_failures
    assert result.failed[0].input_path == bad


def test_batch_jobs_and_iteration_exclude_failed_jobs(tmp_path: Path):
    from foreign_video_subtitle_tool.pipeline import BatchItemResult, BatchRunResult

    successful_job = tmp_path / "successful_job"
    failed_job = tmp_path / "failed_job"
    result = BatchRunResult(
        [
            BatchItemResult(tmp_path / "good.mp4", successful_job, "success"),
            BatchItemResult(tmp_path / "bad.mp4", failed_job, "failed", "bad video"),
            BatchItemResult(tmp_path / "missing-job-dir.mp4", None, "success"),
        ]
    )

    assert [job.job_dir for job in result.jobs] == [successful_job]
    assert [job.job_dir for job in list(result)] == [successful_job]
