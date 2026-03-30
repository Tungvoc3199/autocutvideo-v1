from __future__ import annotations

from pathlib import Path

from src.analysis.metrics import SegmentAnalyzer
from src.analysis.scene_detect import detect_scene_cuts
from src.analysis.segmentation import merge_scene_boundaries, split_fixed_windows
from src.core.config import AppConfig
from src.core.decision import build_decisions
from src.core.models import PipelineState, SegmentAnalysis
from src.core.reporting import write_reports
from src.io.files import load_json, save_json
from src.io.ingest import discover_videos, read_video_metadata
from src.scoring.scorer import RealismScorer
from src.stitching.stitcher import Stitcher
from src.utils.ffmpeg_utils import ensure_ffmpeg
from src.utils.logger import setup_logger


class VideoRealityPipeline:
    def __init__(self, config: AppConfig, output_dir: str | Path) -> None:
        self.config = config
        self.state = PipelineState.for_output(output_dir)
        self.logger = setup_logger(Path(output_dir))

    def scan(self, input_dir: str | Path) -> list[dict]:
        ensure_ffmpeg()
        videos = discover_videos(input_dir)
        metadata = [read_video_metadata(v).__dict__ for v in videos]
        save_json(metadata, self.state.scan_file)
        self.logger.info("Scanned %s videos", len(metadata))
        return metadata

    def analyze(self, input_dir: str | Path, resume: bool = False) -> list[SegmentAnalysis]:
        ensure_ffmpeg()
        if resume and self.state.analysis_file.exists():
            self.logger.info("Resuming analysis from cache: %s", self.state.analysis_file)
            cached = load_json(self.state.analysis_file)
            return [self._analysis_from_dict(x) for x in cached]

        metadata = self.scan(input_dir) if not self.state.scan_file.exists() else load_json(self.state.scan_file)
        analyzer = SegmentAnalyzer()
        scorer = RealismScorer(self.config)
        results: list[SegmentAnalysis] = []

        for meta_dict in metadata:
            from src.core.models import VideoMetadata

            meta = VideoMetadata(**meta_dict)
            base_segments = split_fixed_windows(meta, self.config.analysis_window_sec)
            scene_cuts = detect_scene_cuts(meta.path)
            segments = merge_scene_boundaries(base_segments, scene_cuts)

            for seg in segments:
                if seg.duration < self.config.min_segment_duration:
                    continue
                metrics = analyzer.analyze(seg)
                score, conf, risks, critical, needs_review = scorer.compute(metrics)
                results.append(
                    SegmentAnalysis(
                        segment=seg,
                        metrics=metrics,
                        risks=risks,
                        realism_score=score,
                        confidence=conf,
                        critical_failures=critical,
                        needs_review=needs_review,
                    )
                )

        save_json([r.to_dict() for r in results], self.state.analysis_file)
        self.logger.info("Analyzed %s segments", len(results))
        return results

    def stitch(self, analysis_dir: str | Path) -> dict:
        analysis_path = Path(analysis_dir) / "analysis_results.json"
        data = load_json(analysis_path)
        analyses = [self._analysis_from_dict(x) for x in data]
        decisions = build_decisions(analyses, self.config)
        save_json(
            [
                {
                    "video_path": d.video_path,
                    "rejected": d.rejected,
                    "reasons": d.reasons,
                    "kept_segments": [k.to_dict() for k in d.kept_segments],
                    "rejected_segments": [r.to_dict() for r in d.rejected_segments],
                }
                for d in decisions
            ],
            self.state.decisions_file,
        )

        stitcher = Stitcher(self.config)
        result = stitcher.stitch(decisions, self.state.base_output)
        write_reports(analyses, decisions, result, self.state.base_output)
        self.logger.info("Stitch complete: %s", result.get("final_video"))
        return result

    def run_all(self, input_dir: str | Path, resume: bool = False) -> dict:
        analyses = self.analyze(input_dir, resume=resume)
        decisions = build_decisions(analyses, self.config)
        save_json(
            [
                {
                    "video_path": d.video_path,
                    "rejected": d.rejected,
                    "reasons": d.reasons,
                    "kept_segments": [k.to_dict() for k in d.kept_segments],
                    "rejected_segments": [r.to_dict() for r in d.rejected_segments],
                }
                for d in decisions
            ],
            self.state.decisions_file,
        )
        stitcher = Stitcher(self.config)
        result = stitcher.stitch(decisions, self.state.base_output)
        write_reports(analyses, decisions, result, self.state.base_output)
        return result

    def _analysis_from_dict(self, d: dict) -> SegmentAnalysis:
        from src.core.models import Segment

        seg = Segment(**d["segment"])
        return SegmentAnalysis(
            segment=seg,
            metrics=d["metrics"],
            risks=d.get("risks", {}),
            realism_score=d["realism_score"],
            confidence=d["confidence"],
            critical_failures=d.get("critical_failures", []),
            needs_review=d.get("needs_review", False),
        )
