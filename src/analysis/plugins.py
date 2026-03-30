from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class VisionAnalyzerPlugin(ABC):
    """Pluggable local analyzer for advanced artifact scoring."""

    name: str = "custom_plugin"

    @abstractmethod
    def analyze_segment(self, frames: list[np.ndarray], fps: float) -> dict[str, float]:
        raise NotImplementedError
