"""
CLI interface for iPodyssey using Click.

Main commands:
- copy: Copy iPod data to local directory
- explore: Analyze iPod file structure
- extract: Extract music files with proper names
- parse: Parse iTunesDB and show info
- export: Export playlists to various formats

Each command should:
- Show progress with rich
- Handle errors gracefully
- Provide detailed output when verbose

Example usage:
$ ipodyssey copy /Volumes/IPOD ./data/
$ ipodyssey explore ./data/
$ ipodyssey parse ./data/iPod_Control/iTunes/iTunesDB
$ ipodyssey export ./data/ --format spotify --output playlists/
"""