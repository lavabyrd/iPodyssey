"""
Minimal database copier for iPod metadata extraction.

This module:
1. Detects mounted iPod devices
2. Copies only essential database files (not music)
3. Verifies database integrity
4. Provides info about the iPod's music library

Since we're using Soundiiz for playlist import, we only need
the iTunesDB file which contains all metadata and playlists.
"""

import os
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Tuple


def detect_ipod(mount_path: str = "/Volumes/SPLINTER'S") -> Optional[str]:
    """
    Detect if an iPod is mounted and has valid database files.

    Returns:
        Path to iPod mount point if found, None otherwise
    """
    if not os.path.exists(mount_path):
        print(f"❌ No volume mounted at {mount_path}")
        return None

    itunes_db_path = os.path.join(mount_path, "iPod_Control", "iTunes", "iTunesDB")

    if not os.path.exists(itunes_db_path):
        print(f"❌ No iTunesDB found at {mount_path}")
        print("   This might not be an iPod or the database is missing")
        return None

    print(f"✅ Found iPod at: {mount_path}")

    # Get some basic info about the database
    db_size = os.path.getsize(itunes_db_path)
    db_modified = datetime.fromtimestamp(os.path.getmtime(itunes_db_path))

    print(f"   Database size: {db_size / (1024*1024):.2f} MB")
    print(f"   Last synced: {db_modified.strftime('%Y-%m-%d %H:%M:%S')}")

    # Check for other iPod indicators
    ipod_control = os.path.join(mount_path, "iPod_Control")
    if os.path.exists(ipod_control):
        subdirs = os.listdir(ipod_control)
        print(f"   iPod_Control contents: {', '.join(subdirs)}")

    return mount_path


def copy_database_files(ipod_path: str, destination: str) -> Dict[str, str]:
    """
    Copy only the essential database files from iPod.

    Args:
        ipod_path: Mount path of the iPod
        destination: Where to copy the database files

    Returns:
        Dictionary mapping file types to their copied paths
    """
    # Create destination directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_dir = os.path.join(destination, f"ipod_backup_{timestamp}")
    Path(dest_dir).mkdir(parents=True, exist_ok=True)

    print(f"\n📁 Copying to: {dest_dir}\n")

    # Essential files for metadata and playlists
    files_to_copy = {
        "iTunesDB": "iPod_Control/iTunes/iTunesDB",
        "iTunesPState": "iPod_Control/iTunes/iTunesPState",
        "iTunesSD": "iPod_Control/iTunes/iTunesSD",
        "ArtworkDB": "iPod_Control/Artwork/ArtworkDB",
    }

    copied_files = {}
    total_size = 0

    for file_name, rel_path in files_to_copy.items():
        source_path = os.path.join(ipod_path, rel_path)

        if not os.path.exists(source_path):
            print(f"⏭️  {file_name}: Not found (skipping)")
            continue

        dest_path = os.path.join(dest_dir, file_name)
        file_size = os.path.getsize(source_path)

        print(f"📋 {file_name}: {file_size / 1024:.1f} KB", end="")

        try:
            shutil.copy2(source_path, dest_path)
            copied_files[file_name] = dest_path
            total_size += file_size
            print(" ✅")
        except Exception as e:
            print(f" ❌ Failed: {e}")

    print(f"\n✨ Copied {len(copied_files)} files ({total_size / (1024*1024):.2f} MB total)")
    return copied_files


def verify_database_integrity(db_path: str) -> Tuple[bool, str]:
    """
    Verify the iTunesDB file is valid and readable.

    Args:
        db_path: Path to iTunesDB file

    Returns:
        Tuple of (is_valid, info_message)
    """
    if not os.path.exists(db_path):
        return False, "File not found"

    try:
        with open(db_path, 'rb') as f:
            # iTunesDB files start with 'mhbd' (main header binary data)
            header = f.read(4)
            if header != b'mhbd':
                return False, f"Invalid header: {header}"

            # Read header size (next 4 bytes)
            f.read(4)  # header size

            # Read total size (next 4 bytes)
            total_size_bytes = f.read(4)
            total_size = int.from_bytes(total_size_bytes, byteorder='little')

            # Get actual file size
            f.seek(0, 2)  # Seek to end
            actual_size = f.tell()

            # Calculate MD5 for integrity check
            f.seek(0)
            md5 = hashlib.md5()
            while chunk := f.read(8192):
                md5.update(chunk)
            checksum = md5.hexdigest()

            return True, f"Valid iTunesDB (size: {actual_size:,} bytes, MD5: {checksum[:8]}...)"

    except Exception as e:
        return False, f"Error reading file: {e}"


def get_ipod_info(ipod_path: str) -> Dict[str, any]:
    """
    Extract basic information about the iPod and its contents.

    Args:
        ipod_path: Mount path of the iPod

    Returns:
        Dictionary with iPod information
    """
    info = {
        "mount_path": ipod_path,
        "name": os.path.basename(ipod_path),
        "database_found": False,
        "music_folders": 0,
        "total_size": 0,
    }

    # Check for music folders (F00-F49)
    music_path = os.path.join(ipod_path, "iPod_Control", "Music")
    if os.path.exists(music_path):
        music_folders = [d for d in os.listdir(music_path) if d.startswith("F")]
        info["music_folders"] = len(music_folders)

        # Count total music files (optional)
        total_files = 0
        for folder in music_folders:
            folder_path = os.path.join(music_path, folder)
            if os.path.isdir(folder_path):
                total_files += len(os.listdir(folder_path))
        info["total_music_files"] = total_files

    # Check database
    db_path = os.path.join(ipod_path, "iPod_Control", "iTunes", "iTunesDB")
    if os.path.exists(db_path):
        info["database_found"] = True
        info["database_size"] = os.path.getsize(db_path)

    return info


def main():
    """Main function to run the copier."""
    print("🎵 iPodyssey - Database Copier\n")
    print("=" * 40)

    # Detect iPod
    ipod_path = detect_ipod()
    if not ipod_path:
        print("\n💡 Make sure your iPod is mounted and accessible.")
        return 1

    # Get iPod info
    print("\n📊 iPod Statistics:")
    info = get_ipod_info(ipod_path)
    print(f"   Music folders: {info['music_folders']}")
    if info.get('total_music_files'):
        print(f"   Total music files: {info['total_music_files']:,}")

    # Copy database files
    print("\n" + "=" * 40)
    destination = "./data/local_copy"
    copied_files = copy_database_files(ipod_path, destination)

    # Verify the main database
    if "iTunesDB" in copied_files:
        print("\n🔍 Verifying database integrity...")
        is_valid, message = verify_database_integrity(copied_files["iTunesDB"])
        if is_valid:
            print(f"   ✅ {message}")
        else:
            print(f"   ❌ {message}")
            return 1

    print("\n✨ Success! Database files are ready for parsing.")
    print(f"   Next step: Run the parser to extract playlists")

    return 0


if __name__ == "__main__":
    exit(main())