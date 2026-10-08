# image_cache.py
from dataclasses import dataclass
from pathlib import Path
from PIL import Image, ImageOps, ImageTk, UnidentifiedImageError

from countdown.slideshow.models import Slide

class ImageCache:
    def __init__(self, screen_size: tuple[int, int]):
        self.screen = screen_size
        self._slides: dict[Path, Slide] = {}

    def get(self, path: Path) -> Slide:
        if path not in self._slides:
            self._slides[path] = self._load(path)
        return self._slides[path]

    def invalidate(self, path: Path) -> None:
        self._slides.pop(path, None)

    def _load(self, path: Path) -> Slide | None:
        frames, durations = [], []

        try:
            with Image.open(path) as image:
                for i in range(getattr(image, "n_frames", 1)):
                    image.seek(i)
                    frames.append(ImageTk.PhotoImage(self._fit(image)))
                    ms = image.info.get("duration", 100)

                    durations.append(max(ms, 20)) #minimum of 20 ms per frame. some gifs give 0:/
        except UnidentifiedImageError:
            print(f"couldn't load {path}")
            return None
        except FileNotFoundError:
            print(f"couldn't find {path}")
            return None
        
        return Slide(frames, durations)

    def _fit(self, frame: Image.Image) -> Image.Image:
        frame = ImageOps.exif_transpose(frame).convert("RGB")
        scale = min(self.screen[0] / frame.width, self.screen[1] / frame.height)
        if scale != 1:
            frame = frame.resize(
                (round(frame.width * scale), round(frame.height * scale)),
                Image.LANCZOS,
            )
        return frame