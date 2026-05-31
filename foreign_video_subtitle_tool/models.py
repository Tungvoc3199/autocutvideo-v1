from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class SubtitleEntry:
    index: int
    start: str
    end: str
    text: str


@dataclass(slots=True)
class ToolOptions:
    input_path: Path | None = None
    output_dir: Path = Path("output")
    translation_mode: str = "manual"
    language: str = "auto"
    model_size: str = "small"
    device: str = "auto"
    compute_type: str = "auto"
    subtitle_style: Path | None = None
    force: bool = False
    skip_burn: bool = False


@dataclass(slots=True)
class JobPaths:
    job_dir: Path
    input_metadata: Path
    audio: Path
    original_srt: Path
    translate_prompt: Path
    vietnamese_srt: Path
    final_video: Path
    report: Path
    state: Path
    logs_dir: Path
    run_log: Path

    @classmethod
    def from_job_dir(cls, job_dir: Path) -> "JobPaths":
        return cls(
            job_dir=job_dir,
            input_metadata=job_dir / "input_metadata.json",
            audio=job_dir / "audio.wav",
            original_srt=job_dir / "original.srt",
            translate_prompt=job_dir / "translate_prompt.txt",
            vietnamese_srt=job_dir / "vietnamese.srt",
            final_video=job_dir / "final_vi_sub.mp4",
            report=job_dir / "report.json",
            state=job_dir / "state.json",
            logs_dir=job_dir / "logs",
            run_log=job_dir / "logs" / "run.log",
        )


@dataclass(slots=True)
class StageResult:
    name: str
    status: str
    detail: str = ""
    data: dict[str, Any] = field(default_factory=dict)
