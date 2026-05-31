from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import DEFAULT_OUTPUT_DIR
from .doctor import REQUIRED_CHECKS, check_environment, format_doctor_report
from .models import ToolOptions
from .pipeline import batch_run, resume_job, run_pipeline


def add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--translation-mode", choices=["manual", "openai"], default="manual")
    parser.add_argument("--language", default="auto")
    parser.add_argument("--model-size", choices=["small", "medium", "large-v3"], default="small")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--compute-type", choices=["auto", "int8", "float16"], default="auto")
    parser.add_argument("--subtitle-style", type=Path)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--skip-burn", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m foreign_video_subtitle_tool.cli",
        description="Tạo phụ đề tiếng Việt cho video nước ngoài trên Windows 11.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="Kiểm tra FFmpeg/FFprobe và dependency Python.")

    run_parser = subparsers.add_parser("run", help="Chạy pipeline cho một video.")
    run_parser.add_argument("--input", required=True, type=Path)
    add_common_options(run_parser)

    resume_parser = subparsers.add_parser("resume", help="Tiếp tục job đã tạo.")
    resume_parser.add_argument("--job", required=True, type=Path)
    add_common_options(resume_parser)

    batch_parser = subparsers.add_parser("batch", help="Chạy nhiều video trong một folder.")
    batch_parser.add_argument("--input-dir", required=True, type=Path)
    add_common_options(batch_parser)
    return parser


def options_from_args(args: argparse.Namespace, input_path: Path | None = None) -> ToolOptions:
    return ToolOptions(
        input_path=input_path,
        output_dir=args.output_dir,
        translation_mode=args.translation_mode,
        language=args.language,
        model_size=args.model_size,
        device=args.device,
        compute_type=args.compute_type,
        subtitle_style=args.subtitle_style,
        force=args.force,
        skip_burn=args.skip_burn,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "doctor":
        checks = check_environment()
        print(format_doctor_report(checks))
        return 0 if all(check.ok for check in checks if check.name in REQUIRED_CHECKS) else 2
    try:
        if args.command == "run":
            paths = run_pipeline(options_from_args(args, input_path=args.input))
            print(f"Job: {paths.job_dir}")
            print(f"State: {paths.state}")
            return 0
        if args.command == "resume":
            paths = resume_job(args.job, options_from_args(args))
            print(f"Job: {paths.job_dir}")
            print(f"State: {paths.state}")
            return 0
        if args.command == "batch":
            result = batch_run(args.input_dir, options_from_args(args))
            print(
                f"Batch summary: success={len(result.succeeded)} "
                f"failed={len(result.failed)} skipped={len(result.skipped)} total={len(result)}"
            )
            for item in result.items:
                suffix = f" -> {item.job_dir}" if item.job_dir else ""
                error = f" | Lỗi: {item.error}" if item.error else ""
                print(f"[{item.status}] {item.input_path}{suffix}{error}")
            return 1 if result.has_failures else 0
    except Exception as exc:  # user-facing CLI boundary, not import handling
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1
    parser.error("Lệnh không hợp lệ")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
