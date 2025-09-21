"""
Database structures for iTunesDB format.

Uses the 'construct' library to define binary structures.
This is like a reverse-engineering blueprint of Apple's format.

Key structures to define:
- DatabaseHeader (mhbd)
- TrackItem (mhit)
- PlaylistHeader (mhyp)
- StringContainer (mhos)

Each structure has:
- Signature (4 bytes)
- Header size
- Total size
- Version info
- Actual data

Example track fields:
- Track ID
- File size
- Total time (milliseconds)
- Track number
- Bitrate
- Sample rate
- Volume adjustment
- File type
- Date added (Mac timestamp)
- Bookmark time
- Play count
- Last played
- Rating
"""