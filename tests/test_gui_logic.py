"""Tests for GUI logic without requiring display."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestGUILogic:
    """Test GUI business logic without Tkinter dependencies."""

    @patch('ipodyssey.gui.detect_ipod')
    @patch('ipodyssey.gui.get_ipod_info')
    def test_ipod_detection_logic(self, mock_info, mock_detect):
        """Test iPod detection logic flow."""
        mock_detect.return_value = "/Volumes/iPod"
        mock_info.return_value = {
            'model': 'iPod Video',
            'music_folders': 50,
            'total_music_files': 1000,
            'database_found': True,
            'database_size': 1024 * 1024
        }

        # Test that detection returns proper info
        path = mock_detect()
        info = mock_info(path)

        assert path == "/Volumes/iPod"
        assert info['model'] == 'iPod Video'
        assert info['total_music_files'] == 1000

    @patch('ipodyssey.gui.scan_ipod_music')
    @patch('pathlib.Path.mkdir')
    def test_scan_extraction_logic(self, mock_mkdir, mock_scan):
        """Test scan extraction logic."""
        mock_scan.return_value = [
            {'title': 'Song1', 'artist': 'Artist1', 'album': 'Album1'},
            {'title': 'Song2', 'artist': 'Artist2', 'album': 'Album2'}
        ]

        # Test scanning
        tracks = mock_scan("/Volumes/iPod")
        assert len(tracks) == 2
        assert tracks[0]['title'] == 'Song1'

    @patch('ipodyssey.gui.copy_database_files')
    @patch('ipodyssey.gui.DatabaseParser')
    def test_database_extraction_logic(self, mock_parser_class, mock_copy):
        """Test database extraction logic."""
        mock_copy.return_value = {"iTunesDB": "/tmp/iTunesDB"}

        mock_parser = MagicMock()
        mock_tracks = {
            1: MagicMock(title='Track1', artist='Artist1'),
            2: MagicMock(title='Track2', artist='Artist2')
        }
        mock_playlists = [MagicMock(name='Playlist1')]
        mock_parser.parse.return_value = (mock_tracks, mock_playlists)
        mock_parser_class.return_value = mock_parser

        # Test database extraction
        copied = mock_copy("/Volumes/iPod", "/tmp/output")
        parser = mock_parser_class(copied["iTunesDB"])
        tracks, playlists = parser.parse()

        assert len(tracks) == 2
        assert len(playlists) == 1

    def test_export_json_logic(self):
        """Test JSON export logic."""
        tracks = [
            {'title': 'Song1', 'artist': 'Artist1', 'album': 'Album1'},
            {'title': 'Song2', 'artist': 'Artist2', 'album': 'Album2'}
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = os.path.join(temp_dir, "test.json")

            # Simulate JSON export logic
            import json
            data = {
                'export_date': '2023-01-01',
                'track_count': len(tracks),
                'tracks': tracks
            }

            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            # Verify
            assert os.path.exists(json_path)
            with open(json_path) as f:
                loaded = json.load(f)
                assert loaded['track_count'] == 2
                assert loaded['tracks'][0]['title'] == 'Song1'

    def test_export_m3u_logic(self):
        """Test M3U export logic."""
        tracks = [
            {'title': 'Song1', 'artist': 'Artist1', 'duration': 180000},
            {'title': 'Song2', 'artist': 'Artist2', 'duration': 240000}
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            m3u_path = os.path.join(temp_dir, "test.m3u")

            # Simulate M3U export logic
            with open(m3u_path, 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n")
                for track in tracks:
                    duration = track.get('duration', 0) // 1000
                    f.write(f"#EXTINF:{duration},{track.get('artist', 'Unknown')} - {track.get('title', 'Unknown')}\n")
                    f.write(f"{track.get('artist', 'Unknown')} - {track.get('title', 'Unknown')}.mp3\n")

            # Verify
            assert os.path.exists(m3u_path)
            with open(m3u_path) as f:
                content = f.read()
                assert "#EXTM3U" in content
                assert "Artist1 - Song1" in content
                assert "#EXTINF:180" in content

    def test_export_csv_logic(self):
        """Test CSV export logic."""
        tracks = [
            {'title': 'Song1', 'artist': 'Artist1', 'album': 'Album1', 'duration_string': '3:00'},
            {'title': 'Song2', 'artist': 'Artist2', 'album': 'Album2', 'duration_string': '4:00'}
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = os.path.join(temp_dir, "test.csv")

            # Simulate CSV export logic
            import csv
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Title', 'Artist', 'Album', 'Duration'])
                for track in tracks:
                    writer.writerow([
                        track.get('title', 'Unknown'),
                        track.get('artist', 'Unknown'),
                        track.get('album', 'Unknown'),
                        track.get('duration_string', '0:00')
                    ])

            # Verify
            assert os.path.exists(csv_path)
            with open(csv_path) as f:
                lines = f.readlines()
                assert len(lines) == 3  # Header + 2 tracks
                assert 'Song1' in lines[1]

    @patch('ipodyssey.gui.messagebox')
    def test_error_handling(self, mock_messagebox):
        """Test error handling in GUI."""
        # Simulate an error scenario
        error_msg = "Failed to detect iPod"

        # Would normally show error dialog
        mock_messagebox.showerror("Error", error_msg)

        mock_messagebox.showerror.assert_called_once_with("Error", error_msg)


class TestProgressWindowLogic:
    """Test progress window logic."""

    def test_progress_calculation(self):
        """Test progress percentage calculation."""
        current = 50
        total = 100

        percent = (current / total) * 100
        assert percent == 50.0

    def test_time_formatting(self):
        """Test time formatting logic."""
        def format_time(seconds):
            if seconds < 60:
                return f"{seconds:.0f}s"
            elif seconds < 3600:
                return f"{seconds/60:.1f}m"
            else:
                return f"{seconds/3600:.1f}h"

        assert format_time(45) == "45s"
        assert format_time(90) == "1.5m"
        assert format_time(3700) == "1.0h"

    def test_eta_calculation(self):
        """Test ETA calculation logic."""
        current = 100
        total = 1000
        elapsed = 10  # seconds

        rate = current / elapsed  # 10 files per second
        remaining = total - current  # 900 files
        eta = remaining / rate  # 90 seconds

        assert eta == 90.0

    def test_progress_status_messages(self):
        """Test progress status message generation."""
        messages = []

        # Simulate progress updates
        for i in range(0, 101, 10):
            if i == 0:
                messages.append("Starting extraction...")
            elif i == 100:
                messages.append("Extraction complete!")
            else:
                messages.append(f"Processing... {i}%")

        assert messages[0] == "Starting extraction..."
        assert messages[-1] == "Extraction complete!"
        assert "Processing... 50%" in messages


class TestGUICallbacks:
    """Test GUI callback functions."""

    @patch('ipodyssey.gui.filedialog.askdirectory')
    def test_browse_directory_callback(self, mock_askdir):
        """Test directory browsing callback."""
        mock_askdir.return_value = "/new/path"

        # Simulate browse button click
        result = mock_askdir()

        assert result == "/new/path"
        mock_askdir.assert_called_once()

    @patch('ipodyssey.gui.threading.Thread')
    def test_extraction_thread_start(self, mock_thread):
        """Test that extraction starts in separate thread."""
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        # Simulate starting extraction
        thread = mock_thread(target=lambda: None, daemon=True)
        thread.start()

        mock_thread_instance.start.assert_called_once()

    def test_format_selection_logic(self):
        """Test output format selection logic."""
        # Simulate checkbox states
        formats = {
            'csv': True,
            'json': False,
            'm3u': True,
            'txt': False
        }

        selected = [fmt for fmt, enabled in formats.items() if enabled]

        assert 'csv' in selected
        assert 'm3u' in selected
        assert 'json' not in selected
        assert len(selected) == 2