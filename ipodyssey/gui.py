"""
iPodyssey GUI - Modern desktop interface for iPod music extraction.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

# Import our modules
from .copier import detect_ipod, copy_database_files, get_ipod_info
from .database.parser import DatabaseParser
from .scanner import scan_ipod_music, export_to_csv
from .gui_progress import ProgressWindow


class iPodysseyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("iPodyssey - iPod Music Liberation Tool")
        self.root.geometry("800x600")

        # Variables
        self.ipod_path = tk.StringVar()
        self.output_path = tk.StringVar(value=str(Path.home() / "Desktop" / f"ipod_export_{datetime.now().strftime('%Y%m%d')}"))
        self.tracks = []
        self.playlists = []

        # Configure styles
        self.setup_styles()

        # Create UI
        self.create_widgets()

        # Auto-detect iPod on startup
        self.root.after(100, self.auto_detect_ipod)

    def setup_styles(self):
        """Configure ttk styles for a modern look."""
        style = ttk.Style()

        # Configure colors
        bg_color = "#f0f0f0"
        self.root.configure(bg=bg_color)

        # Configure button style
        style.configure("Accent.TButton",
                       foreground="white",
                       font=("Segoe UI", 10, "bold"))

        # Configure header style
        style.configure("Header.TLabel",
                       font=("Segoe UI", 16, "bold"))

        style.configure("Subheader.TLabel",
                       font=("Segoe UI", 12))

    def create_widgets(self):
        """Create all GUI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky=(tk.W, tk.E))

        ttk.Label(title_frame, text="🎵 iPodyssey", style="Header.TLabel").pack()
        ttk.Label(title_frame, text="Extract music and playlists from your iPod",
                 style="Subheader.TLabel").pack()

        # iPod Detection Section
        detection_frame = ttk.LabelFrame(main_frame, text="iPod Detection", padding="10")
        detection_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        detection_frame.columnconfigure(1, weight=1)

        ttk.Label(detection_frame, text="iPod Path:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Entry(detection_frame, textvariable=self.ipod_path, state="readonly").grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))

        self.detect_button = ttk.Button(detection_frame, text="Detect iPod",
                                       command=self.auto_detect_ipod)
        self.detect_button.grid(row=0, column=2)

        # iPod Info Display
        self.info_text = scrolledtext.ScrolledText(main_frame, height=6, width=60,
                                                   wrap=tk.WORD, state="disabled")
        self.info_text.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        # Extraction Options
        options_frame = ttk.LabelFrame(main_frame, text="Extraction Options", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        options_frame.columnconfigure(1, weight=1)

        # Extraction mode
        ttk.Label(options_frame, text="Mode:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))

        self.mode_var = tk.StringVar(value="both")
        mode_frame = ttk.Frame(options_frame)
        mode_frame.grid(row=0, column=1, sticky=tk.W)

        ttk.Radiobutton(mode_frame, text="Database Only", variable=self.mode_var,
                       value="database").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(mode_frame, text="Scan Files Only", variable=self.mode_var,
                       value="scan").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(mode_frame, text="Both (Recommended)", variable=self.mode_var,
                       value="both").pack(side=tk.LEFT)

        # Output formats
        ttk.Label(options_frame, text="Formats:").grid(row=1, column=0, sticky=tk.W,
                                                       padx=(0, 10), pady=(10, 0))

        format_frame = ttk.Frame(options_frame)
        format_frame.grid(row=1, column=1, sticky=tk.W, pady=(10, 0))

        self.format_csv = tk.BooleanVar(value=True)
        self.format_json = tk.BooleanVar(value=False)
        self.format_m3u = tk.BooleanVar(value=False)
        self.format_txt = tk.BooleanVar(value=False)

        ttk.Checkbutton(format_frame, text="CSV (Soundiiz)",
                       variable=self.format_csv).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(format_frame, text="JSON",
                       variable=self.format_json).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(format_frame, text="M3U Playlist",
                       variable=self.format_m3u).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(format_frame, text="Text Report",
                       variable=self.format_txt).pack(side=tk.LEFT)

        # Output directory
        ttk.Label(options_frame, text="Output:").grid(row=2, column=0, sticky=tk.W,
                                                      padx=(0, 10), pady=(10, 0))

        output_frame = ttk.Frame(options_frame)
        output_frame.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        output_frame.columnconfigure(0, weight=1)

        ttk.Entry(output_frame, textvariable=self.output_path).grid(
            row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(output_frame, text="Browse...",
                  command=self.browse_output).grid(row=0, column=1)

        # Progress Section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                           mode='indeterminate')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))

        self.status_label = ttk.Label(progress_frame, text="Ready")
        self.status_label.grid(row=1, column=0, sticky=tk.W)

        # Action Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=(10, 0))

        self.extract_button = ttk.Button(button_frame, text="Extract Music",
                                        command=self.start_extraction,
                                        style="Accent.TButton", state="disabled")
        self.extract_button.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(button_frame, text="Exit", command=self.root.quit).pack(side=tk.LEFT)

    def auto_detect_ipod(self):
        """Auto-detect connected iPod."""
        self.update_status("Detecting iPod...")
        self.detect_button.config(state="disabled")

        def detect():
            ipod_path = detect_ipod()
            self.root.after(0, self.handle_detection_result, ipod_path)

        thread = threading.Thread(target=detect, daemon=True)
        thread.start()

    def handle_detection_result(self, ipod_path):
        """Handle iPod detection result."""
        self.detect_button.config(state="normal")

        if ipod_path:
            self.ipod_path.set(ipod_path)
            self.update_status(f"iPod detected at {ipod_path}")
            self.extract_button.config(state="normal")

            # Get iPod info
            info = get_ipod_info(ipod_path)
            self.display_ipod_info(info)
        else:
            self.ipod_path.set("")
            self.update_status("No iPod detected")
            self.extract_button.config(state="disabled")
            messagebox.showinfo("No iPod Found",
                              "No iPod device was detected.\n\n"
                              "Please ensure your iPod is:\n"
                              "• Connected via USB\n"
                              "• Mounted as a disk drive\n"
                              "• Has the iPod_Control folder")

    def display_ipod_info(self, info):
        """Display iPod information."""
        self.info_text.config(state="normal")
        self.info_text.delete(1.0, tk.END)

        info_lines = [
            f"iPod Model: {info.get('model', 'Unknown')}",
            f"Mount Path: {info.get('mount_path', '')}",
            f"Music Folders: {info.get('music_folders', 0)}",
            f"Music Files: {info.get('total_music_files', 0):,}",
            f"Database: {'Found' if info.get('database_found') else 'Not found'}",
        ]

        if info.get('database_found'):
            size_mb = info.get('database_size', 0) / (1024*1024)
            info_lines.append(f"Database Size: {size_mb:.1f} MB")

        self.info_text.insert(1.0, "\n".join(info_lines))
        self.info_text.config(state="disabled")

    def browse_output(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(initialdir=self.output_path.get())
        if directory:
            self.output_path.set(directory)

    def start_extraction(self):
        """Start the extraction process in a separate thread."""
        if not self.ipod_path.get():
            messagebox.showerror("Error", "No iPod detected!")
            return

        # Check if at least one format is selected
        if not any([self.format_csv.get(), self.format_json.get(),
                   self.format_m3u.get(), self.format_txt.get()]):
            messagebox.showerror("Error", "Please select at least one output format!")
            return

        # Disable buttons during extraction
        self.extract_button.config(state="disabled")
        self.detect_button.config(state="disabled")

        # Start progress bar
        self.progress_bar.start(10)

        # Run extraction in thread
        thread = threading.Thread(target=self.perform_extraction, daemon=True)
        thread.start()

    def perform_extraction(self):
        """Perform the actual extraction with progress window."""
        # Create progress window
        self.root.after(0, self.create_progress_window)

        try:
            ipod_path = self.ipod_path.get()
            output_dir = self.output_path.get()
            mode = self.mode_var.get()

            # Create output directory with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extraction_dir = os.path.join(output_dir, f"ipod_extraction_{timestamp}")
            Path(extraction_dir).mkdir(parents=True, exist_ok=True)

            self.tracks = []
            self.playlists = []

            # Extract based on mode
            if mode in ["database", "both"]:
                self.root.after(0, self.update_progress_status,
                              0, 0, "Copying database files...")

                try:
                    copied_files = copy_database_files(ipod_path, extraction_dir)

                    if "iTunesDB" in copied_files:
                        self.root.after(0, self.update_progress_status,
                                      0, 0, "Parsing iTunes database...")
                        parser = DatabaseParser(copied_files["iTunesDB"])
                        tracks, playlists = parser.parse()
                        self.tracks = list(tracks.values())
                        self.playlists = playlists
                        self.root.after(0, self.update_progress_status,
                                      len(self.tracks), len(self.tracks),
                                      f"Found {len(self.tracks)} tracks in database")
                except Exception as e:
                    print(f"Database extraction error: {e}")
                    if mode == "database":
                        raise e
                    # Continue with scan if mode is "both"

            if mode in ["scan", "both"] and not self.tracks:
                # Create progress callback for scanner
                def progress_callback(current, total, message):
                    self.root.after(0, self.update_progress_status,
                                  current, total, message)

                self.root.after(0, self.update_progress_status,
                              0, 0, "Starting music file scan...")

                # Scan with progress updates
                self.tracks = scan_ipod_music(ipod_path, progress_callback)

            # Export to selected formats
            self.root.after(0, self.export_results, extraction_dir)

        except Exception as e:
            self.root.after(0, self.handle_extraction_error, str(e))
        finally:
            self.root.after(0, self.extraction_complete)

    def export_results(self, output_dir):
        """Export results to selected formats."""
        if not self.tracks:
            self.update_status("No tracks found to export")
            return

        exported_files = []

        if self.format_csv.get():
            self.update_status("Exporting CSV...")
            csv_path = os.path.join(output_dir, "ipod_music.csv")
            export_to_csv(self.tracks, csv_path)
            exported_files.append("ipod_music.csv")

        if self.format_json.get():
            self.update_status("Exporting JSON...")
            json_path = os.path.join(output_dir, "ipod_music.json")
            self.export_json(json_path)
            exported_files.append("ipod_music.json")

        if self.format_m3u.get():
            self.update_status("Exporting M3U...")
            m3u_path = os.path.join(output_dir, "ipod_music.m3u")
            self.export_m3u(m3u_path)
            exported_files.append("ipod_music.m3u")

        if self.format_txt.get():
            self.update_status("Exporting text report...")
            txt_path = os.path.join(output_dir, "ipod_summary.txt")
            self.export_text_report(txt_path)
            exported_files.append("ipod_summary.txt")

        # Show success message
        message = f"Successfully extracted {len(self.tracks):,} tracks!\n\n"
        message += "Files saved:\n"
        for file in exported_files:
            message += f"• {file}\n"
        message += f"\nLocation: {output_dir}"

        messagebox.showinfo("Extraction Complete", message)

        # Open output folder (platform-specific)
        import platform
        if platform.system() == "Darwin":  # macOS
            os.system(f'open "{output_dir}"')
        elif platform.system() == "Windows":
            os.startfile(output_dir)
        elif platform.system() == "Linux":
            os.system(f'xdg-open "{output_dir}"')
        self.update_status(f"Extracted {len(self.tracks):,} tracks")

    def export_json(self, path):
        """Export to JSON format."""
        import json
        data = {
            'export_date': datetime.now().isoformat(),
            'track_count': len(self.tracks),
            'tracks': []
        }

        for track in self.tracks:
            if isinstance(track, dict):
                data['tracks'].append(track)
            else:
                data['tracks'].append({
                    'title': getattr(track, 'title', 'Unknown'),
                    'artist': getattr(track, 'artist', 'Unknown'),
                    'album': getattr(track, 'album', 'Unknown'),
                    'year': getattr(track, 'year', 0),
                    'play_count': getattr(track, 'play_count', 0),
                })

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def export_m3u(self, path):
        """Export to M3U playlist format."""
        with open(path, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            for track in self.tracks:
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

    def export_text_report(self, path):
        """Export text summary report."""
        with open(path, 'w', encoding='utf-8') as f:
            f.write("iPodyssey Music Extraction Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Extraction Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Tracks: {len(self.tracks)}\n")
            f.write(f"Total Playlists: {len(self.playlists)}\n\n")

            # Group by artist
            artists = {}
            for track in self.tracks:
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

    def handle_extraction_error(self, error_msg):
        """Handle extraction errors."""
        if hasattr(self, 'progress_window'):
            self.progress_window.set_error(error_msg)
        else:
            messagebox.showerror("Extraction Error", f"An error occurred:\n\n{error_msg}")
        self.update_status("Extraction failed")

    def extraction_complete(self):
        """Re-enable buttons after extraction."""
        if hasattr(self, 'progress_window'):
            self.progress_window.set_complete(f"Successfully extracted {len(self.tracks):,} tracks!")
        self.progress_bar.stop()
        self.extract_button.config(state="normal")
        self.detect_button.config(state="normal")

    def update_status(self, message):
        """Update status label."""
        self.status_label.config(text=message)

    def create_progress_window(self):
        """Create the progress window."""
        self.progress_window = ProgressWindow(self.root, "iPod Music Extraction")

    def update_progress_status(self, current, total, message):
        """Update progress window status."""
        if hasattr(self, 'progress_window'):
            self.progress_window.update_progress(current, total, message)
        self.update_status(message)


def main():
    """Main GUI application entry point."""
    root = tk.Tk()
    app = iPodysseyGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()