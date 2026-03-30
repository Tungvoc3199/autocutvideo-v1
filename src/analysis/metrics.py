from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from src.core.models import Segment


@dataclass
class AnalyzerPlugin:
    name: str = "base"

    def analyze_segment(self, _frames: list[np.ndarray], _fps: float) -> dict[str, float]:
        return {}


class SegmentAnalyzer:
    def __init__(self, plugin: AnalyzerPlugin | None = None) -> None:
        self.plugin = plugin
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def _read_frames(self, video_path: str | Path, start: float, end: float) -> tuple[list[np.ndarray], float]:
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)
        frames: list[np.ndarray] = []
        while cap.isOpened():
            current_sec = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            if current_sec > end:
                break
            ok, frame = cap.read()
            if not ok:
                break
            frames.append(frame)
        cap.release()
        return frames, fps

    def analyze(self, segment: Segment) -> dict[str, float]:
        frames, fps = self._read_frames(segment.video_path, segment.start, segment.end)
        if not frames:
            return {
                "sharpness": 0.0,
                "blur": 1.0,
                "flicker": 1.0,
                "motion_stability": 0.0,
                "duplication": 1.0,
                "exposure_stability": 0.0,
                "color_consistency": 0.0,
                "face_consistency": 0.0,
                "hand_artifact_risk": 0.5,
                "body_deformation_risk": 0.5,
                "object_warp_risk": 0.5,
                "lip_sync_risk": 0.5,
                "continuity_potential": 0.0,
                "corrupted_frame_ratio": 1.0,
            }

        gray = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]
        lap_vars = np.array([cv2.Laplacian(g, cv2.CV_64F).var() for g in gray])
        sharpness = float(np.clip(np.mean(lap_vars) / 250.0, 0, 1))
        blur = 1.0 - sharpness

        means = np.array([np.mean(g) for g in gray])
        flicker = float(np.clip(np.std(np.diff(means)) / 20.0, 0, 1)) if len(means) > 1 else 0.0

        diffs = []
        hdiffs = []
        flow_mags = []
        duplicates = 0
        face_counts = []
        corrupted = 0

        for i in range(1, len(gray)):
            a, b = gray[i - 1], gray[i]
            d = cv2.absdiff(a, b)
            avg_diff = float(np.mean(d))
            diffs.append(avg_diff)
            if avg_diff < 1.2:
                duplicates += 1
            hist_a = cv2.calcHist([a], [0], None, [64], [0, 256])
            hist_b = cv2.calcHist([b], [0], None, [64], [0, 256])
            hdiffs.append(float(cv2.compareHist(hist_a, hist_b, cv2.HISTCMP_BHATTACHARYYA)))
            flow = cv2.calcOpticalFlowFarneback(a, b, None, 0.5, 3, 15, 3, 5, 1.1, 0)
            flow_mags.append(float(np.linalg.norm(flow, axis=2).mean()))
            if np.isnan(avg_diff) or np.isinf(avg_diff):
                corrupted += 1

        for g in gray:
            faces = self.face_cascade.detectMultiScale(g, scaleFactor=1.1, minNeighbors=4)
            face_counts.append(len(faces))

        duplication = duplicates / max(1, len(gray) - 1)
        motion_stability = 1.0 - float(np.clip(np.std(flow_mags) / 4.0, 0, 1)) if flow_mags else 0.5
        exposure_stability = 1.0 - float(np.clip(np.std(np.diff(means)) / 18.0, 0, 1)) if len(means) > 1 else 1.0
        color_consistency = 1.0 - float(np.clip(np.mean(hdiffs), 0, 1)) if hdiffs else 0.5
        face_consistency = 1.0 - float(np.clip(np.std(face_counts) / 2.0, 0, 1)) if face_counts else 0.5
        hand_artifact_risk = float(np.clip((flicker + (1.0 - motion_stability)) / 2.0, 0, 1))
        body_deformation_risk = float(np.clip((1.0 - motion_stability) * 0.7 + flicker * 0.3, 0, 1))
        object_warp_risk = float(np.clip(np.mean(diffs) / 50.0, 0, 1)) if diffs else 0.5
        continuity_potential = float(np.clip((color_consistency + motion_stability) / 2.0, 0, 1))
        corrupted_ratio = corrupted / max(1, len(gray) - 1)

        metrics = {
            "sharpness": sharpness,
            "blur": blur,
            "flicker": flicker,
            "motion_stability": motion_stability,
            "duplication": duplication,
            "exposure_stability": exposure_stability,
            "color_consistency": color_consistency,
            "face_consistency": face_consistency,
            "hand_artifact_risk": hand_artifact_risk,
            "body_deformation_risk": body_deformation_risk,
            "object_warp_risk": object_warp_risk,
            "lip_sync_risk": 0.5,
            "continuity_potential": continuity_potential,
            "corrupted_frame_ratio": corrupted_ratio,
        }
        if self.plugin:
            metrics.update(self.plugin.analyze_segment(frames, fps))
        return metrics
