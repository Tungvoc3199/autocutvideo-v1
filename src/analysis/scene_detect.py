from __future__ import annotations

from pathlib import Path


def detect_scene_cuts(video_path: str | Path) -> list[float]:
    try:
        from scenedetect import ContentDetector, SceneManager, open_video
    except Exception:
        return []

    video = open_video(str(video_path))
    manager = SceneManager()
    manager.add_detector(ContentDetector())
    manager.detect_scenes(video)
    scenes = manager.get_scene_list()
    cuts: list[float] = []
    for start, _ in scenes:
        cuts.append(start.get_seconds())
    return sorted(set(cuts))
