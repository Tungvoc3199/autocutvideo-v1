from __future__ import annotations

from collections import defaultdict

from src.core.config import AppConfig
from src.core.models import ClipDecision, Segment, SegmentAnalysis


def build_decisions(analyses: list[SegmentAnalysis], config: AppConfig) -> list[ClipDecision]:
    grouped: dict[str, list[SegmentAnalysis]] = defaultdict(list)
    for a in analyses:
        grouped[a.segment.video_path].append(a)

    output: list[ClipDecision] = []
    for video_path, segs in grouped.items():
        segs.sort(key=lambda s: s.segment.start)
        kept, rejected = [], []
        for seg in segs:
            if seg.realism_score < config.realism_threshold or seg.critical_failures:
                rejected.append(seg)
            else:
                kept.append(seg)

        kept_adjusted = _apply_trim_padding(kept, config.trim_padding_ms)
        total_duration = sum(k.segment.duration for k in kept_adjusted)
        reject_clip = total_duration < config.min_segment_duration
        reasons = ["too_short_after_trimming"] if reject_clip else []

        output.append(
            ClipDecision(
                video_path=video_path,
                kept_segments=kept_adjusted if not reject_clip else [],
                rejected_segments=rejected if not reject_clip else segs,
                rejected=reject_clip,
                reasons=reasons,
            )
        )
    return output


def _apply_trim_padding(
    segments: list[SegmentAnalysis], trim_padding_ms: int
) -> list[SegmentAnalysis]:
    if trim_padding_ms <= 0:
        return segments
    pad = trim_padding_ms / 1000.0
    adjusted: list[SegmentAnalysis] = []
    for item in segments:
        s = max(0.0, item.segment.start + pad)
        e = max(s, item.segment.end - pad)
        seg = Segment(video_path=item.segment.video_path, start=s, end=e, scene_id=item.segment.scene_id)
        adjusted.append(
            SegmentAnalysis(
                segment=seg,
                metrics=item.metrics,
                risks=item.risks,
                realism_score=item.realism_score,
                confidence=item.confidence,
                critical_failures=item.critical_failures,
                needs_review=item.needs_review,
            )
        )
    return adjusted
