"""
Scanner to catalog music files directly from iPod without using iTunesDB.

This is useful when the database is empty but music files exist.
"""

import os
from pathlib import Path
from typing import List, Dict
import mutagen
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.id3 import ID3


def scan_ipod_music(ipod_path: str, progress_callback=None) -> List[Dict[str, any]]:
    """
    Scan iPod Music folders and extract metadata directly from files.

    Args:
        ipod_path: Path to mounted iPod
        progress_callback: Optional callback function(current, total, message)

    Returns:
        List of track dictionaries with metadata
    """
    music_path = Path(ipod_path) / "iPod_Control" / "Music"

    if not music_path.exists():
        print(f"❌ Music folder not found at {music_path}")
        return []

    tracks = []
    total_files = 0

    # First, count total files for progress
    folders = [f for f in music_path.iterdir() if f.is_dir() and f.name.startswith("F")]

    if progress_callback:
        progress_callback(0, 0, "Counting music files...")

    file_list = []
    for folder in folders:
        for file_path in folder.iterdir():
            if file_path.suffix.lower() in ['.mp3', '.m4a', '.mp4', '.aac']:
                file_list.append((folder, file_path))

    total_to_scan = len(file_list)

    if progress_callback:
        progress_callback(0, total_to_scan, f"Found {total_to_scan} files to scan")

    # Scan all files
    for idx, (folder, file_path) in enumerate(file_list):
        if progress_callback and idx % 10 == 0:  # Update every 10 files
            progress_callback(idx, total_to_scan,
                            f"Scanning {folder.name}/{file_path.name}")

        total_files += 1

        try:
            # Extract metadata using mutagen
            audio = mutagen.File(file_path)

            if audio is None:
                continue

            track = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'folder': folder.name,
                'format': file_path.suffix[1:].upper(),
                'file_size': file_path.stat().st_size,
            }

            # Extract common tags
            if isinstance(audio, MP3):
                # MP3 with ID3 tags
                track['artist'] = str(audio.get('TPE1', ['Unknown'])[0])
                track['title'] = str(audio.get('TIT2', [file_path.stem])[0])
                track['album'] = str(audio.get('TALB', ['Unknown'])[0])
                track['date'] = str(audio.get('TDRC', [''])[0])
                track['genre'] = str(audio.get('TCON', [''])[0])
                track['track_number'] = str(audio.get('TRCK', [''])[0])
            elif isinstance(audio, MP4):
                # M4A/AAC with MP4 tags
                track['artist'] = audio.get('©ART', ['Unknown'])[0]
                track['title'] = audio.get('©nam', [file_path.stem])[0]
                track['album'] = audio.get('©alb', ['Unknown'])[0]
                track['date'] = str(audio.get('©day', [''])[0])
                track['genre'] = audio.get('©gen', [''])[0]
                track['track_number'] = str(audio.get('trkn', [('', '')])[0][0])
            else:
                # Generic tags
                track['artist'] = audio.get('artist', ['Unknown'])[0] if 'artist' in audio else 'Unknown'
                track['title'] = audio.get('title', [file_path.stem])[0] if 'title' in audio else file_path.stem
                track['album'] = audio.get('album', ['Unknown'])[0] if 'album' in audio else 'Unknown'

            # Get audio properties
            if hasattr(audio.info, 'length'):
                track['duration'] = int(audio.info.length * 1000)  # Convert to milliseconds
                minutes = int(audio.info.length // 60)
                seconds = int(audio.info.length % 60)
                track['duration_string'] = f"{minutes}:{seconds:02d}"

            if hasattr(audio.info, 'bitrate'):
                track['bitrate'] = audio.info.bitrate

            if hasattr(audio.info, 'sample_rate'):
                track['sample_rate'] = audio.info.sample_rate

            tracks.append(track)

        except Exception as e:
            if progress_callback and idx % 100 == 0:
                progress_callback(idx, total_to_scan,
                                f"Error reading {file_path.name}: {e}")
            continue

    if progress_callback:
        progress_callback(total_to_scan, total_to_scan,
                        f"Completed! Scanned {len(tracks)} valid files")

    print(f"\n✅ Found {len(tracks)} valid music files out of {total_files} total files")
    return tracks


def export_to_csv(tracks: List[Dict], output_path: str):
    """Export tracks to CSV format for Soundiiz."""
    import csv

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Soundiiz-compatible header
        writer.writerow(['Title', 'Artist', 'Album', 'Duration'])

        for track in tracks:
            writer.writerow([
                track.get('title', 'Unknown'),
                track.get('artist', 'Unknown'),
                track.get('album', 'Unknown'),
                track.get('duration_string', '0:00')
            ])

    print(f"📝 Exported {len(tracks)} tracks to {output_path}")


def main():
    """Main function to scan iPod."""
    import sys

    # Auto-detect iPod or use command line argument
    if len(sys.argv) > 1:
        ipod_path = sys.argv[1]
    else:
        # Auto-detect based on platform
        ipod_path = None

        if sys.platform == "darwin":  # macOS
            if os.path.exists('/Volumes'):
                for volume in os.listdir('/Volumes'):
                    volume_path = os.path.join('/Volumes', volume)
                    if os.path.exists(os.path.join(volume_path, 'iPod_Control')):
                        ipod_path = volume_path
                        break

        elif sys.platform.startswith("linux"):  # Linux
            # Check /media/username/
            if os.path.exists('/media'):
                for user_dir in os.listdir('/media'):
                    user_path = os.path.join('/media', user_dir)
                    if os.path.isdir(user_path):
                        for mount in os.listdir(user_path):
                            mount_path = os.path.join(user_path, mount)
                            if os.path.exists(os.path.join(mount_path, 'iPod_Control')):
                                ipod_path = mount_path
                                break
                    if ipod_path:
                        break

            # Also check /mnt/
            if ipod_path is None and os.path.exists('/mnt'):
                for mount in os.listdir('/mnt'):
                    mount_path = os.path.join('/mnt', mount)
                    if os.path.exists(os.path.join(mount_path, 'iPod_Control')):
                        ipod_path = mount_path
                        break

        elif sys.platform == "win32":  # Windows
            import string
            for drive_letter in string.ascii_uppercase:
                drive_path = f"{drive_letter}:\\"
                if os.path.exists(drive_path):
                    if os.path.exists(os.path.join(drive_path, 'iPod_Control')):
                        ipod_path = drive_path
                        break

    if not ipod_path or not os.path.exists(ipod_path):
        print(f"❌ iPod not found at {ipod_path}")
        return

    print("🎵 iPodyssey Music Scanner")
    print("=" * 40)
    print(f"📱 Scanning iPod at: {ipod_path}\n")

    # Scan music files
    tracks = scan_ipod_music(ipod_path)

    if tracks:
        # Show sample tracks
        print("\n🎵 Sample Tracks:")
        for track in tracks[:10]:
            print(f"  {track.get('artist', 'Unknown')} - {track.get('title', 'Unknown')}")
            print(f"    Album: {track.get('album', 'Unknown')}")
            print(f"    File: {track.get('file_name', 'Unknown')}")
            print()

        # Export to CSV
        output_path = "ipod_music_catalog.csv"
        export_to_csv(tracks, output_path)

        # Group by artist
        artists = {}
        for track in tracks:
            artist = track.get('artist', 'Unknown')
            if artist not in artists:
                artists[artist] = []
            artists[artist].append(track)

        print(f"\n📊 Summary:")
        print(f"  Total tracks: {len(tracks)}")
        print(f"  Total artists: {len(artists)}")
        print(f"  Top artists:")
        for artist, songs in sorted(artists.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
            print(f"    {artist}: {len(songs)} tracks")


if __name__ == "__main__":
    main()