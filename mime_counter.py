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
from tqdm import tqdm


def get_detailed_mime_type(file_path, mime_detector, mime_encoding_detector, description_detector):
    """
    Get the most specific MIME type possible for a file.
    Uses multiple detection methods to avoid generic octet-stream results.
    
    Args:
        file_path: Path to the file
        mime_detector: Magic instance for MIME detection
        mime_encoding_detector: Magic instance for MIME with encoding
        description_detector: Magic instance for text description
        
    Returns:
        Most specific MIME type found
    """
    try:
        # First attempt: standard MIME detection
        mime_type = mime_detector.from_file(str(file_path))
        
        # If we get generic octet-stream, try to be more specific
        if mime_type == 'application/octet-stream':
            # Get file description for additional clues
            description = description_detector.from_file(str(file_path))
            description_lower = description.lower()
            
            # Check for specific binary formats by description
            if 'executable' in description_lower or 'ELF' in description:
                mime_type = 'application/x-executable'
            elif 'archive' in description_lower:
                if 'zip' in description_lower:
                    mime_type = 'application/zip'
                elif 'tar' in description_lower:
                    mime_type = 'application/x-tar'
                else:
                    mime_type = 'application/x-archive'
            elif 'data' in description_lower:
                # Try with encoding detection
                mime_with_encoding = mime_encoding_detector.from_file(str(file_path))
                if mime_with_encoding != 'application/octet-stream':
                    mime_type = mime_with_encoding.split(';')[0].strip()
        
        return mime_type
        
    except Exception as e:
        raise e


def scan_directory(directory_path):
    """
    Recursively scan a directory and count files by MIME type.
    
    Args:
        directory_path: Path to the directory to scan
        
    Returns:
        Dictionary mapping MIME types to file counts
    """
    mime_counts = defaultdict(int)
    
    # Create multiple magic detectors for better accuracy
    mime_detector = magic.Magic(mime=True, uncompress=True)
    mime_encoding_detector = magic.Magic(mime_encoding=True)
    description_detector = magic.Magic()
    
    # Convert to Path object
    root_path = Path(directory_path).resolve()
    
    if not root_path.exists():
        print(f"Error: Directory '{directory_path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not root_path.is_dir():
        print(f"Error: '{directory_path}' is not a directory", file=sys.stderr)
        sys.exit(1)
    
    print(f"Scanning directory: {root_path}")
    print("Counting files...")
    
    # First, collect all file paths to get total count
    file_paths = [f for f in root_path.rglob('*') if f.is_file()]
    total_files = len(file_paths)
    
    print(f"Found {total_files} files to process")
    print("-" * 60)
    
    # Process files with progress bar
    for file_path in tqdm(file_paths, desc="Processing files", unit="file"):
        try:
            # Get detailed MIME type using multiple detection methods
            mime_type = get_detailed_mime_type(
                file_path, 
                mime_detector, 
                mime_encoding_detector, 
                description_detector
            )
            mime_counts[mime_type] += 1
        except Exception as e:
            # Handle files that can't be read
            tqdm.write(f"Warning: Could not determine MIME type for {file_path}: {e}")
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
