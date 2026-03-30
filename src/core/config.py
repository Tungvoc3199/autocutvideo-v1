from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any



@dataclass
class ScoreWeights:
    sharpness: float = 0.08
    blur: float = 0.08
    flicker: float = 0.1
    motion_stability: float = 0.1
    duplication: float = 0.1
    exposure_stability: float = 0.08
    color_consistency: float = 0.08
    face_consistency: float = 0.1
    hand_artifact_risk: float = 0.07
    body_deformation_risk: float = 0.07
    object_warp_risk: float = 0.07
    lip_sync_risk: float = 0.04
    continuity_potential: float = 0.03


@dataclass
class AppConfig:
    min_segment_duration: float = 0.5
    analysis_window_sec: float = 1.0
    realism_threshold: float = 62.0
    critical_failure_threshold: float = 80.0
    trim_padding_ms: int = 120
    target_resolution: str = "1920x1080"
    target_fps: int = 30
    target_aspect_ratio: str = "16:9"
    transition_type: str = "auto"  # auto|hard|fade
    transition_duration: float = 0.2
    audio_normalization: bool = True
    max_workers: int = 4
    resume_from_log: bool = True
    review_queue_enabled: bool = True
    score_weights: ScoreWeights = field(default_factory=ScoreWeights)

    @classmethod
    def load(cls, path: str | Path | None) -> "AppConfig":
        if not path:
            return cls()
        try:
            import yaml
            data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        except ModuleNotFoundError as exc:
            raise RuntimeError("PyYAML is required to load YAML config files.") from exc
        weights_data = data.pop("weights", {})
        weights = ScoreWeights(**weights_data) if weights_data else ScoreWeights()
        return cls(**data, score_weights=weights)

    def to_dict(self) -> dict[str, Any]:
        return {
            "min_segment_duration": self.min_segment_duration,
            "analysis_window_sec": self.analysis_window_sec,
            "realism_threshold": self.realism_threshold,
            "critical_failure_threshold": self.critical_failure_threshold,
            "trim_padding_ms": self.trim_padding_ms,
            "target_resolution": self.target_resolution,
            "target_fps": self.target_fps,
            "target_aspect_ratio": self.target_aspect_ratio,
            "transition_type": self.transition_type,
            "transition_duration": self.transition_duration,
            "audio_normalization": self.audio_normalization,
            "max_workers": self.max_workers,
            "resume_from_log": self.resume_from_log,
            "review_queue_enabled": self.review_queue_enabled,
            "weights": self.score_weights.__dict__,
        }
