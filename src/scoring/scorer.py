from __future__ import annotations

from src.core.config import AppConfig

RISK_KEYS = {"blur", "flicker", "duplication", "hand_artifact_risk", "body_deformation_risk", "object_warp_risk", "lip_sync_risk"}


class RealismScorer:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.weights = config.score_weights.__dict__

    def compute(self, metrics: dict[str, float]) -> tuple[float, float, dict[str, float], list[str], bool]:
        weighted = 0.0
        total_weight = 0.0
        risks: dict[str, float] = {}
        for key, weight in self.weights.items():
            value = float(metrics.get(key, 0.5))
            total_weight += weight
            if key in RISK_KEYS:
                risks[key] = value
                contrib = (1.0 - value) * weight
            else:
                contrib = value * weight
            weighted += contrib

        score = (weighted / max(total_weight, 1e-6)) * 100.0
        confidence = self._confidence(metrics)
        critical = self._critical_failures(metrics)
        needs_review = confidence < 0.45 and self.config.review_queue_enabled
        return round(score, 2), round(confidence, 3), risks, critical, needs_review

    def _confidence(self, metrics: dict[str, float]) -> float:
        penalties = [
            metrics.get("corrupted_frame_ratio", 0.0),
            abs(metrics.get("face_consistency", 0.5) - 0.5),
            metrics.get("duplication", 0.0),
        ]
        conf = 1.0 - min(1.0, sum(penalties) / 2.2)
        return float(max(0.0, conf))

    def _critical_failures(self, metrics: dict[str, float]) -> list[str]:
        t = self.config.critical_failure_threshold / 100.0
        failures = []
        mapping = {
            "face_consistency": "severe_face_drift",
            "hand_artifact_risk": "severe_hand_deformation",
            "flicker": "heavy_flicker",
            "object_warp_risk": "severe_morphing",
            "duplication": "frozen_frame_burst",
            "corrupted_frame_ratio": "corrupted_frames",
        }
        for key, reason in mapping.items():
            value = metrics.get(key, 0.0)
            bad = value < (1.0 - t) if key == "face_consistency" else value > t
            if bad:
                failures.append(reason)
        return failures
