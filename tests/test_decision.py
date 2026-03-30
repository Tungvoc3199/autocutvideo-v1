from src.core.config import AppConfig
from src.core.decision import build_decisions
from src.core.models import Segment, SegmentAnalysis


def _analysis(start: float, end: float, score: float, critical: list[str] | None = None) -> SegmentAnalysis:
    return SegmentAnalysis(
        segment=Segment(video_path="clip.mp4", start=start, end=end, scene_id=0),
        metrics={},
        risks={},
        realism_score=score,
        confidence=0.8,
        critical_failures=critical or [],
        needs_review=False,
    )


def test_decision_keeps_and_rejects_segments() -> None:
    config = AppConfig(realism_threshold=60, trim_padding_ms=100)
    analyses = [_analysis(0, 1, 75), _analysis(1, 2, 40), _analysis(2, 3, 80)]
    decisions = build_decisions(analyses, config)
    assert len(decisions) == 1
    decision = decisions[0]
    assert not decision.rejected
    assert len(decision.kept_segments) == 2
    assert len(decision.rejected_segments) == 1
    assert decision.kept_segments[0].segment.start == 0.1


def test_decision_rejects_clip_if_too_short() -> None:
    config = AppConfig(realism_threshold=60, min_segment_duration=2.0, trim_padding_ms=400)
    analyses = [_analysis(0, 1, 90)]
    decision = build_decisions(analyses, config)[0]
    assert decision.rejected
    assert "too_short_after_trimming" in decision.reasons
