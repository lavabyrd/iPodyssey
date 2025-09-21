#!/bin/bash
# Demo script showing iPodyssey TUI options

# Auto-select options for demo:
# - Yes to use iPod
# - Option 1 (Scan music files)
# - Option 1 (CSV for Soundiiz)
# - Default output directory

echo "y
1
1
" | uv run python -m ipodyssey