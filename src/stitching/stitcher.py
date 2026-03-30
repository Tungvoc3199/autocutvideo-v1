from __future__ import annotations

from pathlib import Path

from src.core.config import AppConfig
from src.core.models import ClipDecision, SegmentAnalysis
from src.utils.ffmpeg_utils import concat_videos, extract_subclip, normalize_video


class Stitcher:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def stitch(self, decisions: list[ClipDecision], output_dir: str | Path) -> dict:
        out = Path(output_dir)
        tmp = out / "temp_segments"
        tmp.mkdir(parents=True, exist_ok=True)
        normalized_dir = out / "normalized"
        normalized_dir.mkdir(parents=True, exist_ok=True)

        segments = self._collect_segments(decisions)
        rendered_paths: list[Path] = []

        for idx, seg in enumerate(segments):
            clip_file = tmp / f"segment_{idx:04d}.mp4"
            normalized_file = normalized_dir / f"segment_{idx:04d}.mp4"
            extract_subclip(seg.segment.video_path, clip_file, seg.segment.start, seg.segment.end, reencode=True)
            normalize_video(
                clip_file,
                normalized_file,
                target_resolution=self.config.target_resolution,
                target_fps=self.config.target_fps,
                audio_norm=self.config.audio_normalization,
            )
            rendered_paths.append(normalized_file)

        concat_file = out / "concat_list.txt"
        concat_file.write_text(
            "\n".join([f"file '{p.as_posix()}'" for p in rendered_paths]), encoding="utf-8"
        )
        final_file = out / "final_video.mp4"
        if rendered_paths:
            concat_videos(concat_file, final_file)

        return {
            "final_video": str(final_file) if rendered_paths else "",
            "segments_used": len(rendered_paths),
        }

    def _collect_segments(self, decisions: list[ClipDecision]) -> list[SegmentAnalysis]:
        items: list[SegmentAnalysis] = []
        for d in decisions:
            if d.rejected:
                continue
            items.extend(d.kept_segments)
        items.sort(key=lambda x: (x.segment.video_path, x.segment.start))
        return items
