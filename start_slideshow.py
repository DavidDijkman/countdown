"""Fullscreen image slideshow.

Usage:
	python3 main.py --seconds 8 --shuffle

Press Escape or Q to quit, Space to pause/resume, and the arrow keys to
move between images.
"""

from __future__ import annotations

import argparse
import os
import random
import signal
import shutil
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

try:
	import tkinter as tk
except ModuleNotFoundError:
	raise SystemExit(
		"Tkinter is required. On Debian/Ubuntu, install it with: sudo apt install python3-tk"
	) from None

try:
	from PIL import Image, ImageFile, ImageOps, ImageTk
except ImportError as error:
	raise SystemExit(
		"Pillow's ImageTk support is required. On Debian/Ubuntu, install it with: "
		"sudo apt install python3-pil.imagetk"
	) from error


ImageFile.LOAD_TRUNCATED_IMAGES = True

PROJECT_DIR = Path(__file__).resolve().parent
SNIFFER_DIR = PROJECT_DIR / "Sniffer"
RUN_SYSTEM_SCRIPT = SNIFFER_DIR / "run_system.py"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}
VRIJMIBO_FILENAME = "vrijmibo.gif"
AUDIO_OFFSETS = {
	"gdn.sci.090701.sc.moon-countdown-launch.mp3": 0.0,
	"i-said-hey.mp3": 0.0,
	"live-is-life.mp3": 0.0,
	"toby.mp3": 0.0,
}


class Slideshow:
	def __init__(
		self,
		root: tk.Tk,
		images: list[Path],
		seconds: float,
		shuffle: bool,
		quote_image: Path | None = None,
		vrijmibo_image: Path | None = None,
		audio: list[Path] | None = None,
		system_process: subprocess.Popen[bytes] | None = None,
	) -> None:
		self.root = root
		self.images = images[:]
		self.quote_image = quote_image
		self.vrijmibo_image = vrijmibo_image
		self.quote_generated_index: int | None = None
		self.vrijmibo_index: int | None = None
		self.last_vrijmibo_hour: tuple[date, int] | None = None
		self.audio = audio or []
		self.last_audio_date: date | None = None
		self.audio_process: subprocess.Popen[bytes] | None = None
		self.system_process = system_process
		self.seconds = seconds
		self.index = 0
		self.paused = False
		self.timer_id: str | None = None
		self.photo: ImageTk.PhotoImage | None = None
		self.animation_image: Image.Image | None = None
		self.animation_photos: list[ImageTk.PhotoImage] = []
		self.animation_durations: list[float] = []
		self.animation_frame = 0
		self.animation_frames = 0
		self.animation_deadline = 0.0
		self.cached_photos: dict[Path, ImageTk.PhotoImage] = {}
		self.cached_animations: dict[
			Path, tuple[list[ImageTk.PhotoImage], list[float]]
		] = {}
		self.label = tk.Label(root, background="black")
		self.label.pack(fill="both", expand=True)

		if shuffle:
			random.shuffle(self.images)
		if quote_image is not None:
			self.images.append(quote_image)
		if vrijmibo_image is not None:
			self.vrijmibo_index = len(self.images)
			self.images.append(vrijmibo_image)

		root.configure(background="black", cursor="none")
		root.attributes("-fullscreen", True)
		root.bind("<Escape>", lambda _event: root.destroy())
		root.bind("q", lambda _event: root.destroy())
		root.bind("<space>", self.toggle_pause)
		root.bind("<Right>", self.next_image)
		root.bind("<Down>", self.next_image)
		root.bind("<Left>", self.previous_image)
		root.bind("<Up>", self.previous_image)
		root.bind("<Configure>", self.display_current)
		root.protocol("WM_DELETE_WINDOW", self.close)
		root.focus_force()

		root.update_idletasks()
		self.preprocess_images()
		self.display_current()
		self.check_vrijmibo()
		self.check_audio()

	def check_vrijmibo(self) -> None:
		now = datetime.now()
		hour = (now.date(), now.hour)
		if (
			self.vrijmibo_index is not None
			and now.weekday() == 4
			and hour != self.last_vrijmibo_hour
		):
			self.last_vrijmibo_hour = hour
			self.index = self.vrijmibo_index
			self.display_current()
		self.root.after(60_000, self.check_vrijmibo)

	def check_audio(self) -> None:
		now = datetime.now()
		if (
			self.audio
			and now.hour == 16
			and now.minute == 0
			and now.date() != self.last_audio_date
		):
			self.last_audio_date = now.date()
			self.play_random_song()
		self.root.after(15_000, self.check_audio)

	def play_random_song(self) -> None:
		player = shutil.which("ffplay")
		if player is None:
			print("Could not play audio: ffplay was not found", file=sys.stderr)
			return

		song = random.choice(self.audio)
		if self.audio_process is not None and self.audio_process.poll() is None:
			self.audio_process.terminate()
		self.audio_process = subprocess.Popen(
			[
				player,
				"-nodisp",
				"-autoexit",
				"-loglevel",
				"error",
				"-ss",
				str(AUDIO_OFFSETS.get(song.name, 0.0)),
				str(song),
			],
			stdout=subprocess.DEVNULL,
			stderr=subprocess.PIPE,
		)

	def close(self) -> None:
		if self.audio_process is not None and self.audio_process.poll() is None:
			self.audio_process.terminate()
		if self.system_process is not None and self.system_process.poll() is None:
			try:
				os.killpg(self.system_process.pid, signal.SIGINT)
				self.system_process.wait(timeout=5)
			except (OSError, subprocess.TimeoutExpired):
				self.system_process.terminate()
		self.root.destroy()

	def display_current(self, _event: tk.Event | None = None) -> None:
		if not self.images:
			return

		self.cancel_timer()
		self.close_animation()
		if self.quote_image is not None and self.images[self.index] == self.quote_image:
			if self.quote_generated_index != self.index:
				try:
					subprocess.run(
						[sys.executable, str(PROJECT_DIR / "quotes" / "quotes.py")],
						cwd=PROJECT_DIR / "quotes",
						check=True,
					)
				except (OSError, subprocess.CalledProcessError) as error:
					print(f"Could not generate quote image: {error}", file=sys.stderr)
					self.next_image()
					return
				self.quote_generated_index = self.index
		else:
			self.quote_generated_index = None
		path = self.images[self.index]
		if path in self.cached_animations:
			self.animation_photos, self.animation_durations = [
				list(cached) for cached in self.cached_animations[path]
			]
			self.animation_frames = len(self.animation_photos)
			self.display_animation_frame()
			return
		if path in self.cached_photos:
			self.photo = self.cached_photos[path]
			self.show_photo()
			self.schedule_next()
			return
		try:
			image = Image.open(path)
			self.animation_frames = getattr(image, "n_frames", 1)
			if self.animation_frames > 1:
				self.animation_image = image
				self.preload_animation_frame()
				return

			with image:
				self.photo = self.show_frame(image)
		except (OSError, EOFError, ValueError) as error:
			print(f"Skipping {self.images[self.index]}: {error}", file=sys.stderr)
			self.next_image()
			return

		self.show_photo()
		self.schedule_next()

	def preprocess_images(self) -> None:
		for path in self.images:
			if path == self.quote_image:
				continue
			try:
				with Image.open(path) as image:
					frame_count = getattr(image, "n_frames", 1)
					if frame_count > 1:
						photos: list[ImageTk.PhotoImage] = []
						durations: list[float] = []
						for frame_index in range(frame_count):
							image.seek(frame_index)
							frame = ImageOps.exif_transpose(image).convert("RGB")
							photos.append(ImageTk.PhotoImage(frame))
							durations.append(max(0.01, image.info.get("duration", 100) / 1000))
						self.cached_animations[path] = (photos, durations)
					else:
						self.cached_photos[path] = self.show_frame(image)
			except (OSError, EOFError, ValueError) as error:
				print(f"Could not preprocess {path}: {error}", file=sys.stderr)

	def show_frame(self, image: Image.Image, fit_to_screen: bool = True) -> ImageTk.PhotoImage:
		image = ImageOps.exif_transpose(image).convert("RGB")
		if fit_to_screen:
			available_width = max(self.root.winfo_width(), self.root.winfo_screenwidth())
			available_height = max(self.root.winfo_height(), self.root.winfo_screenheight())
			resampling = Image.LANCZOS
			scale = min(available_width / image.width, available_height / image.height)
			if scale != 1:
				image = image.resize(
					(round(image.width * scale), round(image.height * scale)),
					resampling,
				)
		return ImageTk.PhotoImage(image)

	def preload_animation_frame(self) -> None:
		if self.animation_image is None or len(self.animation_photos) >= self.animation_frames:
			return

		try:
			self.animation_image.seek(len(self.animation_photos))
			frame = ImageOps.exif_transpose(self.animation_image).convert("RGB")
			self.animation_photos.append(ImageTk.PhotoImage(frame))
			self.animation_durations.append(
				max(0.01, self.animation_image.info.get("duration", 100) / 1000)
			)
		except (OSError, EOFError, ValueError) as error:
			print(f"Skipping {self.images[self.index]}: {error}", file=sys.stderr)
			self.next_image()
			return

		if len(self.animation_photos) == 1:
			self.display_animation_frame()
		if len(self.animation_photos) < self.animation_frames:
			self.root.after_idle(self.preload_animation_frame)

	def display_animation_frame(self) -> None:
		if not self.animation_photos:
			return

		try:
			now = time.monotonic()
			if self.animation_deadline == 0:
				self.animation_deadline = now + self.animation_durations[self.animation_frame]
			while (
				self.animation_frame < self.animation_frames - 1
				and self.animation_frame + 1 < len(self.animation_photos)
				and now >= self.animation_deadline
			):
				self.animation_deadline += self.animation_durations[self.animation_frame]
				self.animation_frame += 1
			if (
				self.animation_frame < self.animation_frames - 1
				and self.animation_frame + 1 >= len(self.animation_photos)
				and now >= self.animation_deadline
			):
				self.timer_id = self.root.after(1, self.display_animation_frame)
				return
			self.photo = self.animation_photos[self.animation_frame]
		except (IndexError, OSError, ValueError) as error:
			print(f"Skipping {self.images[self.index]}: {error}", file=sys.stderr)
			self.next_image()
			return

		self.show_photo()

		if self.animation_frame < self.animation_frames - 1:
			self.schedule_animation_frame()
		else:
			self.timer_id = self.root.after(0, self.next_image)

	def show_photo(self) -> None:
		self.label.configure(image=self.photo)

	def schedule_animation_frame(self) -> None:
		delay = max(1, round((self.animation_deadline - time.monotonic()) * 1000))
		self.timer_id = self.root.after(delay, self.display_animation_frame)

	def schedule_next(self) -> None:
		self.cancel_timer()
		if not self.paused:
			self.timer_id = self.root.after(round(self.seconds * 1000), self.next_image)

	def cancel_timer(self) -> None:
		if self.timer_id is not None:
			self.root.after_cancel(self.timer_id)
			self.timer_id = None

	def close_animation(self) -> None:
		if self.animation_image is not None:
			self.animation_image.close()
			self.animation_image = None
		self.animation_photos.clear()
		self.animation_durations.clear()
		self.animation_frame = 0
		self.animation_frames = 0
		self.animation_deadline = 0.0

	def next_image(self, _event: tk.Event | None = None) -> None:
		self.index = (self.index + 1) % len(self.images)
		if self.index == self.vrijmibo_index and len(self.images) > 1:
			self.index = (self.index + 1) % len(self.images)
		self.display_current()

	def previous_image(self, _event: tk.Event | None = None) -> None:
		self.index = (self.index - 1) % len(self.images)
		if self.index == self.vrijmibo_index and len(self.images) > 1:
			self.index = (self.index - 1) % len(self.images)
		self.display_current()

	def toggle_pause(self, _event: tk.Event | None = None) -> None:
		self.paused = not self.paused
		if self.animation_frames > 1:
			if self.paused:
				self.cancel_timer()
			else:
				self.display_animation_frame()
		else:
			self.schedule_next()


def find_images(folder: Path) -> list[Path]:
	return sorted(
		path for path in folder.iterdir()
		if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
	)


def find_audio(folder: Path) -> list[Path]:
	return sorted(
		path for path in folder.iterdir()
		if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS
	)


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Display a folder of images like a screensaver.")
	parser.add_argument("--seconds", type=float, default=8.0, help="Seconds per image (default: 8)")
	parser.add_argument("--shuffle", action="store_true", help="Show images in random order")
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	folder = PROJECT_DIR / "slides"
	if not folder.is_dir():
		raise SystemExit(f"Not a folder: {folder}")
	if args.seconds <= 0:
		raise SystemExit("--seconds must be greater than zero")

	images = find_images(folder)
	audio = find_audio(PROJECT_DIR / "audio")
	vrijmibo_image = next(
		(path for path in images if path.name.lower() == VRIJMIBO_FILENAME),
		None,
	)
	if vrijmibo_image is not None:
		images.remove(vrijmibo_image)
	if not images and vrijmibo_image is None:
		raise SystemExit(f"No supported images found in {folder}")

	quote_image = PROJECT_DIR / "quotes" / "images" / "quote.png"
	if not quote_image.is_file():
		print(f"Quote image not found yet; it will be generated: {quote_image}", file=sys.stderr)

	try:
		system_process = subprocess.Popen(
			[sys.executable, str(RUN_SYSTEM_SCRIPT)],
			cwd=SNIFFER_DIR,
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL,
			start_new_session=True,
		)
	except OSError as error:
		raise SystemExit(f"Could not start sniffer system: {error}") from error
	print("run_system.py started successfully.")

	root = tk.Tk()
	slideshow = Slideshow(
		root,
		images,
		args.seconds,
		args.shuffle,
		quote_image,
		vrijmibo_image,
		audio,
		system_process,
	)
	signal.signal(signal.SIGINT, lambda _signum, _frame: slideshow.close())
	root.mainloop()


if __name__ == "__main__":
	main()

