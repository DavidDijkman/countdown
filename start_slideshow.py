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

from countdown.slideshow.slideshow import Slideshow
from countdown.config import *


ImageFile.LOAD_TRUNCATED_IMAGES = True


def start_sniffer() -> subprocess.Popen[bytes]:
	for terminal_name, option in TERMINAL_EMULATORS:
		terminal = shutil.which(terminal_name)
		if terminal is not None:
			return subprocess.Popen(
				[
					terminal,
					option,
					sys.executable,
					str(SNIFFER_SCRIPT),
				],
				cwd=SNIFFER_DIR,
				start_new_session=True,
			)

	raise OSError("No supported terminal emulator was found")



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


	quote_image = PROJECT_DIR / "quotes" / "images" / "quote.png"
	if not quote_image.is_file():
		print(f"Quote image not found yet; it will be generated: {quote_image}", file=sys.stderr)

	try:
		start_sniffer()
	except OSError as error:
		raise SystemExit(f"Could not open terminal for run_system.py: {error}") from error
	print("run_system.py started successfully.")

	root = tk.Tk()
	slideshow = Slideshow(root, 
	                      args.seconds, 
						  args.shuffle)
	slideshow.start()
	signal.signal(signal.SIGINT, lambda _signum, _frame: slideshow.close())
	
	try:
		root.mainloop()
	finally:
		slideshow.close()


if __name__ == "__main__":
	main()

