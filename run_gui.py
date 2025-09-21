#!/usr/bin/env python3
"""
Simple launcher for iPodyssey GUI that works around macOS Tkinter issues.
"""

import os
import sys

# Add the project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variable to fix macOS Tkinter issue
os.environ['TK_SILENCE_DEPRECATION'] = '1'

# Import and run the GUI
from ipodyssey.gui import main

if __name__ == "__main__":
    main()