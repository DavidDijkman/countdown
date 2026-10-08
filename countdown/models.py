# models.py
from dataclasses import dataclass, field
from pathlib import Path
from PIL import ImageTk

@dataclass
class Slide:
    frames: list[ImageTk.PhotoImage]
    durations: list[float]          # seconds per frame; ignored for stills

    @property
    def animated(self) -> bool:
        return len(self.frames) > 1


@dataclass
class AudioFile:
    path: Path
    offset: float = 0.0
    volume: float = 1.0