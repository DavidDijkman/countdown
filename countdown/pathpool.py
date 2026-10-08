import random
from dataclasses import dataclass
from pathlib import Path

from slideshow.config import SLIDES_CONFIG, BASE


@dataclass
class Pool:
    name: str
    images: list[Path]
    seconds: float = SLIDES_CONFIG["default"].get("seconds")
    frequency: int = SLIDES_CONFIG["default"].get("frequency")       # max number of images from this pool per cycle


@dataclass(frozen=True)
class Entry:
    path: Path
    seconds: float


class PathPool:
    def __init__(self, shuffle: bool = True) -> None:
        self.shuffle = shuffle
        self.pools: dict[str, Pool] = {}
        self.playlist: list[Entry] = self._build_playlist()
        self.index = -1                  # so the first next_path() returns item 0

    # ---- public ----

    def next_entry(self) -> Entry | None:
        self.index += 1
        if self.index >= len(self.playlist):
            # print("Rebuilding slide queue")
            # end of cycle: rescan folders and start a fresh cycle
            self.playlist = self._build_playlist()
            self.index = 0
            # print("Done rebuilding!")
            # for entry in self.playlist:
            #    print(entry.path)

        if not self.playlist:
            self.index = -1
            return None
        return self.playlist[self.index]

    def previous_entry(self) -> Entry | None:
        if not self.playlist:
            return None
        self.index = (self.index - 1) % len(self.playlist)
        return self.playlist[self.index]

    def current_entry(self) -> Entry | None:
        if not self.playlist:
            return None
        return self.playlist[self.index]

    def peek_next(self) -> Entry | None:
        if not self.playlist:
            return

        next_index = (self.index + 1) % len(self.playlist)
        return self.playlist[next_index]

    # ---- internals ----

    def _scan_pools(self) -> None:
        self.pools = {}
        root = BASE / Path(SLIDES_CONFIG["slides_folder"])
        defaults = SLIDES_CONFIG["default"]

        if not root.exists():
            raise FileNotFoundError(
                f"Slides folder does not exist: {root}"
            )
                

        if not root.is_dir():
            raise FileNotFoundError(
                f"Slides path is not a directory: {root}"
            )

        # images sitting directly in the root folder
        self.pools["default"] = Pool(
            "default",
            self._find_images(root),
            defaults["seconds"],
            defaults["frequency"],
        )

        # one pool per configured subfolder, falling back on the defaults
        for name, folder_config in SLIDES_CONFIG["folders"].items():
            settings = {**defaults, **(folder_config or {})}
            self.pools[name] = Pool(
                name,
                self._find_images(root / name),
                settings["seconds"],
                settings["frequency"],
            )

    def _build_playlist(self) -> list[Entry]:
        self._scan_pools()

        playlist: list[Entry] = []

        for name, pool in self.pools.items():

            if not pool.images:
                continue

            if pool.frequency < 0:
                count = len(pool.images)
            else:
                count = min(pool.frequency, len(pool.images))


            if count == 0:
                continue

            if self.shuffle:
                chosen = random.sample(pool.images, count)
            else:
                chosen = pool.images[:count]

            playlist.extend(
                Entry(path, pool.seconds)
                for path in chosen
            )

        if (len(playlist) == 0):
            raise ValueError("Playlist is empty, no eligible slides found")

        if self.shuffle:
            random.shuffle(playlist)

        print(f"playlist complete: {len(playlist)} entries", flush=True)

        return playlist

    @staticmethod
    def _find_images(folder: Path) -> list[Path]:
        if not folder.is_dir():
            return []
        extensions = {e.lower() for e in SLIDES_CONFIG["image_extensions"]}
        return sorted(
            path for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() in extensions
        )