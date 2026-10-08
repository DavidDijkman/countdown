from datetime import date, datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field

from slideshow.countdown.pathpool import Entry
from slideshow.countdown.models import AudioFile

from slideshow.config import SLIDES_CONFIG

@dataclass
class Special:
    name: str
    entry: Entry | None = None
    audio: AudioFile | None = None
    audio_delay: int = 0
    command: list[str] | None = None
    in_rotation: bool = True
    weekday: int | None = None
    every_hour: bool = False
    time: tuple[int, int, int] | None = None
    last_triggered: datetime | None = None


class SpecialEvents:

    def __init__(self) -> None:
        self.specials = [
            self._parse_special(config)
            for config in SLIDES_CONFIG.get("specials", [])
        ]

    def due(self, threshold: timedelta, now: datetime | None = None) -> tuple[Special, timedelta] | None:
        """Return the first special occurring within threshold."""
        if now is None:
            now = datetime.now()

        closest: tuple[Special, timedelta] | None = None

        for special in self.specials:
            due_in = self._time_until_due(special, now)

            if due_in is None or due_in > threshold:
                continue

            if closest is None or due_in < closest[1]:
                closest = (special, due_in)

        return closest


    def mark_triggered(self, special: Special, now: datetime | None = None) -> None:
        """Mark a special as having been triggered."""
        if now is None:
            now = datetime.now()

        special.last_triggered = now


    def _time_until_due(self, special: Special, now: datetime) -> timedelta | None:
        if special.weekday is not None and now.weekday() != special.weekday:
            return None

        if special.time is not None and special.every_hour is None:
            hour, minute, second = special.time

            target = now.replace(
                hour=hour,
                minute=minute,
                second=second,
                microsecond=0,
            )

            if target <= now:
                target += timedelta(days=1)

            return target - now

        if special.every_hour:
            h_min, h_sec = 0, 0
            if special.time is not None:
                h_min = special.time.get("minute", 0)
                h_sec = special.time.get("second", 0)

            
            target = now.replace(
                minute=h_min,
                second=h_sec,
                microsecond=0,
            )

            if target <= now:
                target += timedelta(hours=1)

            return target - now

        return None

    def _parse_special(self, config: dict) -> Special:
        return Special(
            name=config["name"],
            entry=self._parse_entry(config),
            audio=self._parse_audio(config),
            audio_delay=self._parse_audio_delay(config),
            command=config.get("command"),
            in_rotation=config.get("in_rotation", True),
            weekday=config.get("weekday"),
            every_hour=config.get("every_hour", False),
            time=self._parse_time(config),
        )

    def _parse_entry(self, config: dict) -> Entry | None:
        image = config.get("slide")

        if image is None:
            return None

        return Entry(
            Path(image.get("path")),
            image.get("seconds", SLIDES_CONFIG["default"]["seconds"]),
        )

    def _parse_time(self, config: dict) -> tuple[int, int, int] | None:
        time = config.get("time")

        if time is None:
            return None

        hrs = time.get("hour")
        mins = time.get("minute")
        secs = time.get("second")

        if hrs is None: #hours is necessary
            return None

        if mins is None:
            mins = 0

        if secs is None:
            secs = 0

        if not 0 <= hrs <= 23:
            return None

        if not 0 <= mins <= 59:
            return None

        if not 0 <= secs <= 59:
            return None

        return hrs, mins, secs
        

    def _parse_audio(self, config: dict) -> AudioFile | None:
        audio = config.get("audio")

        if audio is None:
            return None

        return AudioFile(
            path=Path(audio["path"]),
            offset=audio.get("offset", 0.0),
            volume=audio.get("volume", 1.0),
        )

    def _parse_audio_delay(self, config: dict) -> int:
        audio = config.get("audio")
        if audio is None:
            return 0

        delay = audio.get("delay")

        if delay is None:
            return 0

        return delay
