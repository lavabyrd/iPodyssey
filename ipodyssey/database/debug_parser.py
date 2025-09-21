"""Debug script to understand the actual iTunesDB structure."""

import struct
from pathlib import Path
import sys


def hexdump(data, length=16):
    """Create a hex dump of binary data."""
    result = []
    for i in range(0, len(data), length):
        chunk = data[i:i + length]
        hex_str = ' '.join(f'{b:02x}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        result.append(f'{i:08x}  {hex_str:<48}  {ascii_str}')
    return '\n'.join(result)


def analyze_database(db_path):
    """Analyze the structure of an iTunesDB file."""
    path = Path(db_path)

    if not path.exists():
        print(f"❌ File not found: {db_path}")
        return

    print(f"📁 Analyzing: {db_path}")
    print(f"   Size: {path.stat().st_size:,} bytes\n")

    with open(db_path, 'rb') as f:
        # Read and display first 512 bytes
        data = f.read(512)
        print("First 512 bytes:")
        print(hexdump(data))
        print()

        # Reset and read headers
        f.seek(0)

        # Main header
        sig = f.read(4)
        print(f"Main signature: {sig} ({sig.hex()})")

        if sig == b'mhbd':
            header_size = struct.unpack('<I', f.read(4))[0]
            total_size = struct.unpack('<I', f.read(4))[0]
            version = struct.unpack('<I', f.read(4))[0]

            print(f"  Header size: {header_size}")
            print(f"  Total size: {total_size}")
            print(f"  Version: {version}")
            print()

            # Skip to end of header
            f.seek(header_size)

            # Look for datasets
            print("Looking for datasets...")
            found_datasets = []

            for i in range(10):  # Check up to 10 potential datasets
                pos = f.tell()
                sig = f.read(4)

                if len(sig) < 4:
                    break

                print(f"  Position {pos:08x}: {sig} ({sig.hex()})")

                if sig == b'mhsd':
                    header_size = struct.unpack('<I', f.read(4))[0]
                    total_size = struct.unpack('<I', f.read(4))[0]
                    print(f"    Dataset found! Header: {header_size}, Total: {total_size}")

                    # Check what's inside this dataset
                    f.seek(pos + header_size)
                    inner_sig = f.read(4)
                    print(f"    Contains: {inner_sig} ({inner_sig.hex()})")

                    found_datasets.append((pos, inner_sig))

                    # Move to next dataset
                    f.seek(pos + total_size)
                elif sig == b'mhlt':
                    count = struct.unpack('<I', f.read(4))[0]
                    print(f"    Track list! Count: {count}")
                    break
                elif sig == b'mhlp':
                    count = struct.unpack('<I', f.read(4))[0]
                    print(f"    Playlist list! Count: {count}")
                    break
                else:
                    # Try to find next known signature
                    f.seek(pos + 1)

            print(f"\nFound {len(found_datasets)} datasets")

            # If we found a track list, look for tracks
            for dataset_pos, dataset_type in found_datasets:
                if dataset_type == b'mhlt':
                    print(f"\nExamining track list at {dataset_pos:08x}")
                    f.seek(dataset_pos)
                    f.read(12)  # Skip mhsd header

                    # Read mhlt
                    sig = f.read(4)
                    if sig == b'mhlt':
                        header_size = struct.unpack('<I', f.read(4))[0]
                        total_size = struct.unpack('<I', f.read(4))[0]
                        track_count = struct.unpack('<I', f.read(4))[0]

                        print(f"  Track count in list: {track_count}")

                        # Skip to first track
                        f.seek(f.tell() + header_size - 16)

                        # Look for first track
                        for j in range(min(5, track_count)):
                            pos = f.tell()
                            sig = f.read(4)

                            if sig == b'mhit':
                                print(f"  Track {j+1} at {pos:08x}")
                                header_size = struct.unpack('<I', f.read(4))[0]
                                total_size = struct.unpack('<I', f.read(4))[0]

                                # Read some track data
                                f.read(4)  # Skip something
                                track_id = struct.unpack('<I', f.read(4))[0]

                                print(f"    Track ID: {track_id}")
                                print(f"    Header size: {header_size}")
                                print(f"    Total size: {total_size}")

                                # Move to next track
                                f.seek(pos + total_size)
                            else:
                                print(f"  Expected mhit, got {sig}")
                                break
        else:
            print("❌ Not a valid iTunesDB file (should start with 'mhbd')")
            print()
            print("File actually starts with:")
            f.seek(0)
            print(hexdump(f.read(256)))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_parser.py <path_to_iTunesDB>")
        sys.exit(1)

    # Handle glob pattern
    from glob import glob
    files = glob(sys.argv[1])

    if not files:
        print(f"No files found matching: {sys.argv[1]}")
        sys.exit(1)

    for file_path in files:
        analyze_database(file_path)
        print("\n" + "="*60 + "\n")