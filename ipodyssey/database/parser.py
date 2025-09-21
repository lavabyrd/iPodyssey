"""
iTunesDB binary parser - the heart of iPod data extraction.

The iTunesDB uses a hierarchical structure with 4-byte signatures:
- mhbd: Main database header
- mhsd: Dataset (contains either tracks or playlists)
- mhlt: Track list header
- mhit: Track item (individual song)
- mhlp: Playlist list header
- mhyp: Playlist header
- mhip: Playlist item (track reference)

All multi-byte integers are little-endian.
"""

import struct
from typing import Dict, List, Any, BinaryIO, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Track:
    """Represents a single track from the iTunesDB."""
    id: int
    title: str = ""
    artist: str = ""
    album: str = ""
    genre: str = ""
    file_path: str = ""
    file_size: int = 0
    total_time_ms: int = 0
    track_number: int = 0
    track_count: int = 0
    year: int = 0
    bitrate: int = 0
    sample_rate: int = 0
    play_count: int = 0
    last_played: Optional[datetime] = None
    date_added: Optional[datetime] = None
    rating: int = 0
    bpm: int = 0
    compilation: bool = False
    file_type: str = ""

    @property
    def duration_string(self) -> str:
        """Convert milliseconds to MM:SS format."""
        if self.total_time_ms:
            seconds = self.total_time_ms // 1000
            minutes = seconds // 60
            seconds = seconds % 60
            return f"{minutes}:{seconds:02d}"
        return "0:00"


@dataclass
class Playlist:
    """Represents a playlist from the iTunesDB."""
    id: int
    name: str
    track_ids: List[int] = field(default_factory=list)
    is_smart: bool = False
    timestamp: Optional[datetime] = None


class DatabaseParser:
    """Parser for iPod iTunesDB binary format."""

    # iTunes epoch starts at January 1, 1904 (Mac HFS+ epoch)
    ITUNES_EPOCH_OFFSET = 2082844800  # Seconds between 1904 and 1970

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.tracks: Dict[int, Track] = {}
        self.playlists: List[Playlist] = []
        self.file_handle: Optional[BinaryIO] = None

    def parse(self) -> Tuple[Dict[int, Track], List[Playlist]]:
        """
        Parse the entire database and return tracks and playlists.

        Returns:
            Tuple of (tracks_dict, playlists_list)
        """
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        with open(self.db_path, 'rb') as f:
            self.file_handle = f

            # Read main database header
            header = self._read_header()
            if header['signature'] != 'mhbd':
                raise ValueError(f"Invalid database signature: {header['signature']}")

            print(f"📚 Parsing iTunesDB v{header.get('version', 'unknown')}")

            # Read datasets
            self._parse_datasets(header['header_size'])

        print(f"✅ Parsed {len(self.tracks)} tracks and {len(self.playlists)} playlists")
        return self.tracks, self.playlists

    def _read_header(self) -> Dict[str, Any]:
        """Read a standard iTunes database header."""
        # All headers follow: signature(4) + header_size(4) + total_size(4)
        signature = self.file_handle.read(4).decode('ascii', errors='ignore')
        header_size = struct.unpack('<I', self.file_handle.read(4))[0]
        total_size = struct.unpack('<I', self.file_handle.read(4))[0]

        header = {
            'signature': signature,
            'header_size': header_size,
            'total_size': total_size
        }

        # Read version info if this is main header
        if signature == 'mhbd':
            version = struct.unpack('<I', self.file_handle.read(4))[0]
            header['version'] = version
            # Skip remaining header bytes
            self.file_handle.read(header_size - 16)

        return header

    def _parse_datasets(self, offset: int):
        """Parse all datasets (track list and playlist list)."""
        self.file_handle.seek(offset)

        while True:
            pos = self.file_handle.tell()

            # Check if we have enough data
            sig = self.file_handle.read(4)
            if len(sig) < 4:
                break

            self.file_handle.seek(pos)

            # Read dataset header
            signature = sig.decode('ascii', errors='ignore')
            if signature != 'mhsd':
                break

            dataset = self._read_header()

            # Determine dataset type
            self.file_handle.seek(pos + dataset['header_size'])
            next_sig = self.file_handle.read(4).decode('ascii', errors='ignore')
            self.file_handle.seek(pos + dataset['header_size'])

            if next_sig == 'mhla':
                # Album list - skip for now
                print(f"  Found album list (skipping)")
            elif next_sig == 'mhlt':
                # Track list
                self._parse_track_list()
            elif next_sig == 'mhlp':
                # Playlist list
                self._parse_playlist_list()
            else:
                print(f"  Unknown dataset type: {next_sig}")

            # Move to next dataset
            self.file_handle.seek(pos + dataset['total_size'])

    def _parse_track_list(self):
        """Parse the track list section."""
        start_pos = self.file_handle.tell()
        header = self._read_header()
        if header['signature'] != 'mhlt':
            print(f"  Expected mhlt, got {header['signature']}")
            return

        # Read track count (4 bytes after header)
        data = self.file_handle.read(4)
        if len(data) >= 4:
            track_count = struct.unpack('<I', data)[0]
            print(f"  Found track list with {track_count} tracks")
        else:
            print(f"  Failed to read track count")
            return

        # Skip rest of header
        remaining = header['header_size'] - 16  # Already read 12 + 4
        if remaining > 0:
            self.file_handle.read(remaining)

        # Parse each track (show progress for large collections)
        for i in range(min(track_count, 10000)):  # Safety limit
            if i % 100 == 0 and i > 0:
                print(f"    Parsing track {i}/{track_count}...")

            track = self._parse_track()
            if track:
                self.tracks[track.id] = track
            else:
                print(f"    Failed to parse track {i+1}")
                break

    def _parse_track(self) -> Optional[Track]:
        """Parse a single track entry."""
        start_pos = self.file_handle.tell()
        header = self._read_header()

        if header['signature'] != 'mhit':
            return None

        # Track data structure (partial - most important fields)
        data = self.file_handle.read(min(header['header_size'] - 12, 400))

        # Parse fixed fields
        track = Track(
            id=struct.unpack('<I', data[4:8])[0] if len(data) > 8 else 0,
            total_time_ms=struct.unpack('<I', data[12:16])[0] if len(data) > 16 else 0,
            file_size=struct.unpack('<I', data[16:20])[0] if len(data) > 20 else 0,
        )

        # More fields at specific offsets
        if len(data) > 36:
            track.bitrate = struct.unpack('<I', data[32:36])[0]
        if len(data) > 40:
            track.sample_rate = struct.unpack('<I', data[36:40])[0]
        if len(data) > 48:
            track.track_number = struct.unpack('<I', data[44:48])[0]
        if len(data) > 52:
            track.track_count = struct.unpack('<I', data[48:52])[0]
        if len(data) > 56:
            track.year = struct.unpack('<I', data[52:56])[0]
        if len(data) > 84:
            track.play_count = struct.unpack('<I', data[80:84])[0]

        # Parse timestamps (iTunes epoch)
        if len(data) > 92:
            added_time = struct.unpack('<I', data[88:92])[0]
            if added_time:
                track.date_added = self._convert_itunes_timestamp(added_time)

        # Move to track details (strings)
        self.file_handle.seek(start_pos + header['header_size'])

        # Parse string sections (mhod)
        track_end = start_pos + header['total_size']
        while self.file_handle.tell() < track_end:
            string_data = self._parse_string_section()
            if string_data:
                string_type, text = string_data
                if string_type == 1:
                    track.title = text
                elif string_type == 2:
                    track.file_path = text
                elif string_type == 3:
                    track.album = text
                elif string_type == 4:
                    track.artist = text
                elif string_type == 5:
                    track.genre = text
            else:
                break

        self.file_handle.seek(track_end)
        return track

    def _parse_string_section(self) -> Optional[Tuple[int, str]]:
        """Parse a string section (mhod)."""
        pos = self.file_handle.tell()
        sig = self.file_handle.read(4)

        if len(sig) < 4 or sig != b'mhod':
            self.file_handle.seek(pos)
            return None

        header_size = struct.unpack('<I', self.file_handle.read(4))[0]
        total_size = struct.unpack('<I', self.file_handle.read(4))[0]
        string_type = struct.unpack('<I', self.file_handle.read(4))[0]

        # Skip to string data
        self.file_handle.read(16)  # Skip padding

        string_length = struct.unpack('<I', self.file_handle.read(4))[0]
        encoding = struct.unpack('<I', self.file_handle.read(4))[0]

        # Read string bytes
        if string_length > 0 and string_length < 10000:  # Sanity check
            string_bytes = self.file_handle.read(string_length)
            # Decode based on encoding flag
            if encoding == 1:  # UTF-16
                text = string_bytes.decode('utf-16-le', errors='ignore').rstrip('\x00')
            else:  # UTF-8
                text = string_bytes.decode('utf-8', errors='ignore').rstrip('\x00')
        else:
            text = ""

        # Move to end of this section
        self.file_handle.seek(pos + total_size)
        return (string_type, text)

    def _parse_playlist_list(self):
        """Parse the playlist list section."""
        header = self._read_header()
        if header['signature'] != 'mhlp':
            return

        playlist_count = struct.unpack('<I', self.file_handle.read(4))[0]
        print(f"  Found {playlist_count} playlists in this section")

        # Skip rest of header
        self.file_handle.read(header['header_size'] - 16)

        # Parse each playlist
        for i in range(min(playlist_count, 100)):  # Limit for safety
            playlist = self._parse_playlist()
            if playlist:  # Keep all playlists, even empty ones
                self.playlists.append(playlist)
                if playlist.name:
                    print(f"    Playlist: {playlist.name} ({len(playlist.track_ids)} tracks)")

    def _parse_playlist(self) -> Optional[Playlist]:
        """Parse a single playlist."""
        start_pos = self.file_handle.tell()
        header = self._read_header()

        if header['signature'] != 'mhyp':
            return None

        # Read playlist data
        data = self.file_handle.read(min(header['header_size'] - 12, 100))

        playlist = Playlist(
            id=struct.unpack('<I', data[4:8])[0] if len(data) > 8 else 0,
            name=""
        )

        # Track count is at offset 8
        if len(data) > 12:
            track_count = struct.unpack('<I', data[8:12])[0]

        # Move to playlist items
        self.file_handle.seek(start_pos + header['header_size'])

        # First string section should be playlist name
        name_data = self._parse_string_section()
        if name_data:
            _, playlist.name = name_data

        # Parse track references
        playlist_end = start_pos + header['total_size']
        while self.file_handle.tell() < playlist_end:
            pos = self.file_handle.tell()
            sig = self.file_handle.read(4)

            if sig == b'mhip':
                # Playlist item (track reference)
                self.file_handle.seek(pos)
                track_id = self._parse_playlist_item()
                if track_id:
                    playlist.track_ids.append(track_id)
            else:
                break

        self.file_handle.seek(playlist_end)
        return playlist

    def _parse_playlist_item(self) -> Optional[int]:
        """Parse a playlist item (track reference)."""
        start_pos = self.file_handle.tell()
        header = self._read_header()

        if header['signature'] != 'mhip':
            return None

        # Skip to track ID (various fields before it)
        self.file_handle.read(12)  # Skip padding
        track_id = struct.unpack('<I', self.file_handle.read(4))[0]

        # Move to end
        self.file_handle.seek(start_pos + header['total_size'])
        return track_id

    def _convert_itunes_timestamp(self, timestamp: int) -> datetime:
        """Convert iTunes timestamp (seconds since 1904) to datetime."""
        if timestamp:
            unix_timestamp = timestamp - self.ITUNES_EPOCH_OFFSET
            if unix_timestamp > 0:
                return datetime.fromtimestamp(unix_timestamp)
        return None


def main():
    """Test the parser with a real database."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python parser.py <path_to_iTunesDB>")
        return

    db_path = sys.argv[1]
    parser = DatabaseParser(db_path)

    try:
        tracks, playlists = parser.parse()

        # Show sample data
        print(f"\n📊 Database Summary:")
        print(f"  Tracks: {len(tracks)}")
        print(f"  Playlists: {len(playlists)}")

        # Show first few tracks
        print("\n🎵 Sample Tracks:")
        for i, (track_id, track) in enumerate(list(tracks.items())[:5]):
            print(f"  {track.artist} - {track.title}")
            print(f"    Album: {track.album}")
            print(f"    Duration: {track.duration_string}")
            print(f"    Plays: {track.play_count}")
            print()

        # Show playlists
        print("\n📝 Playlists:")
        for playlist in playlists[:10]:
            print(f"  {playlist.name} ({len(playlist.track_ids)} tracks)")

    except Exception as e:
        print(f"❌ Error parsing database: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()