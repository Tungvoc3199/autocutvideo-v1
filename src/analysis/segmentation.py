from __future__ import annotations

from src.core.models import Segment, VideoMetadata


def split_fixed_windows(meta: VideoMetadata, window_sec: float) -> list[Segment]:
    segments: list[Segment] = []
    t = 0.0
    scene = 0
    while t < meta.duration:
        end = min(meta.duration, t + window_sec)
        segments.append(Segment(video_path=meta.path, start=t, end=end, scene_id=scene))
        t = end
        scene += 1
    return segments


def merge_scene_boundaries(
    base_segments: list[Segment], scene_cuts: list[float], tolerance: float = 0.1
) -> list[Segment]:
    if not scene_cuts:
        return base_segments
    for seg in base_segments:
        for cut in scene_cuts:
            if abs(seg.start - cut) <= tolerance:
                seg.scene_id += 1
    return base_segments
