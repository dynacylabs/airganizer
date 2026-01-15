#!/usr/bin/env python3
"""
Script to recursively scan a directory and move all MP3 files (based on MIME type) to a specified folder.
Uses multiple detection methods to accurately identify MP3 files.
"""

import os
import sys
import shutil
import argparse
import subprocess
from pathlib import Path
from collections import defaultdict
import magic
from tqdm import tqdm


def identify_with_file_command(file_path):
    """
    Use the file command with MIME type detection.
    """
    try:
        result = subprocess.run(
            ['file', '--mime-type', '-b', str(file_path)],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            mime_type = result.stdout.strip()
            return mime_type
                
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return None


def identify_by_content_analysis(file_path):
    """
    Analyze file content for MP3 magic bytes and patterns.
    """
    try:
        with open(file_path, 'rb') as f:
            header = f.read(512)  # Read first 512 bytes
            
            if len(header) < 2:
                return None
            
            # MP3 files can start with ID3 tag or MPEG audio frame sync
            if header.startswith(b'ID3'):
                return 'audio/mpeg'
            
            # MPEG audio frame sync (0xFFE or 0xFFF)
            # MP3 files often start with 0xFF 0xFB or 0xFF 0xFA
            if len(header) >= 2 and header[0] == 0xFF and (header[1] & 0xE0) == 0xE0:
                return 'audio/mpeg'
            
    except (IOError, OSError):
        pass
    
    return None


def get_mime_type(file_path):
    """
    Get MIME type using multiple detection methods.
    Returns the detected MIME type or None.
    """
    # Try python-magic first
    try:
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(str(file_path))
        if mime_type and mime_type != 'application/octet-stream':
            return mime_type
    except Exception:
        pass
    
    # Try file command
    mime_type = identify_with_file_command(file_path)
    if mime_type and mime_type != 'application/octet-stream':
        return mime_type
    
    # Try content analysis
    mime_type = identify_by_content_analysis(file_path)
    if mime_type:
        return mime_type
    
    return None


def is_mp3_file(file_path):
    """
    Check if a file is an MP3 based on MIME type.
    Returns True if the file is an MP3, False otherwise.
    """
    mime_type = get_mime_type(file_path)
    return mime_type == 'audio/mpeg'


def collect_mp3_files(source_dir, verbose=False):
    """
    Recursively scan directory and collect all MP3 files.
    Returns a list of Path objects for MP3 files.
    """
    source_path = Path(source_dir).resolve()
    mp3_files = []
    
    if not source_path.exists():
        print(f"Error: Source directory '{source_dir}' does not exist.")
        return mp3_files
    
    if not source_path.is_dir():
        print(f"Error: '{source_dir}' is not a directory.")
        return mp3_files
    
    print(f"Scanning for MP3 files in: {source_path}")
    
    # Collect all files
    all_files = []
    for root, dirs, files in os.walk(source_path):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for filename in files:
            # Skip hidden files
            if filename.startswith('.'):
                continue
            file_path = Path(root) / filename
            if file_path.is_file():
                all_files.append(file_path)
    
    print(f"Found {len(all_files)} files. Checking MIME types...")
    
    # Check each file for MP3 MIME type
    for file_path in tqdm(all_files, desc="Checking files", unit="file"):
        try:
            if is_mp3_file(file_path):
                mp3_files.append(file_path)
                if verbose:
                    print(f"Found MP3: {file_path}")
        except Exception as e:
            if verbose:
                print(f"Error checking {file_path}: {e}")
    
    return mp3_files


def move_files(mp3_files, destination_dir, source_dir, dry_run=False, preserve_structure=False):
    """
    Move MP3 files to the destination directory.
    
    Args:
        mp3_files: List of Path objects for MP3 files
        destination_dir: Destination directory path
        source_dir: Original source directory (for calculating relative paths)
        dry_run: If True, only show what would be moved without moving
        preserve_structure: If True, preserve directory structure in destination
    """
    dest_path = Path(destination_dir).resolve()
    source_path = Path(source_dir).resolve()
    
    if not dry_run:
        dest_path.mkdir(parents=True, exist_ok=True)
    
    moved_count = 0
    failed_count = 0
    stats = defaultdict(int)
    
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Moving {len(mp3_files)} MP3 files to: {dest_path}")
    
    for file_path in tqdm(mp3_files, desc="Moving files", unit="file"):
        try:
            if preserve_structure:
                # Calculate relative path from source
                try:
                    rel_path = file_path.relative_to(source_path)
                    target_path = dest_path / rel_path
                except ValueError:
                    # If file is not relative to source, use filename only
                    target_path = dest_path / file_path.name
            else:
                # Just use filename
                target_path = dest_path / file_path.name
            
            # Handle filename conflicts
            if target_path.exists() and target_path != file_path:
                base_name = target_path.stem
                extension = target_path.suffix
                counter = 1
                while target_path.exists():
                    target_path = target_path.parent / f"{base_name}_{counter}{extension}"
                    counter += 1
            
            if not dry_run:
                # Create parent directory if needed
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Move the file
                shutil.move(str(file_path), str(target_path))
            
            stats['moved'] += 1
            moved_count += 1
            
        except Exception as e:
            print(f"Error moving {file_path}: {e}")
            stats['failed'] += 1
            failed_count += 1
    
    # Print summary
    print("\n" + "="*60)
    print(f"{'DRY RUN ' if dry_run else ''}Summary:")
    print(f"  Total MP3 files found: {len(mp3_files)}")
    print(f"  Successfully {'would be ' if dry_run else ''}moved: {moved_count}")
    if failed_count > 0:
        print(f"  Failed: {failed_count}")
    print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description='Recursively scan and move MP3 files (based on MIME type) to a specified folder.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Move all MP3 files to a destination folder
  %(prog)s /path/to/source /path/to/destination

  # Dry run to see what would be moved
  %(prog)s /path/to/source /path/to/destination --dry-run

  # Preserve directory structure
  %(prog)s /path/to/source /path/to/destination --preserve-structure

  # Verbose output showing each file found
  %(prog)s /path/to/source /path/to/destination --verbose
        """
    )
    
    parser.add_argument(
        'source',
        help='Source directory to scan for MP3 files'
    )
    
    parser.add_argument(
        'destination',
        help='Destination directory to move MP3 files to'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be moved without actually moving files'
    )
    
    parser.add_argument(
        '--preserve-structure',
        action='store_true',
        help='Preserve directory structure in destination folder'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show verbose output'
    )
    
    args = parser.parse_args()
    
    # Collect MP3 files
    mp3_files = collect_mp3_files(args.source, verbose=args.verbose)
    
    if not mp3_files:
        print("\nNo MP3 files found.")
        return 0
    
    print(f"\nFound {len(mp3_files)} MP3 file(s)")
    
    # Move files
    move_files(
        mp3_files,
        args.destination,
        args.source,
        dry_run=args.dry_run,
        preserve_structure=args.preserve_structure
    )
    
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
