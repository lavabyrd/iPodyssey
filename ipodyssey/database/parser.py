"""
iTunesDB binary parser - the heart of iPod data structure.

The iTunesDB is a binary file with a specific structure:
- Headers marked with 4-byte signatures (mhbd, mhsd, mhit, etc.)
- Little-endian byte ordering
- Nested structure with size fields

Key database sections:
- mhbd: Main database header
- mhsd: Dataset (tracks or playlists)
- mhit: Track item with all metadata
- mhyp: Playlist header
- mhip: Playlist item (track reference)

Functions to implement:
- parse_database(): Main parser entry point
- read_header(): Parse 4-byte header signatures
- parse_track(): Extract track information
- parse_playlist(): Extract playlist structure
- decode_string(): Handle Unicode strings in database

This reveals how iTunes/iPod actually stores your music metadata!
"""