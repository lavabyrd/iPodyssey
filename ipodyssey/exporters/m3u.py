"""
M3U/M3U8 playlist exporter for universal compatibility.

M3U is the most widely supported playlist format:
- Simple text format
- Supports extended info (#EXTINF)
- Works with VLC, Winamp, most players

Functions to implement:
- export_m3u(): Create basic M3U playlist
- export_m3u_extended(): Include track duration and title
- create_relative_paths(): Make portable playlists
"""