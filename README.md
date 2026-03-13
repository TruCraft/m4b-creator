# M4B Creator

Create M4B audiobook files with chapters from individual audio files. Includes both a GUI and a command-line interface.

## Features

- **Multi-format input** — MP3, FLAC, M4A, M4B, AAC, OGG, Opus, WAV
- **Automatic chapter markers** — each input file becomes a chapter
- **Metadata extraction** — auto-populates title, author, year, cover art, and more from source audio tags
- **Cover art** — automatically extracted from source audio, or manually specified
- **Smart encoding** — stream-copies AAC files (fast, lossless) and re-encodes other formats
- **Configurable bitrate** — 64k to 256k AAC encoding
- **Sorted input** — chapter files are automatically sorted for correct ordering

## Requirements

- Python 3.8+
- [ffmpeg](https://ffmpeg.org/) installed and available on PATH

### Install ffmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows — download from https://ffmpeg.org/download.html
```

## Installation

### Using uv (recommended)

Install directly from GitHub without cloning:

```bash
uv tool install git+https://github.com/TruCraft/m4b-creator.git
```

Or from a local clone:

```bash
git clone https://github.com/TruCraft/m4b-creator.git
cd m4b-creator
uv tool install .
```

This installs `m4b` and `m4b-gui` as globally available commands.

To update:

```bash
uv tool uninstall m4b-creator && uv cache clean m4b-creator && uv tool install git+https://github.com/TruCraft/m4b-creator.git
```

### Using pip

```bash
pip install -e .
```

Both methods install the Python dependencies ([mutagen](https://mutagen.readthedocs.io/), [Pillow](https://pillow.readthedocs.io/)) automatically.

## Usage

### Command Line

```bash
# Basic — metadata, cover art, and year are auto-extracted from source files
m4b output.m4b *.m4a

# Use embedded title tags as chapter names
m4b output.m4b *.m4a --use-tags

# Override auto-extracted metadata
m4b output.m4b *.m4a --title "My Book" --author "Author Name" --narrator "Narrator"

# Specify cover art and bitrate
m4b output.m4b *.mp3 --cover cover.jpg --bitrate 192k

# All options
m4b output.m4b *.m4a \
  --title "Book Title" \
  --author "Author" \
  --narrator "Narrator" \
  --year 2021 \
  --comment "A great audiobook" \
  --cover cover.jpg \
  --bitrate 128k \
  --use-tags
```

Auto-extracted metadata from source files can always be overridden by passing the corresponding flag explicitly.

### GUI

```bash
m4b-gui
```

1. Click **Add Audio Files** and select your chapter files
2. Metadata and cover art are auto-populated from the first file's tags
3. Edit the title, author, narrator, and other fields as needed
4. Choose an AAC bitrate (default 128k, ignored when stream-copying AAC input)
5. Click **Create M4B** and choose where to save

### Python API

```python
from m4b_creator import M4BCreator

creator = M4BCreator()

# Extract metadata and cover from source files
metadata = creator.extract_metadata("chapter1.m4a")
cover_bytes = creator.extract_cover("chapter1.m4a")

# Create the M4B
creator.create(
    audio_files=["chapter1.m4a", "chapter2.m4a", "chapter3.m4a"],
    output_path="book.m4b",
    title="My Audiobook",
    author="Author Name",
    narrator="Narrator Name",
    cover_path="cover.jpg",
    bitrate="128k",
)
```

## Output Metadata

The following tags are written to the output M4B file:

| Tag | Source |
|-----|--------|
| `title` | `--title` flag, or album/title from source tags |
| `album` | Same as title |
| `artist` | `--author` flag, or artist/album artist from source tags |
| `album_artist` | `--narrator` flag, or same as author |
| `date` | `--year` flag, or date from source tags |
| `comment` | `--comment` flag |

## How It Works

1. **Analyze** — reads duration and metadata from each input file using mutagen
2. **Concatenate** — uses ffmpeg's concat demuxer to join all files into a single AAC stream (stream-copy for AAC inputs, re-encode for other formats)
3. **Add chapters** — writes an ffmpeg metadata file with chapter markers based on cumulative durations
4. **Mux** — combines the audio, chapter metadata, and optional cover art into the final `.m4b` file
