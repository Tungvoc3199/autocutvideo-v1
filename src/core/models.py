from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class VideoMetadata:
    path: str
    filename: str
    duration: float
    fps: float
    width: int
    height: int
    has_audio: bool

    @property
    def aspect_ratio(self) -> str:
        return f"{self.width}:{self.height}"


@dataclass
class Segment:
    video_path: str
    start: float
    end: float
    scene_id: int

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass
class SegmentAnalysis:
    segment: Segment
    metrics: dict[str, float]
    risks: dict[str, float]
    realism_score: float
    confidence: float
    critical_failures: list[str] = field(default_factory=list)
    needs_review: bool = False

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["segment"] = asdict(self.segment)
        return out


@dataclass
class ClipDecision:
    video_path: str
    kept_segments: list[SegmentAnalysis]
    rejected_segments: list[SegmentAnalysis]
    rejected: bool = False
    reasons: list[str] = field(default_factory=list)


@dataclass
class PipelineState:
    base_output: Path
    scan_file: Path
    analysis_file: Path
    decisions_file: Path

    @classmethod
    def for_output(cls, out_dir: str | Path) -> "PipelineState":
        base = Path(out_dir)
        return cls(
            base_output=base,
            scan_file=base / "scan_metadata.json",
            analysis_file=base / "analysis_results.json",
            decisions_file=base / "edit_decisions.json",
        )
