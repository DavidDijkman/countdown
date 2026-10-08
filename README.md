# Python Countdown for the Francken Members' Room

A Python/Tkinter-based fullscreen slideshow and countdown application for the Francken Members' Room.

## Usage

Run the slideshow from **outside the `countdown` folder**:

```bash
python -m countdown.start_slideshow [OPTIONS]
```

### Command-line options

| Option      | Description                       |
| ----------- | --------------------------------- |
| `--shuffle` | Display slides in a random order. |

For example:

```bash
python -m countdown.start_slideshow --shuffle
```

## Configuration

The slideshow is configured using the following files and folders:

```text
slides/               # Images and animations for regular slides.
                      # Slides can be organized into different namespaces.

audio/                # Audio files used by special events.

config.py             # General constants used for running subprocesses
                      # and the sniffer.

audio_config.json     # Configures the available audio files.

slides_config.json    # Configures slide namespaces, including:
                      # - seconds per slide
                      # - relative frequency
                      # - special events

.env                  # Optional environment variables, including the
                      # locations of the JSON configuration files.
```

### Slides

The `slides/` directory contains the images and animations displayed by the slideshow.

Slides can be organized into subfolders, which can then be configured independently in `slides_config.json`.

For example:

```text
slides/
├── image1.jpg
├── image2.png
├── memes/
│   ├── meme1.jpg
│   └── meme2.png
└── announcements/
    └── announcement.png
```

Each configured folder can have its own display duration and relative frequency.

## Keyboard Controls

The slideshow runs in fullscreen mode and hides the mouse cursor.

| Key           | Action                        |
| ------------- | ----------------------------- |
| `Esc`         | Exit the slideshow            |
| `Q`           | Exit the slideshow            |
| `Space`       | Pause or resume the slideshow |
| `Right Arrow` | Show the next slide           |
| `Down Arrow`  | Show the next slide           |
| `Left Arrow`  | Show the previous slide       |
| `Up Arrow`    | Show the previous slide       |

The slideshow automatically takes keyboard focus when it starts, so these controls should work without clicking the window first.

## Special Events

Special events can be configured through `slides_config.json`. These can be used to trigger behaviour such as playing audio or displaying specific slides.

Audio used by special events is configured separately in `audio_config.json` and stored in the `audio/` directory.

## Development

When running or developing the project, make sure you execute the module from the directory **containing** the `countdown` package:

```text
project/
└── countdown/
    ├── start_slideshow.py
    ├── ...
```

From `project/`, run:

```bash
python -m countdown.start_slideshow
```

Running the file directly from inside the package, for example:

```bash
python start_slideshow.py
```

may cause package imports to fail.



## pip requirements
piper
python-dotenv
matplotlib
tkinter


## cl requirememts
PIL
tkinter
ffmpeg
