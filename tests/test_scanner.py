"""Tests for the scanner module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ipodyssey.scanner import scan_ipod_music, export_to_csv


class TestScanIpodMusic:
    """Test iPod music scanning functionality."""

    def test_scan_no_music_folder(self):
        """Test scanning when music folder doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # No iPod_Control folder
            tracks = scan_ipod_music(temp_dir)
            assert tracks == []

    def test_scan_empty_music_folder(self):
        """Test scanning when music folder exists but is empty."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create empty music folder structure
            music_path = Path(temp_dir) / "iPod_Control" / "Music"
            music_path.mkdir(parents=True)

            tracks = scan_ipod_music(temp_dir)
            assert tracks == []

    def test_scan_with_mp3_file(self):
        """Test scanning MP3 files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create iPod music structure
            music_path = Path(temp_dir) / "iPod_Control" / "Music" / "F00"
            music_path.mkdir(parents=True)

            # Create a fake MP3 file
            mp3_file = music_path / "TEST.mp3"
            mp3_file.write_bytes(b'fake_mp3_data')

            # Mock mutagen to return metadata
            mock_audio = MagicMock()
            mock_audio.info.length = 180.5  # 3 minutes
            mock_audio.info.bitrate = 192000
            mock_audio.info.sample_rate = 44100
            mock_audio.get = MagicMock(side_effect=lambda key, default: {
                'TPE1': ['Test Artist'],
                'TIT2': ['Test Song'],
                'TALB': ['Test Album'],
                'TDRC': ['2023'],
                'TCON': ['Rock'],
                'TRCK': ['1'],
            }.get(key, default))

            with patch('mutagen.File', return_value=mock_audio), \
                 patch('ipodyssey.scanner.isinstance', side_effect=lambda obj, cls: cls.__name__ == 'MP3'):

                tracks = scan_ipod_music(temp_dir)

                assert len(tracks) == 1
                track = tracks[0]
                assert track['artist'] == 'Test Artist'
                assert track['title'] == 'Test Song'
                assert track['album'] == 'Test Album'
                assert track['duration'] == 180500  # milliseconds
                assert track['duration_string'] == '3:00'

    def test_scan_with_m4a_file(self):
        """Test scanning M4A/AAC files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create iPod music structure
            music_path = Path(temp_dir) / "iPod_Control" / "Music" / "F01"
            music_path.mkdir(parents=True)

            # Create a fake M4A file
            m4a_file = music_path / "TEST.m4a"
            m4a_file.write_bytes(b'fake_m4a_data')

            # Mock mutagen for M4A
            mock_audio = MagicMock()
            mock_audio.info.length = 240.0  # 4 minutes
            mock_audio.info.bitrate = 256000
            mock_audio.get = MagicMock(side_effect=lambda key, default: {
                '©ART': ['M4A Artist'],
                '©nam': ['M4A Song'],
                '©alb': ['M4A Album'],
                '©day': ['2024'],
                '©gen': ['Pop'],
                'trkn': [(2, 10)],
            }.get(key, default))

            with patch('mutagen.File', return_value=mock_audio), \
                 patch('ipodyssey.scanner.isinstance', side_effect=lambda obj, cls: cls.__name__ == 'MP4'):

                tracks = scan_ipod_music(temp_dir)

                assert len(tracks) == 1
                track = tracks[0]
                assert track['artist'] == 'M4A Artist'
                assert track['title'] == 'M4A Song'
                assert track['album'] == 'M4A Album'

    def test_scan_with_progress_callback(self):
        """Test scanning with progress callback."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create iPod music structure with multiple files
            for folder_num in range(3):
                music_path = Path(temp_dir) / "iPod_Control" / "Music" / f"F{folder_num:02d}"
                music_path.mkdir(parents=True)

                for file_num in range(5):
                    mp3_file = music_path / f"FILE{file_num}.mp3"
                    mp3_file.write_bytes(b'fake_mp3_data')

            progress_calls = []

            def progress_callback(current, total, message):
                progress_calls.append((current, total, message))

            # Mock mutagen to return None (files will be skipped)
            with patch('mutagen.File', return_value=None):
                tracks = scan_ipod_music(temp_dir, progress_callback)

                # Check that progress was reported
                assert len(progress_calls) > 0

                # Check initial counting message
                assert any("Found" in call[2] and "files to scan" in call[2]
                          for call in progress_calls)

                # Check completion message
                assert progress_calls[-1][2].startswith("Completed!")

    def test_scan_handles_corrupt_file(self):
        """Test scanning handles corrupt audio files gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            music_path = Path(temp_dir) / "iPod_Control" / "Music" / "F00"
            music_path.mkdir(parents=True)

            # Create multiple files
            good_file = music_path / "GOOD.mp3"
            good_file.write_bytes(b'good_data')

            bad_file = music_path / "BAD.mp3"
            bad_file.write_bytes(b'bad_data')

            def mutagen_side_effect(path):
                if "BAD" in str(path):
                    raise Exception("Corrupt file")
                mock = MagicMock()
                mock.info.length = 100
                mock.get = MagicMock(return_value=['Test'])
                return mock

            with patch('mutagen.File', side_effect=mutagen_side_effect):
                # Should handle the error and continue
                tracks = scan_ipod_music(temp_dir)

                # Only good file should be processed
                assert len(tracks) == 1

    def test_scan_multiple_folders(self):
        """Test scanning across multiple F00-F49 folders."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_count = 0

            # Create F00 through F05 folders
            for folder_num in range(6):
                music_path = Path(temp_dir) / "iPod_Control" / "Music" / f"F{folder_num:02d}"
                music_path.mkdir(parents=True)

                # Add 2 files to each folder
                for i in range(2):
                    mp3_file = music_path / f"SONG{file_count}.mp3"
                    mp3_file.write_bytes(b'data')
                    file_count += 1

            # Mock mutagen to return valid audio
            mock_audio = MagicMock()
            mock_audio.info.length = 100
            mock_audio.get = MagicMock(return_value=['Value'])

            with patch('mutagen.File', return_value=mock_audio):
                tracks = scan_ipod_music(temp_dir)

                # Should find all 12 files
                assert len(tracks) == 12


class TestExportToCSV:
    """Test CSV export functionality."""

    def test_export_empty_tracks(self):
        """Test exporting empty track list."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        try:
            export_to_csv([], output_path)

            # Check file was created with header only
            with open(output_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 1  # Header only
                assert 'Title,Artist,Album,Duration' in lines[0]
        finally:
            os.unlink(output_path)

    def test_export_tracks_to_csv(self):
        """Test exporting tracks to CSV."""
        tracks = [
            {
                'title': 'Song 1',
                'artist': 'Artist 1',
                'album': 'Album 1',
                'duration_string': '3:45'
            },
            {
                'title': 'Song 2',
                'artist': 'Artist 2',
                'album': 'Album 2',
                'duration_string': '4:20'
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        try:
            export_to_csv(tracks, output_path)

            # Check CSV content
            with open(output_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 3  # Header + 2 tracks
                assert 'Song 1,Artist 1,Album 1,3:45' in lines[1]
                assert 'Song 2,Artist 2,Album 2,4:20' in lines[2]
        finally:
            os.unlink(output_path)

    def test_export_handles_special_characters(self):
        """Test CSV export handles special characters."""
        tracks = [
            {
                'title': 'Song, with comma',
                'artist': 'Artist "quoted"',
                'album': 'Album\nwith\nnewline',
                'duration_string': '2:30'
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        try:
            export_to_csv(tracks, output_path)

            # CSV should properly escape special characters
            with open(output_path, 'r') as f:
                content = f.read()
                assert 'Song, with comma' in content or '"Song, with comma"' in content
        finally:
            os.unlink(output_path)

    def test_export_missing_fields(self):
        """Test export handles tracks with missing fields."""
        tracks = [
            {
                'title': 'Only Title'
                # Missing artist, album, duration
            },
            {
                'artist': 'Only Artist'
                # Missing title, album, duration
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        try:
            export_to_csv(tracks, output_path)

            with open(output_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 3
                # Should use 'Unknown' for missing fields
                assert 'Unknown' in lines[1]
                assert 'Unknown' in lines[2]
        finally:
            os.unlink(output_path)


class TestScannerIntegration:
    """Integration tests for scanner module."""

    def test_scan_realistic_ipod_structure(self):
        """Test scanning a realistic iPod folder structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create realistic iPod structure
            ipod_control = Path(temp_dir) / "iPod_Control"
            ipod_control.mkdir()

            # Create iTunes folder
            itunes_folder = ipod_control / "iTunes"
            itunes_folder.mkdir()

            # Create Music folders F00-F49
            music_folder = ipod_control / "Music"
            music_folder.mkdir()

            for i in range(50):
                folder = music_folder / f"F{i:02d}"
                folder.mkdir()

                # Add one dummy file to first folder only
                if i == 0:
                    (folder / "TEST.mp3").write_bytes(b'test')

            # Mock mutagen
            with patch('mutagen.File', return_value=None):
                tracks = scan_ipod_music(temp_dir)
                # Should complete without errors
                assert isinstance(tracks, list)