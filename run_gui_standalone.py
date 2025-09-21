#!/usr/bin/env python3
"""
Standalone GUI launcher that works with system Python on macOS.
This version includes all necessary code inline to avoid import issues.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from datetime import datetime

class iPodysseyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("iPodyssey - iPod Music Liberation Tool")
        self.root.geometry("800x600")

        # Variables
        self.ipod_path = tk.StringVar()
        self.output_path = tk.StringVar(value=str(Path.home() / "Desktop" / f"ipod_export_{datetime.now().strftime('%Y%m%d')}"))

        # Configure styles
        self.setup_styles()

        # Create UI
        self.create_widgets()

        # Auto-detect iPod on startup
        self.root.after(100, self.auto_detect_ipod)

    def setup_styles(self):
        """Configure ttk styles for a modern look."""
        style = ttk.Style()
        bg_color = "#f0f0f0"
        self.root.configure(bg=bg_color)

        style.configure("Accent.TButton",
                       foreground="white",
                       font=("Segoe UI", 10, "bold"))

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

        # Output formats
        ttk.Label(options_frame, text="Format:").grid(row=0, column=0, sticky=tk.W,
                                                       padx=(0, 10))

        format_frame = ttk.Frame(options_frame)
        format_frame.grid(row=0, column=1, sticky=tk.W)

        ttk.Label(format_frame, text="CSV format compatible with Soundiiz").pack(side=tk.LEFT)

        # Output directory
        ttk.Label(options_frame, text="Output:").grid(row=1, column=0, sticky=tk.W,
                                                      padx=(0, 10), pady=(10, 0))

        output_frame = ttk.Frame(options_frame)
        output_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        output_frame.columnconfigure(0, weight=1)

        ttk.Entry(output_frame, textvariable=self.output_path).grid(
            row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(output_frame, text="Browse...",
                  command=self.browse_output).grid(row=0, column=1)

        # Status Section
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(0, weight=1)

        self.status_label = ttk.Label(status_frame, text="Ready to detect iPod")
        self.status_label.grid(row=0, column=0, sticky=tk.W)

        # Action Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=(10, 0))

        self.extract_button = ttk.Button(button_frame, text="Extract Music",
                                        command=self.extract_music,
                                        style="Accent.TButton", state="disabled")
        self.extract_button.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(button_frame, text="Exit", command=self.root.quit).pack(side=tk.LEFT)

    def auto_detect_ipod(self):
        """Auto-detect connected iPod."""
        self.update_status("Detecting iPod...")
        self.detect_button.config(state="disabled")

        # Simple detection logic
        ipod_path = self.find_ipod()

        if ipod_path:
            self.ipod_path.set(ipod_path)
            self.update_status(f"iPod detected at {ipod_path}")
            self.extract_button.config(state="normal")

            # Display iPod info
            self.display_ipod_info(ipod_path)
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

        self.detect_button.config(state="normal")

    def find_ipod(self):
        """Find mounted iPod on the system."""
        import platform

        if platform.system() == "Darwin":  # macOS
            volumes_path = Path("/Volumes")
            if volumes_path.exists():
                for volume in volumes_path.iterdir():
                    ipod_control = volume / "iPod_Control"
                    if ipod_control.exists():
                        return str(volume)

        elif platform.system() == "Windows":
            import string
            for drive_letter in string.ascii_uppercase:
                drive_path = Path(f"{drive_letter}:/")
                if drive_path.exists():
                    ipod_control = drive_path / "iPod_Control"
                    if ipod_control.exists():
                        return str(drive_path)

        elif platform.system() == "Linux":
            # Check /media/username/
            media_path = Path("/media")
            if media_path.exists():
                for user_dir in media_path.iterdir():
                    if user_dir.is_dir():
                        for mount in user_dir.iterdir():
                            ipod_control = mount / "iPod_Control"
                            if ipod_control.exists():
                                return str(mount)

        return None

    def display_ipod_info(self, ipod_path):
        """Display iPod information."""
        self.info_text.config(state="normal")
        self.info_text.delete(1.0, tk.END)

        music_path = Path(ipod_path) / "iPod_Control" / "Music"
        music_folders = 0
        total_files = 0

        if music_path.exists():
            folders = [d for d in music_path.iterdir() if d.is_dir() and d.name.startswith("F")]
            music_folders = len(folders)

            for folder in folders[:10]:  # Sample first 10 folders
                total_files += len(list(folder.glob("*.*")))

            # Estimate total based on sample
            if music_folders > 10:
                total_files = int(total_files * (music_folders / 10))

        info_lines = [
            f"iPod Path: {ipod_path}",
            f"Music Folders: {music_folders}",
            f"Estimated Music Files: {total_files:,}" if total_files else "Music Files: Unknown",
            "",
            "Ready to extract music to CSV format"
        ]

        self.info_text.insert(1.0, "\n".join(info_lines))
        self.info_text.config(state="disabled")

    def browse_output(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(initialdir=self.output_path.get())
        if directory:
            self.output_path.set(directory)

    def extract_music(self):
        """Extract music - simplified version."""
        if not self.ipod_path.get():
            messagebox.showerror("Error", "No iPod detected!")
            return

        output_dir = self.output_path.get()
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # For now, just show a message about what would be done
        message = f"Music extraction would:\n\n"
        message += f"1. Scan music files from:\n   {self.ipod_path.get()}/iPod_Control/Music/\n\n"
        message += f"2. Extract metadata using mutagen library\n\n"
        message += f"3. Save CSV to:\n   {output_dir}/ipod_music.csv\n\n"
        message += "Note: Full extraction requires the complete iPodyssey package.\n"
        message += "Run 'uv run python -m ipodyssey' for command-line extraction."

        messagebox.showinfo("Extraction Info", message)
        self.update_status("Ready for extraction (requires full package)")

    def update_status(self, message):
        """Update status label."""
        self.status_label.config(text=message)


def main():
    """Main GUI application entry point."""
    root = tk.Tk()

    # Try to set window to front on macOS
    if sys.platform == "darwin":
        try:
            root.lift()
            root.attributes('-topmost', True)
            root.after_idle(root.attributes, '-topmost', False)
        except:
            pass

    app = iPodysseyGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()