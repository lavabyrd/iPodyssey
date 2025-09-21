"""
Music file extractor for cryptic iPod filenames.

This module:
1. Locates all music files in F00-F49 folders
2. Creates a catalog of files with their cryptic names
3. Prepares files for metadata extraction
4. Handles different audio formats (MP3, AAC, Apple Lossless)

Key functions to implement:
- find_all_music_files(): Recursively find audio files
- catalog_files(): Create index of cryptic name -> file path
- detect_format(): Identify audio format by magic bytes
- extract_to_organized(): Copy with meaningful names (after metadata read)

File naming insight:
iPod uses 4-character codes like "ABCD.mp3" to prevent casual browsing.
The actual track info is stored in iTunesDB, linked by these codes.
"""