# 🎵 iPodyssey

> Liberation tool for your iPod's music collection

Extract music, playlists, and metadata from classic iPod devices with a beautiful terminal interface.

## 📸 Screenshots

### Terminal UI
```
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║      iPodyssey - iPod Music Liberation Tool              ║
║                                                          ║
║      Extract your music collection from classic iPods    ║
║      Support for iPod Video and other classic models     ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

Searching for iPod devices...

╭──────────────── iPod Detected ─────────────────╮
│                                                │
│  Device Information                            │
│  ──────────────────                            │
│  Path          : /Volumes/iPod                 │
│  Name          : iPod                          │
│  Database      : Found (18 MB)                 │
│  Music Folders : 50                            │
│  Music Files   : 12,159                        │
│                                                │
╰────────────────────────────────────────────────╯
```

### Desktop GUI

<img width="912" height="744" alt="image" src="https://github.com/user-attachments/assets/e04903f9-90fd-444e-aa6c-30b3b0cc2f0f" />


The GUI provides an intuitive interface with:
- Automatic iPod detection with device information display
- Multiple extraction modes (Database Only, Scan Files Only, Both)
- Format selection for exports (CSV, JSON, M3U, Text Report)
- Real-time progress tracking during extraction
- Browse button for easy output directory selection

## ✨ Features

- 🔍 **Auto-detection** of connected iPod devices across macOS, Linux, and Windows
- 📊 **Database parsing** for complete track metadata and playlists from iTunesDB
- 🎵 **Direct file scanning** with metadata extraction when database is empty or corrupted
- 📁 **Multiple export formats**:
  - CSV (Soundiiz compatible for playlist migration)
  - JSON (complete metadata preservation)
  - M3U/M3U8 (standard playlist format)
  - Text summary (artist and playlist statistics)
- 🎨 **Dual interfaces**:
  - Beautiful terminal UI (TUI) with rich menus and progress bars
  - Desktop GUI with real-time extraction progress
- 🚀 **High performance** - handles 12,000+ song collections efficiently
- 🧪 **Battle-tested** - 74+ unit tests ensuring reliability
- 🔄 **Progress tracking** - real-time updates during long operations
- 🛡️ **Error resilient** - handles corrupted files and continues extraction

## Project Structure

```
iPodyssey/
├── ipodyssey/
│   ├── main.py             # TUI interface with rich menus
│   ├── gui.py              # Desktop GUI interface
│   ├── gui_progress.py     # GUI progress window
│   ├── scanner.py          # Direct music file scanning
│   ├── copier.py           # iPod detection and file copying
│   ├── explorer.py         # File system mapping
│   ├── extractor.py        # Music file extraction
│   ├── metadata.py         # ID3/AAC metadata reader
│   ├── cli.py              # CLI entry point
│   ├── database/
│   │   ├── parser.py       # iTunesDB binary parser
│   │   ├── structures.py   # Track/Playlist structures
│   │   ├── playlist.py     # Playlist reconstruction
│   │   └── debug_parser.py # Database debugging tools
│   └── exporters/
│       ├── spotify.py      # Spotify CSV format
│       ├── youtube.py      # YouTube Music format
│       └── m3u.py          # Standard M3U playlists
├── tests/                  # Comprehensive test suite
│   ├── test_scanner.py     # Scanner tests (12 tests)
│   ├── test_main.py        # TUI tests (18 tests)
│   ├── test_parser.py      # Database parser tests (13 tests)
│   ├── test_copier.py      # iPod detection tests (17 tests)
│   ├── test_gui_logic.py   # GUI logic tests (14 tests)
│   └── test_explorer.py    # Explorer placeholder
└── data/
    └── local_copy/         # Local iPod data copy
```

## Installation

### Prerequisites
- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- USB connection to iPod

### Setup with uv (recommended)

#### macOS/Linux
```bash
# Create virtual environment
uv venv

# Install in development mode
uv pip install -e .

# Run directly with uv
uv run python -m ipodyssey
```

#### Windows
```powershell
# Create virtual environment
uv venv

# Install in development mode
uv pip install -e .

# Run directly with uv
uv run python -m ipodyssey
```

### Setup with pip

#### macOS/Linux
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .

# Run the tool
python -m ipodyssey
```

#### Windows
```powershell
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -e .

# Run the tool
python -m ipodyssey
```

## iPod Video Structure Notes

The iPod Video uses an obfuscated file system:
- Music files: `/iPod_Control/Music/F00-F49/` with names like `ABCD.mp3`
- Database: `/iPod_Control/iTunes/iTunesDB` (binary format)
- Artwork: `/iPod_Control/Artwork/ArtworkDB`
- All metadata and playlists stored in iTunesDB

## Development with Jujutsu

This project uses Jujutsu (jj) for version control:

```bash
# Check status
jj st

# Create new change
jj new -m "Description of change"

# Update current change description
jj describe -m "Updated description"

# View change history
jj log
```

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/lavabyrd/iPodyssey.git
cd iPodyssey
uv venv
uv pip install -e .

# Run Terminal UI
uv run python -m ipodyssey

# Run Desktop GUI
uv run python -m ipodyssey.gui
```

The app will guide you through:
1. **Connect your iPod** via USB
2. **Auto-detection** finds your device
3. **Choose extraction mode** - Database, file scan, or both
4. **Select export format** - CSV, JSON, M3U, or text
5. **Extract** your music and playlists

### System Requirements

- **Python**: 3.13+ required
- **iPod**: Classic models (Video, Photo, Mini, Nano)
- **Format**: FAT32 formatted iPods work best

### Platform Notes

**macOS**
- iPods mount at `/Volumes/IPOD_NAME`
- Install Python via Homebrew: `brew install python@3.13`

**Windows**
- iPods appear as drive letters (e.g., `E:\`)
- Enable disk mode on iPod if not detected

**Linux**
- iPods mount at `/media/username/IPOD_NAME`
- Install tkinter: `sudo apt install python3-tk` (Ubuntu/Debian)

## 🧪 Testing

iPodyssey includes a comprehensive test suite with 74+ tests covering all major functionality:

### Running Tests
```bash
# Run all tests
uv run pytest tests/

# Run with coverage report
uv run pytest tests/ --cov=ipodyssey --cov-report=html

# Run specific test file
uv run pytest tests/test_scanner.py

# Run tests with verbose output
uv run pytest tests/ -v
```

### Test Coverage
- **Scanner Module**: 12 tests for MP3/M4A metadata extraction, progress callbacks
- **Main TUI**: 18 tests for interface flows and user interactions
- **Database Parser**: 13 tests for iTunesDB parsing and data structures
- **iPod Detection**: 17 tests for device detection across platforms
- **GUI Logic**: 14 tests for business logic without display dependencies

## 🖥️ GUI Version

iPodyssey includes a desktop GUI for users who prefer a graphical interface:

### Running the GUI
```bash
# With uv
uv run python -m ipodyssey.gui

# Or with activated venv
python -m ipodyssey.gui
```

### Building Standalone Executable

Create a standalone executable that users can run without Python installed:

```bash
# Install PyInstaller
pip install pyinstaller

# Build the executable
python build.py

# Find your executable in the 'dist' folder
```

#### Platform-specific outputs:
- **Windows**: `dist/iPodyssey.exe` - Single executable file
- **macOS**: `dist/iPodyssey.app` - Application bundle
- **Linux**: `dist/iPodyssey` - Single binary file

### Creating Installers

#### Windows
Use [Inno Setup](https://jrsoftware.org/isinfo.php) or [NSIS](https://nsis.sourceforge.io/) to create a proper Windows installer.

#### macOS
Create a DMG disk image:
```bash
brew install create-dmg
create-dmg --volname "iPodyssey" --window-size 600 400 \
  --app-drop-link 450 200 "iPodyssey.dmg" "dist/iPodyssey.app"
```

#### Linux
Create an AppImage for universal Linux compatibility:
```bash
# See https://appimage.org/ for AppImageKit setup
```
