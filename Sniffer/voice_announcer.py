import os
import shutil
import subprocess
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUEUE_FILENAME = os.path.join(BASE_DIR, 'voice_queue.jsonl')
AUDIO_DIR = os.path.join(BASE_DIR, 'audiofiles/')
VOICES_DIR = os.path.join(BASE_DIR, 'voicefiles/')
VOLUME = 100
POLL_INTERVAL_SECONDS = 0.5
VOICE_NAME = "en_US-ryan-high"


def speak_name(name):
    greeting = f'Welcome, {name}'

    speech_engine = shutil.which('espeak')
    command = [speech_engine, greeting]
    run_options = {}

    subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        **run_options,
    )

def audio_exists(name):
    path = f"{AUDIO_DIR}{name}.wav"

    return os.path.isfile(path)

def generate_audio(name, text):
    print("generating audio file")
    audiofile_dir = f"{AUDIO_DIR}{name}.wav"
    tempfile_dir = f"{AUDIO_DIR}temp.wav"
    voicefile = VOICE_NAME
    generate_command = ["python", 
               "-m",  "piper", 
               "-m", voicefile, 
               "--output_file", tempfile_dir, 
               "--data-dir", f"{VOICES_DIR}", 
               f"{text}"]

    run_options = {}
    subprocess.run(
        generate_command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        **run_options,
    )

    pad_command = ["ffmpeg",
                   "-y",
                   "-i", tempfile_dir,
                   "-af", "adelay=300:all=1,apad=pad_dur=0.3",
                   audiofile_dir]

    subprocess.run(
        pad_command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        **run_options,
    )

def play_audio(name):
    audiofile_dir = f"{AUDIO_DIR}{name}.wav"
    print("playing " + audiofile_dir)

    command = ["ffplay", 
               "-nodisp", 
               "-autoexit", 
               f"-volume", f"{VOLUME}", 
               f"{audiofile_dir}"]

    run_options = {}
    subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        **run_options,
    )


def main():
    print("Voice Announcer Running")
    print(QUEUE_FILENAME)
    with open(QUEUE_FILENAME, 'a+', encoding='utf-8') as queue_file:
        queue_file.seek(0, os.SEEK_END)

        while True:
            line = queue_file.readline()
            
            if line:
                name = line.strip()
                if name:
                    if not audio_exists(name):
                        generate_audio(name, f"Welcome {name}!")

                    play_audio(name)
                    #speak_name(name)
            else:
                time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == '__main__':
    main()
