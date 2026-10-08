import json
import os
from pathlib import Path
from dotenv import load_dotenv

BASE = Path(__file__).parent
load_dotenv(BASE / ".env")        # runs first, on import

audio_config_path = os.getenv("AUDIO_CONFIG_FILE", "audio_config.json")
slides_config_path = os.getenv("SLIDES_CONFIG_FILE", "slides_config.json")

def _load(file):
    with open(BASE / file, encoding="utf-8") as f:
        return json.load(f)

SLIDES_CONFIG = _load(BASE / slides_config_path)
AUDIO_CONFIG = _load(BASE / audio_config_path)

PROJECT_DIR = Path(__file__).resolve().parent
SNIFFER_DIR = PROJECT_DIR / "Sniffer"
SNIFFER_SCRIPT = SNIFFER_DIR / "run_system.py"
TERMINAL_EMULATORS = (
	("x-terminal-emulator", "-e"),
	("gnome-terminal", "--"),
	("konsole", "-e"),
	("xfce4-terminal", "--command"),
	("xterm", "-e"),
)
SNIFFER_FILENAME = "sniffer_slide.png"