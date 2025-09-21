"""
Metadata reader for audio files using ID3 tags and other formats.

This module extracts:
1. Basic metadata (artist, title, album, year)
2. Technical info (bitrate, duration, format)
3. iTunes-specific tags (play count, rating, added date)
4. Album artwork if embedded

Key functions to implement:
- read_id3_tags(): Extract ID3v2 tags from MP3 files
- read_aac_metadata(): Handle M4A/AAC iTunes files
- extract_artwork(): Save embedded album art
- get_audio_properties(): Duration, bitrate, sample rate

Uses mutagen library for robust metadata extraction.
Handles edge cases like missing tags, corrupted files.
"""