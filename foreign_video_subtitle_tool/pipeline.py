from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .audio import extract_audio
from .config import SUPPORTED_VIDEO_EXTENSIONS
from .ffmpeg_utils import ffprobe_metadata_command, run_command
from .logging_utils import configure_job_logger
from .models import JobPaths, ToolOptions
from .rendering import burn_subtitles
from .srt_utils import read_srt
from .state import COMPLETED, FAILED, PENDING, file_ready, load_state, mark_stage, save_state, stage_complete
from .transcription import transcribe_audio
from .translation import create_translate_prompt, translate_openai, validate_and_normalize_srt_files

STAGES = ["metadata", "audio", "transcription", "prompt", "translation", "render", "report"]


@dataclass(frozen=True, slots=True)
class InputFingerprint:
    resolved_path: str
    size_bytes: int
    mtime_ns: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "resolved_path": self.resolved_path,
            "size_bytes": self.size_bytes,
            "mtime_ns": self.mtime_ns,
        }


@dataclass(frozen=True, slots=True)
class BatchItemResult:
    input_path: Path
    job_dir: Path | None
    status: str
    error: str = ""


@dataclass(frozen=True, slots=True)
class BatchRunResult:
    items: list[BatchItemResult]

    @property
    def succeeded(self) -> list[BatchItemResult]:
        return [item for item in self.items if item.status == "success"]

    @property
    def failed(self) -> list[BatchItemResult]:
        return [item for item in self.items if item.status == "failed"]

    @property
    def skipped(self) -> list[BatchItemResult]:
        return [item for item in self.items if item.status == "skipped"]

    @property
    def jobs(self) -> list[JobPaths]:
        return [JobPaths.from_job_dir(item.job_dir) for item in self.items if item.job_dir is not None]

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.jobs)

    @property
    def has_failures(self) -> bool:
        return bool(self.failed)


def input_fingerprint(input_path: Path) -> InputFingerprint:
    resolved = input_path.resolve()
    stat = resolved.stat()
    return InputFingerprint(str(resolved), stat.st_size, stat.st_mtime_ns)


def make_job_id(input_path: Path) -> str:
    fingerprint = input_fingerprint(input_path)
    digest = hashlib.sha1(json.dumps(fingerprint.to_dict(), sort_keys=True).encode("utf-8")).hexdigest()[:8]
    stem = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in input_path.stem).strip("_") or "video"
    return f"{stem}_{digest}"


def ensure_video_input(input_path: Path) -> None:
    if not input_path.exists() or not input_path.is_file():
        raise FileNotFoundError(f"Không tìm thấy video đầu vào: {input_path}")
    if input_path.suffix.lower() not in SUPPORTED_VIDEO_EXTENSIONS:
        raise ValueError(f"Định dạng video chưa hỗ trợ: {input_path.suffix}")


def init_job(input_path: Path, output_dir: Path) -> JobPaths:
    job_dir = output_dir / make_job_id(input_path)
    paths = JobPaths.from_job_dir(job_dir)
    paths.logs_dir.mkdir(parents=True, exist_ok=True)
    return paths


def write_input_metadata(input_path: Path, paths: JobPaths) -> dict[str, Any]:
    command = ffprobe_metadata_command(input_path)
    result = run_command(command, log_file=paths.run_log)
    metadata = json.loads(result.stdout or "{}")
    metadata["source_path"] = str(input_path.resolve())
    metadata["input_fingerprint"] = input_fingerprint(input_path).to_dict()
    metadata["captured_at"] = datetime.now(timezone.utc).isoformat()
    paths.input_metadata.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return metadata


def _report_payload(paths: JobPaths, options: ToolOptions, status: str, message: str) -> dict[str, Any]:
    state = load_state(paths.state)
    return {
        "status": status,
        "message": message,
        "job_dir": str(paths.job_dir),
        "translation_mode": options.translation_mode,
        "skip_burn": options.skip_burn,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "outputs": {
            "original_srt": str(paths.original_srt) if file_ready(paths.original_srt) else None,
            "translate_prompt": str(paths.translate_prompt) if file_ready(paths.translate_prompt) else None,
            "vietnamese_srt": str(paths.vietnamese_srt) if file_ready(paths.vietnamese_srt) else None,
            "final_video": str(paths.final_video) if file_ready(paths.final_video) else None,
        },
        "state": state,
        "rollback": "Xóa thư mục job output tương ứng để rollback output; code nằm trong branch riêng.",
    }


def write_report(paths: JobPaths, options: ToolOptions, status: str, message: str) -> None:
    paths.report.write_text(json.dumps(_report_payload(paths, options, status, message), ensure_ascii=False, indent=2), encoding="utf-8")
    mark_stage(paths.state, "report", COMPLETED, status)


def write_failure_report(paths: JobPaths, options: ToolOptions, stage: str, exc: Exception) -> None:
    error_message = str(exc) or exc.__class__.__name__
    mark_stage(
        paths.state,
        stage,
        FAILED,
        error_message,
        {"error_type": exc.__class__.__name__, "failed_at": datetime.now(timezone.utc).isoformat()},
    )
    report = _report_payload(paths, options, "failed", f"Stage {stage} thất bại: {error_message}")
    report["failed_stage"] = stage
    report["error"] = {"type": exc.__class__.__name__, "message": error_message}
    paths.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def run_pipeline(options: ToolOptions) -> JobPaths:
    if options.input_path is None:
        raise ValueError("Thiếu --input")
    input_path = options.input_path
    ensure_video_input(input_path)
    paths = init_job(input_path, options.output_dir)
    logger = configure_job_logger(paths.run_log)
    logger.info("Bắt đầu job %s", paths.job_dir)
    paths.job_dir.mkdir(parents=True, exist_ok=True)
    state = load_state(paths.state)
    save_state(paths.state, state)
    current_stage = "metadata"

    try:
        if not stage_complete(state, "metadata", [paths.input_metadata], options.force):
            write_input_metadata(input_path, paths)
            mark_stage(paths.state, "metadata", COMPLETED)
        else:
            logger.info("Bỏ qua metadata vì đã hoàn tất")

        current_stage = "audio"
        state = load_state(paths.state)
        if not stage_complete(state, "audio", [paths.audio], options.force):
            extract_audio(input_path, paths.audio, log_file=paths.run_log)
            mark_stage(paths.state, "audio", COMPLETED)
        else:
            logger.info("Bỏ qua audio vì đã hoàn tất")

        current_stage = "transcription"
        state = load_state(paths.state)
        if not stage_complete(state, "transcription", [paths.original_srt], options.force):
            transcribe_audio(
                paths.audio,
                paths.original_srt,
                language=options.language,
                model_size=options.model_size,
                device=options.device,
                compute_type=options.compute_type,
            )
            mark_stage(paths.state, "transcription", COMPLETED)
        else:
            logger.info("Bỏ qua transcription vì đã hoàn tất")

        current_stage = "prompt"
        state = load_state(paths.state)
        if not stage_complete(state, "prompt", [paths.translate_prompt], options.force):
            create_translate_prompt(paths.original_srt, paths.translate_prompt)
            mark_stage(paths.state, "prompt", COMPLETED)

        current_stage = "translation"
        if options.translation_mode == "openai":
            state = load_state(paths.state)
            if not stage_complete(state, "translation", [paths.vietnamese_srt], options.force):
                translate_openai(read_srt(paths.original_srt), paths.vietnamese_srt)
                mark_stage(paths.state, "translation", COMPLETED)
        elif file_ready(paths.vietnamese_srt):
            validate_and_normalize_srt_files(paths.original_srt, paths.vietnamese_srt)
            mark_stage(paths.state, "translation", COMPLETED, "Đã xác thực vietnamese.srt thủ công")
        else:
            mark_stage(paths.state, "translation", PENDING, "Chờ người dùng thêm vietnamese.srt rồi chạy resume")
            write_report(paths, options, "waiting_for_manual_translation", "Đã tạo original.srt và translate_prompt.txt")
            logger.info("Dừng manual mode để chờ vietnamese.srt")
            return paths

        validate_and_normalize_srt_files(paths.original_srt, paths.vietnamese_srt)

        current_stage = "render"
        if options.skip_burn:
            mark_stage(paths.state, "render", COMPLETED, "Người dùng chọn --skip-burn")
            write_report(paths, options, "completed_without_burn", "Đã bỏ qua bước burn subtitle")
            return paths

        state = load_state(paths.state)
        if not stage_complete(state, "render", [paths.final_video], options.force):
            burn_subtitles(input_path, paths.vietnamese_srt, paths.final_video, options.subtitle_style, paths.run_log)
            mark_stage(paths.state, "render", COMPLETED)
        else:
            logger.info("Bỏ qua render vì đã hoàn tất")

        current_stage = "report"
        write_report(paths, options, "completed", "Hoàn tất video có phụ đề Việt")
        return paths
    except Exception as exc:
        logger.exception("Stage %s thất bại", current_stage)
        write_failure_report(paths, options, current_stage, exc)
        raise


def resume_job(job_dir: Path, options: ToolOptions) -> JobPaths:
    paths = JobPaths.from_job_dir(job_dir)
    if not paths.input_metadata.exists():
        raise FileNotFoundError(f"Job không có input_metadata.json: {job_dir}")
    metadata = json.loads(paths.input_metadata.read_text(encoding="utf-8"))
    source_path = Path(metadata.get("source_path", ""))
    if not source_path.exists():
        raise FileNotFoundError(f"Không tìm thấy video gốc để resume: {source_path}")
    resume_options = ToolOptions(
        input_path=source_path,
        output_dir=job_dir.parent,
        translation_mode=options.translation_mode,
        language=options.language,
        model_size=options.model_size,
        device=options.device,
        compute_type=options.compute_type,
        subtitle_style=options.subtitle_style,
        force=options.force,
        skip_burn=options.skip_burn,
    )
    return run_pipeline(resume_options)


def batch_run(input_dir: Path, options: ToolOptions) -> BatchRunResult:
    if not input_dir.exists() or not input_dir.is_dir():
        raise NotADirectoryError(f"Không tìm thấy input-dir: {input_dir}")
    items: list[BatchItemResult] = []
    for input_path in sorted(input_dir.iterdir()):
        if not input_path.is_file() or input_path.suffix.lower() not in SUPPORTED_VIDEO_EXTENSIONS:
            continue
        job_dir: Path | None = None
        try:
            job_options = replace(options, input_path=input_path)
            paths = run_pipeline(job_options)
            job_dir = paths.job_dir
            items.append(BatchItemResult(input_path=input_path, job_dir=job_dir, status="success"))
        except Exception as exc:  # continue processing remaining files in a mixed batch
            try:
                job_dir = init_job(input_path, options.output_dir).job_dir
            except Exception:
                job_dir = None
            items.append(BatchItemResult(input_path=input_path, job_dir=job_dir, status="failed", error=str(exc)))
    return BatchRunResult(items)


def copy_manual_vietnamese_srt(job_dir: Path, source_srt: Path) -> Path:
    paths = JobPaths.from_job_dir(job_dir)
    shutil.copyfile(source_srt, paths.vietnamese_srt)
    return paths.vietnamese_srt
