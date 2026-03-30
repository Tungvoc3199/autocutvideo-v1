from __future__ import annotations

import argparse
from pathlib import Path

from src.core.config import AppConfig
from src.core.pipeline import VideoRealityPipeline


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="video_reality_editor")
    parser.add_argument("command", choices=["scan", "analyze", "stitch", "run-all", "resume", "demo"])
    parser.add_argument("--input", default="./input_videos")
    parser.add_argument("--output", default="./output")
    parser.add_argument("--analysis", default="./output")
    parser.add_argument("--config", default="./config.example.yaml")
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    config = AppConfig.load(args.config)
    pipeline = VideoRealityPipeline(config=config, output_dir=args.output)

    if args.command == "scan":
        pipeline.scan(args.input)
    elif args.command == "analyze":
        pipeline.analyze(args.input, resume=False)
    elif args.command == "stitch":
        pipeline.stitch(args.analysis)
    elif args.command == "run-all":
        pipeline.run_all(args.input, resume=False)
    elif args.command == "resume":
        pipeline.run_all(args.input, resume=True)
    elif args.command == "demo":
        _run_demo(pipeline)


def _run_demo(pipeline: VideoRealityPipeline) -> None:
    demo_output = Path(pipeline.state.base_output)
    print(
        "Demo mode ready. Place sample clips in ./input_videos and run:\n"
        "python main.py run-all --input ./input_videos --output ./output --config ./config.example.yaml"
    )
    print(f"Configured output path: {demo_output.resolve()}")
