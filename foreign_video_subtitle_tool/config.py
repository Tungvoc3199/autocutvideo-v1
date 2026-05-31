from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_OUTPUT_DIR = Path("output")
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".m4v", ".webm"}


@dataclass(frozen=True, slots=True)
class SubtitleStyle:
    font_name: str = "Arial"
    font_size: int = 24
    primary_colour: str = "&H00FFFFFF"
    outline_colour: str = "&H00000000"
    outline: int = 3
    shadow: int = 0
    alignment: int = 2
    margin_v: int = 56
    bold: int = 0

    def to_force_style(self) -> str:
        parts = {
            "FontName": self.font_name,
            "FontSize": self.font_size,
            "PrimaryColour": self.primary_colour,
            "OutlineColour": self.outline_colour,
            "Outline": self.outline,
            "Shadow": self.shadow,
            "Alignment": self.alignment,
            "MarginV": self.margin_v,
            "Bold": self.bold,
        }
        return ",".join(f"{key}={value}" for key, value in parts.items())
