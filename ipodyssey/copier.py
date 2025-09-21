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


def detect_ipod(mount_path: str = None) -> Optional[str]:
    """
    Detect if an iPod is mounted and has valid database files.

    Args:
        mount_path: Optional specific path to check

    Returns:
        Path to iPod mount point if found, None otherwise
    """
    if mount_path is None:
        # Auto-detect iPod in common locations based on platform
        import sys

        if sys.platform == "darwin":  # macOS
            if os.path.exists('/Volumes'):
                for volume in os.listdir('/Volumes'):
                    volume_path = os.path.join('/Volumes', volume)
                    if os.path.exists(os.path.join(volume_path, 'iPod_Control')):
                        mount_path = volume_path
                        break

        elif sys.platform.startswith("linux"):  # Linux
            # Check /media/username/
            if os.path.exists('/media'):
                for user_dir in os.listdir('/media'):
                    user_path = os.path.join('/media', user_dir)
                    if os.path.isdir(user_path):
                        for mount in os.listdir(user_path):
                            mount_path_check = os.path.join(user_path, mount)
                            if os.path.exists(os.path.join(mount_path_check, 'iPod_Control')):
                                mount_path = mount_path_check
                                break
                    if mount_path:
                        break

            # Also check /mnt/ if not found
            if mount_path is None and os.path.exists('/mnt'):
                for mount in os.listdir('/mnt'):
                    mount_path_check = os.path.join('/mnt', mount)
                    if os.path.exists(os.path.join(mount_path_check, 'iPod_Control')):
                        mount_path = mount_path_check
                        break

        elif sys.platform == "win32":  # Windows
            import string
            for drive_letter in string.ascii_uppercase:
                drive_path = f"{drive_letter}:\\"
                if os.path.exists(drive_path):
                    if os.path.exists(os.path.join(drive_path, 'iPod_Control')):
                        mount_path = drive_path
                        break

        if mount_path is None:
            print("❌ No iPod detected")
            return None

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


def detect_ipod_model(ipod_path: str) -> str:
    """
    Detect the iPod model from multiple sources.

    Args:
        ipod_path: Mount path of the iPod

    Returns:
        String describing the iPod model
    """
    detected_model = None

    # First check ExtendedSysInfoXml for more reliable info
    extended_info_path = os.path.join(ipod_path, "iPod_Control", "Device", "ExtendedSysInfoXml")
    if os.path.exists(extended_info_path):
        try:
            with open(extended_info_path, 'r') as f:
                content = f.read()
                # Look for capacity and features
                if 'VideoCodecs' in content or 'Video' in content:
                    # Has video capability
                    if '80GB' in content or '80000' in content:
                        return 'iPod Video (5th gen, 80GB)'
                    elif '60GB' in content or '60000' in content:
                        return 'iPod Video (5th gen, 60GB)'
                    elif '30GB' in content or '30000' in content:
                        return 'iPod Video (5th gen, 30GB)'
        except Exception:
            pass

    # Check capacity from mount info if available
    try:
        stat_info = os.statvfs(ipod_path)
        total_bytes = stat_info.f_blocks * stat_info.f_frsize
        total_gb = total_bytes / (1024**3)

        # Check for video folders to confirm Video model
        video_path = os.path.join(ipod_path, "iPod_Control", "Video")
        photos_path = os.path.join(ipod_path, "Photos")

        if os.path.exists(video_path) or os.path.exists(photos_path):
            if 70 < total_gb < 85:
                return 'iPod Video (5th gen, 80GB)'
            elif 55 < total_gb < 65:
                return 'iPod Video (5th gen, 60GB)'
            elif 25 < total_gb < 35:
                return 'iPod Video (5th gen, 30GB)'
    except Exception:
        pass

    # Fallback to SysInfo file (might be corrupted)
    sysinfo_path = os.path.join(ipod_path, "iPod_Control", "Device", "SysInfo")
    if os.path.exists(sysinfo_path):
        try:
            with open(sysinfo_path, 'r') as f:
                content = f.read()
                # Parse model info
                for line in content.split('\n'):
                    if 'ModelNumStr' in line:
                        model = line.split(':', 1)[1].strip()
                        # Map model numbers to names
                        model_map = {
                            'MA002': 'iPod (1st gen) [SysInfo may be incorrect]',
                            'MA003': 'iPod (2nd gen)',
                            'MA079': 'iPod (3rd gen)',
                            'MA099': 'iPod (4th gen)',
                            'MA444': 'iPod Video (5th gen, 30GB)',
                            'MA446': 'iPod Video (5th gen, 60GB)',
                            'MA448': 'iPod Video (5th gen, 80GB)',
                            'MA450': 'iPod Video (5.5 gen, 30GB)',
                            'MA452': 'iPod Video (5.5 gen, 80GB)',
                            'MA350': 'iPod Nano (1st gen)',
                            'MA477': 'iPod Nano (2nd gen)',
                            'MA978': 'iPod Nano (3rd gen)',
                            'MB903': 'iPod Nano (4th gen)',
                            'MC027': 'iPod Nano (5th gen)',
                            'MC525': 'iPod Nano (6th gen)',
                            'MD478': 'iPod Nano (7th gen)',
                            'MA127': 'iPod Mini (1st gen)',
                            'MA051': 'iPod Mini (2nd gen)',
                            'MA107': 'iPod Shuffle (1st gen)',
                            'MA953': 'iPod Shuffle (2nd gen)',
                            'MB683': 'iPod Shuffle (3rd gen)',
                            'MC164': 'iPod Shuffle (4th gen)',
                            'MB029': 'iPod Touch (1st gen)',
                            'MC086': 'iPod Touch (2nd gen)',
                            'MB150': 'iPod Classic (80GB)',
                            'MB145': 'iPod Classic (160GB)',
                            'MB562': 'iPod Classic (120GB)',
                            'MB565': 'iPod Classic (160GB thin)',
                        }
                        return model_map.get(model, f'iPod (Model: {model})')
                    elif 'VisibleBuildID' in line:
                        build_id = line.split(':', 1)[1].strip()
                        # Identify by build ID patterns
                        if '5G' in build_id or '5.0' in build_id:
                            return 'iPod Video (5th gen)'
                        elif '6G' in build_id or '6.0' in build_id:
                            return 'iPod Classic'
                        elif '3G' in build_id or '3.0' in build_id:
                            return 'iPod (3rd gen)'
        except Exception:
            pass

    # Check for iPod_Control structure to guess generation
    music_path = os.path.join(ipod_path, "iPod_Control", "Music")
    if os.path.exists(music_path):
        folders = [d for d in os.listdir(music_path) if d.startswith("F")]
        if len(folders) == 50:  # F00-F49
            # Check database size as a hint
            db_path = os.path.join(ipod_path, "iPod_Control", "iTunes", "iTunesDB")
            if os.path.exists(db_path):
                size_mb = os.path.getsize(db_path) / (1024 * 1024)
                if size_mb > 10:
                    return 'iPod Classic or Video (large capacity)'
                else:
                    return 'iPod (classic structure)'

    return 'iPod (Unknown model)'


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
        "model": detect_ipod_model(ipod_path),
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