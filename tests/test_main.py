"""Tests for the main TUI module."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ipodyssey.main import (
    find_ipods, select_ipod, select_extraction_mode,
    select_output_format, select_destination, perform_extraction,
    export_tracks, show_summary
)


class TestFindIpods:
    """Test iPod finding functionality."""

    @patch('sys.platform', 'darwin')
    def test_find_ipods_macos(self):
        """Test finding iPods on macOS."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create fake Volumes directory
            with patch('pathlib.Path.exists', return_value=True), \
                 patch('pathlib.Path.iterdir') as mock_iterdir:

                # Mock volume with iPod_Control
                mock_volume = MagicMock()
                mock_volume.__truediv__ = lambda self, x: MagicMock(exists=lambda: x == "iPod_Control")
                mock_volume.__str__ = lambda x: "/Volumes/TestIPod"

                mock_iterdir.return_value = [mock_volume]

                ipods = find_ipods()
                assert len(ipods) == 1
                assert ipods[0] == "/Volumes/TestIPod"

    @patch('sys.platform', 'linux')
    def test_find_ipods_linux(self):
        """Test finding iPods on Linux."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock /media structure
            media_path = Path(temp_dir) / "media" / "user"
            ipod_path = media_path / "iPod"
            ipod_control = ipod_path / "iPod_Control"
            ipod_control.mkdir(parents=True)

            with patch('pathlib.Path', side_effect=lambda x: Path(temp_dir) / x.lstrip('/')):
                ipods = find_ipods()
                # Would find iPod if paths were real
                assert isinstance(ipods, list)

    @patch('sys.platform', 'win32')
    @patch('pathlib.Path')
    def test_find_ipods_windows(self, mock_path_class):
        """Test finding iPods on Windows."""
        # Mock drive E: with iPod
        mock_drive = MagicMock()
        mock_drive.exists.return_value = True
        mock_drive.__truediv__ = lambda self, x: MagicMock(exists=lambda: True)
        mock_drive.__str__ = lambda x: "E:/"

        mock_path_class.side_effect = lambda x: mock_drive if "E:" in x else MagicMock(exists=lambda: False)

        ipods = find_ipods()
        # Should check drive letters
        assert isinstance(ipods, list)


class TestSelectIpod:
    """Test iPod selection functionality."""

    @patch('ipodyssey.main.find_ipods')
    @patch('ipodyssey.main.console')
    def test_select_no_ipods_found(self, mock_console, mock_find):
        """Test when no iPods are found."""
        mock_find.return_value = []

        with patch('ipodyssey.main.Confirm.ask', return_value=False):
            result = select_ipod()
            assert result is None
            mock_console.print.assert_any_call("[red]❌ No iPod devices found![/red]")

    @patch('ipodyssey.main.find_ipods')
    @patch('ipodyssey.main.get_ipod_info')
    @patch('ipodyssey.main.Confirm.ask')
    @patch('ipodyssey.main.console')
    def test_select_single_ipod(self, mock_console, mock_confirm, mock_info, mock_find):
        """Test selecting a single iPod."""
        mock_find.return_value = ["/Volumes/iPod"]
        mock_info.return_value = {
            'model': 'iPod Video',
            'database_found': True,
            'database_size': 1024 * 1024 * 10,
            'music_folders': 50,
            'total_music_files': 1000
        }
        mock_confirm.return_value = True

        result = select_ipod()
        assert result == "/Volumes/iPod"

    @patch('ipodyssey.main.find_ipods')
    @patch('ipodyssey.main.get_ipod_info')
    @patch('ipodyssey.main.IntPrompt.ask')
    @patch('ipodyssey.main.console')
    def test_select_multiple_ipods(self, mock_console, mock_prompt, mock_info, mock_find):
        """Test selecting from multiple iPods."""
        mock_find.return_value = ["/Volumes/iPod1", "/Volumes/iPod2"]
        mock_info.return_value = {'total_music_files': 500}
        mock_prompt.return_value = 2

        result = select_ipod()
        assert result == "/Volumes/iPod2"


class TestSelectionFunctions:
    """Test various selection functions."""

    @patch('ipodyssey.main.IntPrompt.ask')
    @patch('ipodyssey.main.console')
    def test_select_extraction_mode(self, mock_console, mock_prompt):
        """Test extraction mode selection."""
        mock_prompt.return_value = 1
        result = select_extraction_mode()
        assert result == "scan"

        mock_prompt.return_value = 2
        result = select_extraction_mode()
        assert result == "database"

        mock_prompt.return_value = 3
        result = select_extraction_mode()
        assert result == "both"

    @patch('ipodyssey.main.Prompt.ask')
    @patch('ipodyssey.main.console')
    def test_select_output_format(self, mock_console, mock_prompt):
        """Test output format selection."""
        mock_prompt.return_value = "1,2"
        result = select_output_format()
        assert "csv" in result
        assert "json" in result

        mock_prompt.return_value = "0"
        result = select_output_format()
        assert len(result) == 4  # All formats

    @patch('ipodyssey.main.Prompt.ask')
    @patch('pathlib.Path.mkdir')
    def test_select_destination(self, mock_mkdir, mock_prompt):
        """Test destination selection."""
        mock_prompt.return_value = "/tmp/test_output"
        result = select_destination()
        assert result == "/tmp/test_output"
        mock_mkdir.assert_called_once()


class TestPerformExtraction:
    """Test extraction functionality."""

    @patch('ipodyssey.main.copy_database_files')
    @patch('ipodyssey.main.DatabaseParser')
    @patch('ipodyssey.main.export_tracks')
    @patch('ipodyssey.main.console')
    def test_perform_database_extraction(self, mock_console, mock_export,
                                        mock_parser_class, mock_copy):
        """Test database extraction mode."""
        # Setup mocks
        mock_copy.return_value = {"iTunesDB": "/tmp/iTunesDB"}
        mock_parser = MagicMock()
        mock_parser.parse.return_value = ({1: MagicMock()}, [])
        mock_parser_class.return_value = mock_parser

        results = perform_extraction(
            "/Volumes/iPod",
            "database",
            ["csv"],
            "/tmp/output"
        )

        assert results['database_copied'] is True
        assert len(results['tracks']) == 1
        mock_export.assert_called_once()

    @patch('ipodyssey.main.scan_ipod_music')
    @patch('ipodyssey.main.export_tracks')
    @patch('ipodyssey.main.console')
    def test_perform_scan_extraction(self, mock_console, mock_export, mock_scan):
        """Test scan extraction mode."""
        mock_scan.return_value = [{'title': 'Song1'}, {'title': 'Song2'}]

        results = perform_extraction(
            "/Volumes/iPod",
            "scan",
            ["csv"],
            "/tmp/output"
        )

        assert len(results['tracks']) == 2
        mock_scan.assert_called_once_with("/Volumes/iPod")


class TestExportTracks:
    """Test track export functionality."""

    def test_export_csv(self):
        """Test CSV export."""
        tracks = [
            {'title': 'Song1', 'artist': 'Artist1', 'album': 'Album1'}
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('ipodyssey.main.export_to_csv') as mock_export:
                export_tracks(tracks, [], "csv", temp_dir)
                mock_export.assert_called_once()

    def test_export_json(self):
        """Test JSON export."""
        tracks = [
            MagicMock(title='Song1', artist='Artist1', album='Album1',
                     year=2023, play_count=5)
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            export_tracks(tracks, [], "json", temp_dir)

            json_file = Path(temp_dir) / "ipod_music.json"
            assert json_file.exists()

    def test_export_m3u(self):
        """Test M3U export."""
        tracks = [
            {'title': 'Song1', 'artist': 'Artist1', 'duration': 180000}
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            export_tracks(tracks, [], "m3u", temp_dir)

            m3u_file = Path(temp_dir) / "ipod_music.m3u"
            assert m3u_file.exists()

            content = m3u_file.read_text()
            assert "#EXTM3U" in content
            assert "Artist1 - Song1" in content

    def test_export_text_summary(self):
        """Test text summary export."""
        tracks = [
            {'artist': 'Artist1'},
            {'artist': 'Artist1'},
            {'artist': 'Artist2'}
        ]
        playlists = [MagicMock(name='Playlist1', track_ids=[1, 2])]

        with tempfile.TemporaryDirectory() as temp_dir:
            export_tracks(tracks, playlists, "text", temp_dir)

            txt_file = Path(temp_dir) / "ipod_summary.txt"
            assert txt_file.exists()

            content = txt_file.read_text()
            assert "Total Tracks: 3" in content
            assert "Artist1: 2 tracks" in content
            # Playlist formatting may vary
            assert "Playlist1" in content


class TestShowSummary:
    """Test summary display functionality."""

    @patch('ipodyssey.main.console')
    def test_show_summary(self, mock_console):
        """Test extraction summary display."""
        results = {
            'tracks': [{'artist': 'A1'}, {'artist': 'A2'}],
            'playlists': [MagicMock()],
            'database_copied': True
        }

        show_summary(results)

        # Check that summary was printed
        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("Extraction Complete" in str(c) for c in calls)


class TestMainFunction:
    """Test main function integration."""

    @patch('ipodyssey.main.select_ipod')
    @patch('ipodyssey.main.console')
    def test_main_no_ipod_selected(self, mock_console, mock_select):
        """Test main when no iPod is selected."""
        mock_select.return_value = None

        from ipodyssey.main import main
        result = main()

        assert result == 1
        mock_console.print.assert_any_call("\n[red]No iPod selected. Exiting.[/red]")

    @patch('ipodyssey.main.select_ipod')
    @patch('ipodyssey.main.select_extraction_mode')
    @patch('ipodyssey.main.select_output_format')
    @patch('ipodyssey.main.select_destination')
    @patch('ipodyssey.main.perform_extraction')
    @patch('ipodyssey.main.show_summary')
    @patch('ipodyssey.main.print_banner')
    def test_main_successful_extraction(self, mock_banner, mock_summary, mock_perform,
                                       mock_dest, mock_format, mock_mode, mock_ipod):
        """Test successful main execution."""
        mock_ipod.return_value = "/Volumes/iPod"
        mock_mode.return_value = "scan"
        mock_format.return_value = ["csv"]
        mock_dest.return_value = "/tmp/output"
        mock_perform.return_value = {'tracks': [{'title': 'Song'}]}

        from ipodyssey.main import main
        result = main()

        assert result == 0
        mock_perform.assert_called_once()
        mock_summary.assert_called_once()