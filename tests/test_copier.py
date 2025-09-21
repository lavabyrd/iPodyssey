"""Tests for the copier module."""

import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pytest
from unittest.mock import patch, MagicMock, mock_open

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ipodyssey import copier


class TestDetectIpod:
    """Test iPod detection functionality."""

    def test_detect_ipod_not_mounted(self):
        """Test when iPod is not mounted."""
        with patch('os.path.exists', return_value=False):
            result = copier.detect_ipod("/Volumes/FAKE_IPOD")
            assert result is None

    def test_detect_ipod_no_database(self):
        """Test when volume exists but no iTunesDB."""
        with patch('os.path.exists') as mock_exists:
            # First call checks mount path, second checks iTunesDB
            mock_exists.side_effect = [True, False]
            result = copier.detect_ipod("/Volumes/TEST")
            assert result is None

    def test_detect_ipod_success(self):
        """Test successful iPod detection."""
        with patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=1024*1024*5), \
             patch('os.path.getmtime', return_value=datetime.now().timestamp()), \
             patch('os.listdir', return_value=['iTunes', 'Music', 'Artwork']):

            result = copier.detect_ipod("/Volumes/TEST_IPOD")
            assert result == "/Volumes/TEST_IPOD"


class TestVerifyDatabaseIntegrity:
    """Test database integrity verification."""

    def test_verify_missing_file(self):
        """Test verifying non-existent file."""
        is_valid, message = copier.verify_database_integrity("/fake/path")
        assert is_valid is False
        assert "not found" in message.lower()

    def test_verify_invalid_header(self):
        """Test file with invalid header."""
        mock_data = b'WRONG_HEADER' + b'\x00' * 100

        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=mock_data)):
            is_valid, message = copier.verify_database_integrity("/fake/db")
            assert is_valid is False
            assert "Invalid header" in message

    def test_verify_valid_database(self):
        """Test valid iTunesDB file."""
        # Create mock iTunesDB data with correct header
        mock_data = b'mhbd' + b'\x00\x00\x00\x68' + b'\x00' * 1000

        # Use a real temporary file for simpler testing
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(mock_data)
            temp_path = temp_file.name

        try:
            is_valid, message = copier.verify_database_integrity(temp_path)
            assert is_valid is True
            assert "Valid iTunesDB" in message
        finally:
            os.unlink(temp_path)


class TestCopyDatabaseFiles:
    """Test database file copying functionality."""

    def test_copy_creates_timestamped_directory(self):
        """Test that copy creates directory with timestamp."""
        with tempfile.TemporaryDirectory() as temp_dir:
            ipod_path = temp_dir
            dest_path = os.path.join(temp_dir, "output")

            # Create fake iPod structure
            os.makedirs(os.path.join(ipod_path, "iPod_Control", "iTunes"))
            db_path = os.path.join(ipod_path, "iPod_Control", "iTunes", "iTunesDB")

            # Create fake database file
            with open(db_path, 'wb') as f:
                f.write(b'mhbd' + b'\x00' * 100)

            # Run copy
            copied = copier.copy_database_files(ipod_path, dest_path)

            # Check that output directory was created with timestamp pattern
            output_dirs = os.listdir(dest_path)
            assert len(output_dirs) == 1
            assert output_dirs[0].startswith("ipod_backup_")

            # Check that file was copied
            assert "iTunesDB" in copied
            assert os.path.exists(copied["iTunesDB"])

    def test_copy_handles_missing_files(self):
        """Test that copy handles missing optional files gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            ipod_path = temp_dir
            dest_path = os.path.join(temp_dir, "output")

            # Create only iTunesDB, not other files
            os.makedirs(os.path.join(ipod_path, "iPod_Control", "iTunes"))
            db_path = os.path.join(ipod_path, "iPod_Control", "iTunes", "iTunesDB")

            with open(db_path, 'wb') as f:
                f.write(b'mhbd' + b'\x00' * 100)

            # Run copy
            copied = copier.copy_database_files(ipod_path, dest_path)

            # Should only have iTunesDB
            assert len(copied) == 1
            assert "iTunesDB" in copied


class TestGetIpodInfo:
    """Test iPod information extraction."""

    def test_get_info_no_music_folders(self):
        """Test getting info when no music folders exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            info = copier.get_ipod_info(temp_dir)

            assert info["mount_path"] == temp_dir
            assert info["music_folders"] == 0
            assert info["database_found"] is False

    def test_get_info_with_music_and_database(self):
        """Test getting info with music folders and database."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create music folders
            music_path = os.path.join(temp_dir, "iPod_Control", "Music")
            os.makedirs(music_path)

            for i in range(5):
                folder = os.path.join(music_path, f"F{i:02d}")
                os.makedirs(folder)
                # Add some fake music files
                for j in range(10):
                    Path(os.path.join(folder, f"SONG{j}.mp3")).touch()

            # Create database
            db_dir = os.path.join(temp_dir, "iPod_Control", "iTunes")
            os.makedirs(db_dir)
            db_path = os.path.join(db_dir, "iTunesDB")
            with open(db_path, 'wb') as f:
                f.write(b'mhbd' + b'\x00' * 100)

            info = copier.get_ipod_info(temp_dir)

            assert info["music_folders"] == 5
            assert info["total_music_files"] == 50  # 5 folders * 10 files
            assert info["database_found"] is True
            assert info["database_size"] == 104  # 4 bytes header + 100 bytes


class TestMainIntegration:
    """Test main function integration."""

    def test_main_no_ipod(self):
        """Test main when no iPod is found."""
        with patch('ipodyssey.copier.detect_ipod', return_value=None):
            result = copier.main()
            assert result == 1

    def test_main_successful_copy(self):
        """Test successful main execution."""
        mock_ipod_path = "/Volumes/TEST_IPOD"
        mock_copied_files = {
            "iTunesDB": "/tmp/backup/iTunesDB"
        }
        mock_info = {
            "music_folders": 10,
            "total_music_files": 500
        }

        with patch('ipodyssey.copier.detect_ipod', return_value=mock_ipod_path), \
             patch('ipodyssey.copier.get_ipod_info', return_value=mock_info), \
             patch('ipodyssey.copier.copy_database_files', return_value=mock_copied_files), \
             patch('ipodyssey.copier.verify_database_integrity', return_value=(True, "Valid")):

            result = copier.main()
            assert result == 0


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])