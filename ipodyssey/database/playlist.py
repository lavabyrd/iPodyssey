"""
Playlist reconstruction from iTunesDB.

This module:
1. Parses playlist definitions from database
2. Maps track IDs to actual files
3. Preserves playlist order and metadata
4. Handles smart playlists (with rules)

Key functions to implement:
- extract_playlists(): Get all playlists from database
- map_tracks_to_files(): Connect database entries to music files
- reconstruct_playlist(): Build playlist with correct order
- parse_smart_rules(): Decode smart playlist criteria

Playlist types:
- Regular playlists (manual track selection)
- Smart playlists (rule-based)
- Podcast playlists
- On-The-Go playlist (created on device)

The magic: Understanding how track IDs in playlists map to
the cryptic filenames in the Music folders.
"""