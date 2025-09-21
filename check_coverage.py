#!/usr/bin/env python3
"""Check test coverage for iPodyssey modules."""

import os
from pathlib import Path

# Get all Python modules in ipodyssey/
ipodyssey_dir = Path("ipodyssey")
modules = set()
for file in ipodyssey_dir.glob("*.py"):
    if file.name != "__init__.py":
        modules.add(file.stem)

# Also check subdirectories
for file in ipodyssey_dir.glob("**/*.py"):
    if "__pycache__" not in str(file) and file.name != "__init__.py":
        relative = file.relative_to(ipodyssey_dir)
        modules.add(str(relative.with_suffix("")))

# Get all test files
test_dir = Path("tests")
tested_modules = set()

for test_file in test_dir.glob("test_*.py"):
    # Extract module name from test file name
    module_name = test_file.stem.replace("test_", "")
    if module_name != "placeholder":
        tested_modules.add(module_name)

# Check coverage
print("=== TEST COVERAGE ANALYSIS ===\n")

print("✅ Modules with tests:")
for module in sorted(tested_modules):
    if module in modules or f"database/{module}" in modules:
        print(f"  - {module}")

print("\n❌ Modules WITHOUT tests:")
untested = modules - tested_modules
# Account for database submodules
untested = [m for m in untested if m.replace("database/", "") not in tested_modules]
for module in sorted(untested):
    print(f"  - {module}")

print(f"\n📊 Coverage: {len(tested_modules)}/{len(modules)} modules tested")

# Check what functionality each test covers
print("\n=== FUNCTIONALITY TESTED ===")
test_functions = []
for test_file in test_dir.glob("test_*.py"):
    with open(test_file) as f:
        for line in f:
            if "def test_" in line:
                func = line.strip().split("def test_")[1].split("(")[0]
                test_functions.append((test_file.stem, func))

functionality = {}
for test_file, func in test_functions:
    if test_file not in functionality:
        functionality[test_file] = []
    functionality[test_file].append(func)

for test_file in sorted(functionality.keys()):
    print(f"\n{test_file}:")
    for func in functionality[test_file]:
        print(f"  - {func}")