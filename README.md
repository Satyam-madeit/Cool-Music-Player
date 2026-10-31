# CMP — Cool Music Player

A lightweight, premium Windows music player built with Python + pywebview + WebView2.

## Features

- **Native Windows App**: Uses pywebview with Microsoft WebView2 for a truly native feel
- **High-Quality Audio**: Supports FLAC (up to 24-bit/192kHz), MP3, WAV, OGG, Opus, M4A/AAC, DSD
- **Real-time Visualizer**: Web Audio API powered frequency spectrum visualizer
- **10-Band EQ**: With presets and preamp control
- **Dynamic Theming**: Album art colors adapt the UI in real-time
- **Local Library**: File/folder import, drag-and-drop, indexed directories
- **Playlists & Favourites**: Full playlist management with persistence
- **Media Keys**: Global media key support
- **Offline Storage**: JSON-based persistence, no database required

## Tech Stack

- **Frontend**: Vanilla HTML, CSS, JavaScript (no frameworks)
- **Desktop**: pywebview + Microsoft WebView2
- **Backend**: Python 3.10+
- **Metadata**: Mutagen
- **Audio**: HTML5 Audio + Web Audio API
- **Packaging**: PyInstaller

## Requirements

- Windows 10/11 with WebView2 Runtime (included in modern Windows)
- Python 3.10+
- Dependencies in `requirements.txt`

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd Cool-Music-Player

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development
python main.py
```

## Building

```bash
# Build standalone executable
python build.py
```

Output: `dist/CMP.exe`

## Project Structure

```
CMP/
├── assets/              # Logo, stitch.html reference design
├── frontend/            # HTML, CSS, JS (served by pywebview)
│   ├── index.html       # Main UI (faithful Stitch recreation)
│   ├── assets/          # Placeholder album art
│   └── fonts/           # Local font CSS
├── backend/             # Python modules
│   ├── api.py           # pywebview JS-Python bridge
│   ├── library.py       # Library management + JSON persistence
│   └── audio_server.py  # HTTP Range server for audio streaming
├── main.py              # Entry point
├── build.py             # PyInstaller build script
├── requirements.txt
└── README.md
```

## Design

The UI is a faithful recreation of the Stitch design:
- Project: `1040429907179381436`
- Screen: `CMP - Clean Music Player`
- Local reference: `assets/stitch.html`

## Architecture

- **Python** handles: file selection, filesystem access, metadata extraction, library management, persistence, HTTP audio serving
- **JavaScript** handles: UI, playback, EQ, visualizer, queue, controls, dynamic theming
- **Bridge**: pywebview's JavaScript-Python bridge for safe communication

## Audio Pipeline

1. User selects files/folders via native dialogs
2. Python extracts metadata with Mutagen, stores in JSON
3. JavaScript requests audio URL from Python
4. Python serves audio via local HTTP server with Range support
5. HTML5 Audio + Web Audio API handles playback, visualization, EQ

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Space | Play/Pause |
| → / ← | Seek forward/backward |
| ↑ / ↓ | Volume up/down |
| N | Next track |
| P | Previous track |
| S | Toggle shuffle |
| R | Cycle repeat mode |

## License

MIT License - See LICENSE file for details.