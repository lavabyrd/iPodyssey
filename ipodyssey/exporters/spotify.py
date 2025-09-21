"""
Spotify playlist exporter.

Spotify doesn't have a direct playlist import, but we can:
1. Export to CSV format for Spotify playlist tools
2. Generate search queries for tracks
3. Create format compatible with spotifytools

Export format:
- Track name
- Artist
- Album
- Duration
- ISRC (if available)

Functions to implement:
- export_spotify_csv(): Create CSV for third-party tools
- generate_search_queries(): Create Spotify search strings
- format_duration(): Convert milliseconds to readable format
"""