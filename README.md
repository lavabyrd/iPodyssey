# iPodyssey

Extract and understand music data from iPod Video (5th generation) devices.

## Overview

iPodyssey reveals how iPods actually store and organize music data, working with local copies for fast analysis.

## Project Structure

```
iPodyssey/
├── src/
│   ├── copier.py          # Bulk copy from iPod to local
│   ├── explorer.py         # File system mapping
│   ├── extractor.py        # Music file extraction
│   ├── metadata.py         # ID3/AAC metadata reader
│   ├── database/
│   │   ├── parser.py       # iTunesDB binary parser
│   │   ├── structures.py   # Database structures
│   │   └── playlist.py     # Playlist reconstruction
│   ├── exporters/
│   │   ├── spotify.py      # Spotify CSV format
│   │   ├── youtube.py      # YouTube Music format
│   │   └── m3u.py          # Standard M3U playlists
│   └── cli.py              # Main CLI interface
├── tests/                  # Test suite
└── data/
    └── local_copy/         # Local iPod data copy
```

## Setup with uv

```bash
# Create virtual environment with uv
uv venv

# Activate (fish shell)
source .venv/bin/activate.fish

# Install project in development mode
uv pip install -e .

# Or run commands directly without activating
uv run ipodyssey --help
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

## Usage

```bash
# Copy iPod data locally (when iPod mounted at /Volumes/IPOD)
ipodyssey copy /Volumes/IPOD ./data/local_copy

# Explore file structure
ipodyssey explore ./data/local_copy

# Extract all music with metadata
ipodyssey extract ./data/local_copy ./output

# Export playlists
ipodyssey export ./data/local_copy --format spotify
```