"""
iPod file system explorer and mapper.

This module analyzes the copied iPod structure to understand:
1. Music file distribution across F00-F49 folders
2. File naming patterns (4-character codes)
3. Database file locations and sizes
4. Total music collection statistics

Key functions to implement:
- map_ipod_structure(): Create a map of all iPod directories
- analyze_music_folders(): Count and categorize music files
- find_database_files(): Locate all iTunes database files
- generate_report(): Create detailed structure report

Interesting things to discover:
- Why F00-F49? (iTunes uses a hash to distribute files)
- File naming scheme (prevents browsing via file manager)
- Hidden metadata in file system attributes
"""