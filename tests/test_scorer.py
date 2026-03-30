from src.core.config import AppConfig
from src.scoring.scorer import RealismScorer


def test_realism_score_high_quality_segment() -> None:
    scorer = RealismScorer(AppConfig())
    metrics = {
        "sharpness": 0.9,
        "blur": 0.1,
        "flicker": 0.1,
        "motion_stability": 0.9,
        "duplication": 0.05,
        "exposure_stability": 0.9,
        "color_consistency": 0.9,
        "face_consistency": 0.9,
        "hand_artifact_risk": 0.1,
        "body_deformation_risk": 0.1,
        "object_warp_risk": 0.1,
        "lip_sync_risk": 0.2,
        "continuity_potential": 0.8,
        "corrupted_frame_ratio": 0.0,
    }
    score, conf, _, critical, needs_review = scorer.compute(metrics)
    assert score > 75
    assert conf > 0.5
    assert not critical
    assert not needs_review


def test_realism_score_flags_critical_failures() -> None:
    scorer = RealismScorer(AppConfig(critical_failure_threshold=80.0))
    metrics = {
        "sharpness": 0.2,
        "blur": 0.9,
        "flicker": 0.95,
        "motion_stability": 0.2,
        "duplication": 0.85,
        "exposure_stability": 0.3,
        "color_consistency": 0.2,
        "face_consistency": 0.1,
        "hand_artifact_risk": 0.9,
        "body_deformation_risk": 0.8,
        "object_warp_risk": 0.95,
        "lip_sync_risk": 0.8,
        "continuity_potential": 0.2,
        "corrupted_frame_ratio": 0.92,
    }
    _, _, _, critical, _ = scorer.compute(metrics)
    assert "severe_face_drift" in critical
    assert "heavy_flicker" in critical
    assert "frozen_frame_burst" in critical
    assert "corrupted_frames" in critical
