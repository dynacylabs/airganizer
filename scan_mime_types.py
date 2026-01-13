#!/usr/bin/env python3
"""
Script to recursively scan a directory and count files by MIME type.
Uses libmagic for definitive MIME type detection (not guessing).
"""

import os
import sys
from pathlib import Path
from collections import defaultdict
import magic


def scan_directory(directory_path):
    """
    Recursively scan a directory and count files by MIME type.
    
    Args:
        directory_path: Path to the directory to scan
        
    Returns:
        Dictionary mapping MIME types to file counts
    """
    mime_counts = defaultdict(int)
    mime_detector = magic.Magic(mime=True)
    
    # Convert to Path object
    root_path = Path(directory_path).resolve()
    
    if not root_path.exists():
        print(f"Error: Directory '{directory_path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not root_path.is_dir():
        print(f"Error: '{directory_path}' is not a directory", file=sys.stderr)
        sys.exit(1)
    
    print(f"Scanning directory: {root_path}")
    print("-" * 60)
    
    # Walk through directory tree
    for file_path in root_path.rglob('*'):
        # Skip directories, only process files
        if file_path.is_file():
            try:
                # Get MIME type using libmagic
                mime_type = mime_detector.from_file(str(file_path))
                mime_counts[mime_type] += 1
            except Exception as e:
                # Handle files that can't be read
                print(f"Warning: Could not determine MIME type for {file_path}: {e}", file=sys.stderr)
                mime_counts['error/unknown'] += 1
    
    return mime_counts


def print_results(mime_counts):
    """
    Print the MIME type counts in a formatted table.
    
    Args:
        mime_counts: Dictionary mapping MIME types to counts
    """
    if not mime_counts:
        print("No files found.")
        return
    
    # Sort by count (descending), then by MIME type (ascending)
    sorted_counts = sorted(mime_counts.items(), key=lambda x: (-x[1], x[0]))
    
    # Calculate total
    total_files = sum(mime_counts.values())
    
    # Print results
    print("\nMIME Type Distribution:")
    print("=" * 60)
    print(f"{'MIME Type':<40} {'Count':>10}")
    print("-" * 60)
    
    for mime_type, count in sorted_counts:
        percentage = (count / total_files) * 100
        print(f"{mime_type:<40} {count:>10} ({percentage:>5.1f}%)")
    
    print("-" * 60)
    print(f"{'TOTAL':<40} {total_files:>10}")
    print("=" * 60)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python mime_counter.py <directory_path>")
        print("\nExample:")
        print("  python mime_counter.py /path/to/directory")
        sys.exit(1)
    
    directory_path = sys.argv[1]
    
    # Scan directory and count MIME types
    mime_counts = scan_directory(directory_path)
    
    # Print results
    print_results(mime_counts)


if __name__ == "__main__":
    main()
