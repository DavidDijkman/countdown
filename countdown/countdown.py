from datetime import datetime, timedelta
import tkinter as tk
import subprocess
import sys

from slideshow.countdown.image_cache import ImageCache, Slide
from slideshow.countdown.audio_player import AudioPlayer
from slideshow.countdown.pathpool import PathPool, Entry
from slideshow.countdown.special_events import SpecialEvents, Special

from slideshow.config import BASE

class Slideshow:

	def __init__(
		self,
		root: tk.Tk,
		seconds: float,
		shuffle: bool,
	) -> None:
		self.root = root
		self.seconds = seconds
		self.shuffle = shuffle

		self.screen_size = (
            root.winfo_screenwidth(),
            root.winfo_screenheight(),
        )

		self.paused = False

		self.audioplayer = AudioPlayer()
		self.cache = ImageCache(self.screen_size)
		self.pathpool = PathPool(self.shuffle)
		self.slide: Slide | None = None
		self.entry: Entry | None = None
		self.frame = 0
		self.interrupted = False
		self.special_events = SpecialEvents()

		self.timer_id: str | None = None
		self.special_timer_id: str | None = None
		self.audio_timer_id: str | None = None
		self.check_special_interval: int = 15		# polling interval in seconds

		self._configure_tk()

		self.label = tk.Label(root, background="black")
		self.label.pack(fill="both", expand=True)

	# Public Members

	def start(self) -> None:
		self._check_specials()
		self._next_slide()

	def close(self) -> None:
		self._cancel_timer()

		if self.special_timer_id is not None:
			self.root.after_cancel(self.special_timer_id)
			self.special_timer_id = None

		self.audioplayer.stop()
		self.root.destroy()


	# Private Members

	def _configure_tk(self) -> None:
        
		self.root.configure(background="black", cursor="none")
		self.root.attributes("-fullscreen", True)
		self.root.bind("<Escape>", 	lambda _event: self.root.destroy())
		self.root.bind("q", 		lambda _event: self.root.destroy())
		self.root.bind("<space>", 	self._toggle_pause)
		self.root.bind("<Right>", 	self._next_slide)
		self.root.bind("<Down>", 	self._next_slide)
		self.root.bind("<Left>", 	self._previous_slide)
		self.root.bind("<Up>", 		self._previous_slide)
		self.root.protocol("WM_DELETE_WINDOW", self.close)
		self.root.focus_force()

		self.root.update_idletasks()

	def _check_specials(self) -> None:
		now = datetime.now()
		polling_time = timedelta(seconds=self.check_special_interval)

		result = self.special_events.due(polling_time, now)

		if result is not None:
			special, due_in = result

			if due_in <= timedelta():
				self._trigger_special(special, now)
			else:
				self.special_timer_id = self.root.after(
					max(1, int(due_in.total_seconds() * 1000)),
					self._trigger_special,
					special,
				)
				return

		self.special_timer_id = self.root.after(
			int(polling_time.total_seconds() * 1000),
			self._check_specials,
		)

	def _trigger_special(self, special: Special) -> None:
		now = datetime.now()
		print(special.audio_delay)

		if (special.command != None):
				try:
					subprocess.run(
						[sys.executable, str(BASE / "quotes" / "quotes.py")],
						cwd=BASE / "quotes",
						check=True,
					)
				except (OSError, subprocess.CalledProcessError) as error:
					print(f"Could not generate quote image: {error}", file=sys.stderr)
					self.next_image()
					return

		self.special_events.mark_triggered(special, now)

		if special.entry is not None:
			self._interrupt_with_special(special)

		if special.audio is not None:
			self.audio_timer_id = self.root.after(
				special.audio_delay * 1000,
				self._play_special_audio,
				special,
			)

		self.special_timer_id = self.root.after(
			self.check_special_interval * 1000,
			self._check_specials,
		)

	def _show_current_slide(self) -> None:

		self._cancel_timer()
		self.frame = 0
		self._render()

	def _cancel_timer(self) -> None:
		if self.timer_id is not None:
			self.root.after_cancel(self.timer_id)
			self.timer_id = None

	def _next_slide(self, _event: tk.Event | None = None) -> None:
		while True:
			self.entry = self.pathpool.next_entry()

			if self.entry:
				self.slide = self.cache.get(self.entry.path)
				break
		self._show_current_slide()

		self.root.after(100, self._preload_next)

	def _preload_next(self) -> None:
		next_entry = self.pathpool.peek_next()

		if next_entry is None:
			return

		if next_entry.path.suffix.lower() == ".gif":
			return

		self.cache.get(next_entry.path)

	def _previous_slide(self, _event: tk.Event | None = None) -> None:
		while True:
			self.entry = self.pathpool.previous_entry()

			if self.entry:
				self.slide = self.cache.get(self.entry.path)
				break
		self._show_current_slide()

	def _toggle_pause(self, _event: tk.Event | None = None) -> None:
		self.paused = not self.paused

		if self.paused:
			self._cancel_timer()
			return

		self._render()

	def _interrupt_with_special(self, special: Special) -> None:
		if self.interrupted:
			return

		self.interrupted = True
		self._cancel_timer()

		self._show_special(special)

	def _show_special(self, special: Special):
		if special.entry is None:
			return

		self.entry = special.entry
		self.slide = self.cache.get(special.entry.path)
		self.frame = 0

		self._render()

	def _play_special_audio(self, special: Special) -> None:
		if special.audio is None:
			return

		if special.audio.path.is_dir():
			self.audioplayer.play_random(special.audio.path)
		else:
			self.audioplayer.play_file(special.audio)

	def _render(self) -> None:
		if self.slide is None:
			return

		self.label.configure(
			image=self.slide.frames[self.frame]
		)

		if self.paused:
			return

		if self.slide.animated:
			delay_ms = self.slide.durations[self.frame]
		else:
			delay_ms = int(self.entry.seconds * 1000)

		self.timer_id = self.root.after(
			delay_ms,
			self._advance,
		)

	def _advance(self) -> None:
		self.timer_id = None

		if self.slide is None:
			return

		if self.slide.animated and self.frame < len(self.slide.frames) - 1: # end of animation
			self.frame += 1
			self._render()
		else:
			self.interrupted = False # slide or animation done
			self._next_slide()