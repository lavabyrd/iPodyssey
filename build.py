#!/usr/bin/env python3
"""
Build script for creating standalone iPodyssey executables.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def build_executable():
    """Build the standalone executable using PyInstaller."""
    print("🔨 Building iPodyssey executable...")

    # Install PyInstaller if not already installed
    try:
        import PyInstaller
    except ImportError:
        print("📦 Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    # Clean previous builds
    for dir in ["build", "dist"]:
        if os.path.exists(dir):
            print(f"🧹 Cleaning {dir}/")
            shutil.rmtree(dir)

    # Determine platform-specific options
    platform_args = []
    output_name = "iPodyssey"

    if sys.platform == "darwin":  # macOS
        platform_args.extend(["--osx-bundle-identifier", "com.ipodyssey.app"])
        print("🍎 Building for macOS...")
    elif sys.platform == "win32":  # Windows
        output_name = "iPodyssey.exe"
        print("🪟 Building for Windows...")
    else:  # Linux
        print("🐧 Building for Linux...")

    # Build command
    cmd = [
        "pyinstaller",
        "--name", "iPodyssey",
        "--onefile",
        "--windowed",  # No console window
        "--clean",
        "--noconfirm",
    ]

    # Add hidden imports
    hidden_imports = [
        "ipodyssey",
        "ipodyssey.copier",
        "ipodyssey.scanner",
        "ipodyssey.database",
        "ipodyssey.database.parser",
        "ipodyssey.database.structures",
        "mutagen",
        "mutagen.mp3",
        "mutagen.mp4",
        "construct",
    ]

    for module in hidden_imports:
        cmd.extend(["--hidden-import", module])

    # Add platform-specific arguments
    cmd.extend(platform_args)

    # Add the main script
    cmd.append("ipodyssey/gui.py")

    print(f"📋 Running: {' '.join(cmd)}")

    # Run PyInstaller
    result = subprocess.run(cmd, capture_output=False, text=True)

    if result.returncode != 0:
        print("❌ Build failed!")
        return False

    print("✅ Build successful!")

    # Show output location
    dist_dir = Path("dist")
    if dist_dir.exists():
        files = list(dist_dir.iterdir())
        print("\n📦 Output files:")
        for file in files:
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"  • {file.name} ({size_mb:.1f} MB)")

    return True


def create_installer():
    """Create platform-specific installer (optional)."""
    if sys.platform == "win32":
        print("\n📦 Creating Windows installer...")
        print("  You can use NSIS or Inno Setup to create a proper installer.")
        print("  Download Inno Setup: https://jrsoftware.org/isdl.php")

    elif sys.platform == "darwin":
        print("\n📦 Creating macOS DMG...")
        # Could use create-dmg here if installed
        print("  You can use create-dmg to make a DMG file.")
        print("  Install with: brew install create-dmg")

    elif sys.platform.startswith("linux"):
        print("\n📦 Creating Linux AppImage...")
        print("  You can use AppImageKit to create an AppImage.")
        print("  See: https://appimage.org/")


def main():
    """Main build process."""
    print("=" * 50)
    print("iPodyssey Build Script")
    print("=" * 50)

    if build_executable():
        create_installer()
        print("\n🎉 Build complete! Check the 'dist' folder for your executable.")
        print("\nTo distribute:")
        print("  • Windows: Share the .exe file or create an installer")
        print("  • macOS: Share the .app bundle or create a DMG")
        print("  • Linux: Share the binary or create an AppImage")
    else:
        print("\n❌ Build failed. Check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()