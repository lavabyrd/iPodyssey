#!/usr/bin/env python3
"""
iPodyssey - iPod Music Extraction Tool
Main TUI interface for extracting music and playlists from iPod devices.
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.layout import Layout
from rich.text import Text
from rich import box
from rich.columns import Columns

# Import our modules
from .copier import detect_ipod, copy_database_files, get_ipod_info
from .database.parser import DatabaseParser
from .scanner import scan_ipod_music, export_to_csv

console = Console()


def print_banner():
    """Print the iPodyssey banner."""
    banner = """
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║  🎵  iPodyssey - iPod Music Liberation Tool  🎵          ║
║                                                          ║
║  Extract your music collection from classic iPods        ║
║  Support for iPod Video and other classic models         ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


def find_ipods() -> List[str]:
    """Find all mounted iPods on the system."""
    ipods = []

    # Check common mount points based on platform
    if sys.platform == "darwin":  # macOS
        volumes_path = Path("/Volumes")
        if volumes_path.exists():
            for volume in volumes_path.iterdir():
                ipod_control = volume / "iPod_Control"
                if ipod_control.exists():
                    ipods.append(str(volume))

    elif sys.platform.startswith("linux"):  # Linux
        # Check /media/username/
        media_path = Path("/media")
        if media_path.exists():
            for user_dir in media_path.iterdir():
                if user_dir.is_dir():
                    for mount in user_dir.iterdir():
                        ipod_control = mount / "iPod_Control"
                        if ipod_control.exists():
                            ipods.append(str(mount))

        # Also check /mnt/
        mnt_path = Path("/mnt")
        if mnt_path.exists():
            for mount in mnt_path.iterdir():
                ipod_control = mount / "iPod_Control"
                if ipod_control.exists():
                    ipods.append(str(mount))

    elif sys.platform == "win32":  # Windows
        import string
        # Check all drive letters
        for drive_letter in string.ascii_uppercase:
            drive_path = Path(f"{drive_letter}:/")
            if drive_path.exists():
                ipod_control = drive_path / "iPod_Control"
                if ipod_control.exists():
                    ipods.append(str(drive_path))

    return ipods


def select_ipod() -> Optional[str]:
    """Let user select an iPod from available devices."""
    console.print("\n[bold]🔍 Searching for iPod devices...[/bold]\n")

    with console.status("[bold green]Scanning volumes..."):
        ipods = find_ipods()

    if not ipods:
        console.print("[red]❌ No iPod devices found![/red]")
        console.print("\nMake sure your iPod is:")
        console.print("  • Connected via USB")
        console.print("  • Mounted as a disk drive")
        console.print("  • Has the iPod_Control folder")

        manual = Confirm.ask("\nWould you like to enter a path manually?")
        if manual:
            path = Prompt.ask("Enter iPod path")
            if os.path.exists(os.path.join(path, "iPod_Control")):
                return path
            else:
                console.print(f"[red]❌ No iPod_Control folder found at {path}[/red]")
        return None

    if len(ipods) == 1:
        ipod_path = ipods[0]
        info = get_ipod_info(ipod_path)

        # Show iPod details
        table = Table(title="iPod Detected", box=box.ROUNDED)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Path", ipod_path)
        table.add_row("Name", os.path.basename(ipod_path))
        table.add_row("Model", info.get('model', 'Unknown'))

        if info.get('database_found'):
            size_mb = info.get('database_size', 0) / (1024*1024)
            table.add_row("Database", f"✓ Found ({size_mb:.1f} MB)")
        else:
            table.add_row("Database", "✗ Not found")

        table.add_row("Music Folders", str(info.get('music_folders', 0)))

        if info.get('total_music_files'):
            table.add_row("Music Files", f"{info['total_music_files']:,}")

        console.print(table)

        if Confirm.ask(f"\nUse this iPod?", default=True):
            return ipod_path
        return None

    # Multiple iPods found
    console.print(f"[green]Found {len(ipods)} iPod devices:[/green]\n")

    for i, ipod in enumerate(ipods, 1):
        info = get_ipod_info(ipod)
        name = os.path.basename(ipod)
        files = info.get('total_music_files', 0)

        console.print(f"  [{i}] {name}")
        if files:
            console.print(f"      └─ {files:,} music files")

    choice = IntPrompt.ask(f"\nSelect iPod [1-{len(ipods)}]", default=1)

    if 1 <= choice <= len(ipods):
        return ipods[choice - 1]
    return None


def select_extraction_mode() -> str:
    """Let user choose what to extract."""
    console.print("\n[bold]📦 What would you like to extract?[/bold]\n")

    options = [
        ("scan", "🎵 Scan music files directly", "Extract metadata from actual music files (recommended if database is empty)"),
        ("database", "📚 Parse iTunes database", "Extract from iTunesDB (tracks, playlists, play counts)"),
        ("both", "🎯 Both (Complete extraction)", "Try database first, fall back to file scanning"),
        ("copy", "💾 Copy database only", "Just copy the database files for later analysis"),
    ]

    for i, (key, title, desc) in enumerate(options, 1):
        console.print(f"  [{i}] [bold]{title}[/bold]")
        console.print(f"      [dim]{desc}[/dim]")

    choice = IntPrompt.ask(f"\nSelect mode [1-{len(options)}]", default=1)

    if 1 <= choice <= len(options):
        return options[choice - 1][0]
    return "scan"


def select_output_format() -> List[str]:
    """Let user choose output formats."""
    console.print("\n[bold]📄 Select output formats:[/bold]\n")

    formats = [
        ("csv", "CSV for Soundiiz", "Upload to Soundiiz.com for playlist import"),
        ("json", "JSON format", "Machine-readable format with all metadata"),
        ("m3u", "M3U playlist", "Standard playlist format"),
        ("text", "Text report", "Human-readable summary"),
    ]

    console.print("Available formats:")
    for i, (key, title, desc) in enumerate(formats, 1):
        console.print(f"  [{i}] [bold]{title}[/bold] - {desc}")

    console.print(f"\n  [0] All formats")

    choices = Prompt.ask("Select formats (comma-separated, e.g., 1,2,3)", default="1")

    if choices == "0":
        return [fmt[0] for fmt in formats]

    selected = []
    for choice in choices.split(","):
        try:
            idx = int(choice.strip()) - 1
            if 0 <= idx < len(formats):
                selected.append(formats[idx][0])
        except ValueError:
            pass

    return selected if selected else ["csv"]


def select_destination() -> str:
    """Let user choose output destination."""
    console.print("\n[bold]📁 Where should files be saved?[/bold]\n")

    default = f"./ipodyssey_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    dest = Prompt.ask("Output directory", default=default)

    # Create directory if it doesn't exist
    Path(dest).mkdir(parents=True, exist_ok=True)

    return dest


def perform_extraction(ipod_path: str, mode: str, formats: List[str], destination: str):
    """Perform the actual extraction based on user choices."""
    console.print("\n[bold]🚀 Starting extraction...[/bold]\n")

    results = {
        'tracks': [],
        'playlists': [],
        'database_copied': False
    }

    # Progress tracking
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:

        if mode in ["database", "both", "copy"]:
            # Copy database files
            task = progress.add_task("[cyan]Copying database files...", total=None)

            try:
                copied_files = copy_database_files(ipod_path, destination)
                results['database_copied'] = True
                progress.update(task, completed=True)

                if "iTunesDB" in copied_files and mode != "copy":
                    # Parse database
                    task = progress.add_task("[cyan]Parsing iTunesDB...", total=None)
                    parser = DatabaseParser(copied_files["iTunesDB"])
                    tracks, playlists = parser.parse()

                    results['tracks'] = list(tracks.values())
                    results['playlists'] = playlists
                    progress.update(task, completed=True)

            except Exception as e:
                console.print(f"[red]Database extraction failed: {e}[/red]")
                if mode == "database":
                    return results

        if mode in ["scan", "both"] and not results['tracks']:
            # Scan music files directly
            task = progress.add_task("[cyan]Scanning music files...", total=None)

            try:
                tracks = scan_ipod_music(ipod_path)
                results['tracks'] = tracks
                progress.update(task, completed=True)
            except Exception as e:
                console.print(f"[red]Music scan failed: {e}[/red]")

    # Export to selected formats
    if results['tracks']:
        console.print(f"\n[green]✅ Extracted {len(results['tracks'])} tracks[/green]")

        for fmt in formats:
            export_tracks(results['tracks'], results['playlists'], fmt, destination)
    else:
        console.print("\n[yellow]⚠️  No tracks found to export[/yellow]")

    return results


def export_tracks(tracks: List, playlists: List, format: str, destination: str):
    """Export tracks to specified format."""
    if format == "csv":
        output_path = os.path.join(destination, "ipod_music.csv")
        export_to_csv(tracks, output_path)
        console.print(f"  ✓ CSV saved to {output_path}")

    elif format == "json":
        import json
        output_path = os.path.join(destination, "ipod_music.json")

        # Convert tracks to serializable format
        data = {
            'export_date': datetime.now().isoformat(),
            'track_count': len(tracks),
            'tracks': []
        }

        for track in tracks:
            if isinstance(track, dict):
                data['tracks'].append(track)
            else:
                # Convert Track objects to dict
                data['tracks'].append({
                    'title': getattr(track, 'title', 'Unknown'),
                    'artist': getattr(track, 'artist', 'Unknown'),
                    'album': getattr(track, 'album', 'Unknown'),
                    'year': getattr(track, 'year', 0),
                    'play_count': getattr(track, 'play_count', 0),
                })

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        console.print(f"  ✓ JSON saved to {output_path}")

    elif format == "m3u":
        output_path = os.path.join(destination, "ipod_music.m3u")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            for track in tracks:
                if isinstance(track, dict):
                    title = track.get('title', 'Unknown')
                    artist = track.get('artist', 'Unknown')
                    duration = track.get('duration', 0) // 1000 if track.get('duration') else -1
                else:
                    title = getattr(track, 'title', 'Unknown')
                    artist = getattr(track, 'artist', 'Unknown')
                    duration = getattr(track, 'total_time_ms', 0) // 1000

                f.write(f"#EXTINF:{duration},{artist} - {title}\n")
                f.write(f"{artist} - {title}.mp3\n")

        console.print(f"  ✓ M3U saved to {output_path}")

    elif format == "text":
        output_path = os.path.join(destination, "ipod_summary.txt")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("iPodyssey Music Extraction Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Extraction Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Tracks: {len(tracks)}\n")
            f.write(f"Total Playlists: {len(playlists)}\n\n")

            # Group by artist
            artists = {}
            for track in tracks:
                if isinstance(track, dict):
                    artist = track.get('artist', 'Unknown')
                else:
                    artist = getattr(track, 'artist', 'Unknown')

                if artist not in artists:
                    artists[artist] = 0
                artists[artist] += 1

            f.write(f"Artists: {len(artists)}\n\n")
            f.write("Top Artists:\n")
            for artist, count in sorted(artists.items(), key=lambda x: x[1], reverse=True)[:20]:
                f.write(f"  {artist}: {count} tracks\n")

            if playlists:
                f.write(f"\n\nPlaylists:\n")
                for pl in playlists:
                    f.write(f"  {pl.name}: {len(pl.track_ids)} tracks\n")

        console.print(f"  ✓ Summary saved to {output_path}")


def show_summary(results: Dict):
    """Show extraction summary."""
    console.print("\n" + "="*60)
    console.print("\n[bold green]✨ Extraction Complete![/bold green]\n")

    # Create summary table
    table = Table(title="Extraction Summary", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Tracks Extracted", f"{len(results.get('tracks', [])): ,}")
    table.add_row("Playlists Found", f"{len(results.get('playlists', [])): ,}")

    if results.get('database_copied'):
        table.add_row("Database Backup", "✓ Copied")

    # Calculate some statistics
    if results.get('tracks'):
        artists = set()
        albums = set()

        for track in results['tracks']:
            if isinstance(track, dict):
                artists.add(track.get('artist', 'Unknown'))
                albums.add(track.get('album', 'Unknown'))
            else:
                artists.add(getattr(track, 'artist', 'Unknown'))
                albums.add(getattr(track, 'album', 'Unknown'))

        table.add_row("Unique Artists", f"{len(artists): ,}")
        table.add_row("Unique Albums", f"{len(albums): ,}")

    console.print(table)

    console.print("\n[bold]Next Steps:[/bold]")
    console.print("  1. Upload the CSV to [link]https://soundiiz.com[/link]")
    console.print("  2. Connect your streaming services")
    console.print("  3. Import your music library")
    console.print("\n[dim]Your iPod music lives on! 🎵[/dim]")


def main():
    """Main TUI application."""
    try:
        print_banner()

        # Step 1: Select iPod
        ipod_path = select_ipod()
        if not ipod_path:
            console.print("\n[red]No iPod selected. Exiting.[/red]")
            return 1

        # Step 2: Select extraction mode
        mode = select_extraction_mode()

        # Step 3: Select output formats
        formats = select_output_format()

        # Step 4: Select destination
        destination = select_destination()

        # Step 5: Perform extraction
        results = perform_extraction(ipod_path, mode, formats, destination)

        # Step 6: Show summary
        show_summary(results)

        console.print(f"\n[dim]Files saved to: {destination}[/dim]\n")

        return 0

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Extraction cancelled by user.[/yellow]")
        return 1
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())