"""
Progress window for iPodyssey GUI - provides detailed extraction feedback.
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from typing import Optional


class ProgressWindow:
    def __init__(self, parent, title="Extraction Progress"):
        """Create a progress window for long-running operations."""
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("600x400")
        self.window.transient(parent)

        # Prevent closing while operation is running
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.can_close = False

        # Main frame
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title label
        self.title_label = ttk.Label(main_frame, text="Extracting Music from iPod",
                                    font=("Segoe UI", 14, "bold"))
        self.title_label.pack(pady=(0, 20))

        # Current operation label
        self.operation_label = ttk.Label(main_frame, text="Initializing...")
        self.operation_label.pack(pady=(0, 10))

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var,
                                           length=500, mode='determinate')
        self.progress_bar.pack(pady=(0, 10))

        # Progress text (e.g., "1234 / 12000 files")
        self.progress_text = ttk.Label(main_frame, text="")
        self.progress_text.pack(pady=(0, 20))

        # Details frame with scrollbar
        details_frame = ttk.Frame(main_frame)
        details_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(details_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Details text area
        self.details_text = tk.Text(details_frame, height=10, width=60,
                                   wrap=tk.WORD, yscrollcommand=scrollbar.set)
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.details_text.yview)

        # Statistics frame
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill=tk.X, pady=(10, 0))

        self.stats_label = ttk.Label(stats_frame, text="", font=("Segoe UI", 9))
        self.stats_label.pack(side=tk.LEFT)

        self.time_label = ttk.Label(stats_frame, text="", font=("Segoe UI", 9))
        self.time_label.pack(side=tk.RIGHT)

        # Close button (disabled initially)
        self.close_button = ttk.Button(main_frame, text="Close", command=self.close,
                                      state="disabled")
        self.close_button.pack(pady=(10, 0))

        # Track timing
        self.start_time = time.time()
        self.last_update_time = 0

        # Center window
        self.center_window()

    def center_window(self):
        """Center the progress window on screen."""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')

    def update_progress(self, current: int, total: int, message: str = ""):
        """Update progress bar and message."""
        if total > 0:
            percent = (current / total) * 100
            self.progress_var.set(percent)
            self.progress_text.config(text=f"{current:,} / {total:,} files ({percent:.1f}%)")
        else:
            # Indeterminate mode for unknown total
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start(10)

        if message:
            self.operation_label.config(text=message)

        # Update details only if enough time has passed (to avoid UI lag)
        current_time = time.time()
        if current_time - self.last_update_time > 0.1:  # Update every 100ms max
            self.add_detail(message)
            self.last_update_time = current_time

        # Update statistics
        elapsed = current_time - self.start_time
        if current > 0 and total > 0:
            rate = current / elapsed if elapsed > 0 else 0
            eta = (total - current) / rate if rate > 0 else 0

            self.stats_label.config(text=f"Rate: {rate:.1f} files/sec")
            self.time_label.config(text=f"ETA: {self.format_time(eta)}")
        else:
            self.time_label.config(text=f"Elapsed: {self.format_time(elapsed)}")

    def add_detail(self, text: str):
        """Add a detail line to the text area."""
        self.details_text.insert(tk.END, f"{text}\n")
        self.details_text.see(tk.END)  # Auto-scroll to bottom

        # Limit lines to prevent memory issues
        lines = int(self.details_text.index('end-1c').split('.')[0])
        if lines > 100:
            self.details_text.delete('1.0', '2.0')

    def format_time(self, seconds: float) -> str:
        """Format seconds into readable time."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"

    def set_complete(self, message: str = "Extraction complete!"):
        """Mark operation as complete."""
        self.progress_var.set(100)
        self.progress_bar.stop()  # Stop indeterminate animation if running
        self.progress_bar.config(mode='determinate')
        self.operation_label.config(text=message)
        self.close_button.config(state="normal")
        self.can_close = True

        elapsed = time.time() - self.start_time
        self.add_detail(f"\n{message}")
        self.add_detail(f"Total time: {self.format_time(elapsed)}")

    def set_error(self, error_message: str):
        """Mark operation as failed."""
        self.progress_bar.stop()
        self.operation_label.config(text="Extraction failed!", foreground="red")
        self.add_detail(f"\nERROR: {error_message}")
        self.close_button.config(state="normal")
        self.can_close = True

    def on_closing(self):
        """Handle window close button."""
        if self.can_close:
            self.close()

    def close(self):
        """Close the progress window."""
        self.window.destroy()