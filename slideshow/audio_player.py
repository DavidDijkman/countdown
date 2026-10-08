from dataclasses import dataclass
from pathlib import Path
import random
import shutil
import subprocess
import sys

from countdown.config import AUDIO_CONFIG


@dataclass
class AudioFile:
    path: Path
    offset: float = 0.0
    volume: float = 1.0


class AudioPlayer:
    def __init__(self) -> None:
        self.process: subprocess.Popen | None = None

    def play_file(self, audio_file: AudioFile) -> None:
        """Play a specific audio file."""
        if not audio_file.path.is_file():
            return

        player = shutil.which("ffplay")
        if player is None:
            print("ffplay not found", file=sys.stderr)
            return

        self.stop()

        self.process = subprocess.Popen(
            [
                player,
                "-nodisp",
                "-autoexit",
                "-loglevel", "error",
                "-ss", str(audio_file.offset),
                "-af", f"volume={audio_file.volume}",
                str(audio_file.path),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    # Volume and Offset aren't defined for random files yet
    def play_random(self, directory: Path) -> None:
        """Play a random audio file from a directory."""
        files = [
            path
            for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() in AUDIO_CONFIG.get("audio_extensions", [])
        ]

        if not files:
            return

        self.play_file(AudioFile(random.choice(files)))

    def stop(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()

        self.process = None