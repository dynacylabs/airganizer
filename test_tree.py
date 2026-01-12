"""Quick test script for tree structure generation."""

import json
import tempfile
import os
from pathlib import Path
from airganizer.scanner import FileScanner

# Create a test directory structure
test_dir = Path(tempfile.mkdtemp())
print(f"Test directory: {test_dir}")

# Create test structure
(test_dir / "readme.txt").write_text("Hello")
(test_dir / "data.csv").write_text("col1,col2\n1,2")
(test_dir / "docs").mkdir()
(test_dir / "docs" / "report.pdf").write_text("PDF content")
(test_dir / "docs" / "notes.txt").write_text("Notes")
(test_dir / "photos").mkdir()
(test_dir / "photos" / "vacation").mkdir()
(test_dir / "photos" / "img1.jpg").write_text("JPG")
(test_dir / "photos" / "vacation" / "beach.png").write_text("PNG")

# Test the scanner
scanner = FileScanner(str(test_dir))
tree = scanner.build_tree_structure()

print("\n" + "=" * 60)
print("TREE STRUCTURE:")
print("=" * 60)
print(json.dumps(tree, indent=2))

print("\n" + "=" * 60)
print("SUMMARY:")
print("=" * 60)
summary = tree['summary']
print(f"Total files: {summary['total_files']}")
print(f"Total directories: {summary['total_directories']}")
print(f"Total size: {summary['total_size_bytes']} bytes ({summary['total_size_mb']} MB)")
print(f"\nFile types:")
for ext, count in summary['extensions'].items():
    print(f"  {ext}: {count}")

# Cleanup
import shutil
shutil.rmtree(test_dir)
print(f"\n✓ Test completed successfully!")
