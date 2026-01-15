#!/usr/bin/env python3
"""
Script to delete files with unconvertible mime types.
These are files that cannot be converted to standard formats (PDF, MP3, JPEG, MP4).
"""

import os
import sys
import argparse
import magic
from pathlib import Path
from datetime import datetime

# MIME types that cannot be converted to standard formats
UNCONVERTIBLE_MIME_TYPES = [
    'application/json',
    'application/gzip',
    'application/octet-stream',
    'application/onenote',
    'application/vnd.ms-office',
    'error/unknown',
    'message/rfc822',
    'text/x-c',
    'text/x-c++',
    'text/x-java',
    'application/javascript',
    'application/vnd.sqlite3',
    'application/x-appleworks3',
    'application/x-dbt',
    'application/vnd.hp-HPGL',
    'audio/midi',
    'audio/x-syx',
    'image/x-atari-degas',
    'image/x-award-bioslogo',
    'image/vnd.dwg',
    'application/x-matlab-data',
]

# System directories to skip
SKIP_DIRS = {
    '.fseventsd',
    '.Spotlight-V100',
    '.Trashes',
    '.TemporaryItems',
    '.DocumentRevisions-V100',
    '__pycache__',
    'node_modules',
    '.git',
    '.svn'
}


def get_mime_type(file_path, mime_detector):
    """Get MIME type using python-magic."""
    try:
        mime_type = mime_detector.from_file(str(file_path))
        return mime_type
    except Exception as e:
        return 'error/unknown'


def delete_unconvertible_files(directory, dry_run=False):
    """
    Scan directory recursively and delete files with unconvertible MIME types.
    
    Args:
        directory: Path to scan
        dry_run: If True, only show what would be deleted
        
    Returns:
        Dictionary with deletion statistics
    """
    mime_detector = magic.Magic(mime=True)
    
    stats = {
        'total_scanned': 0,
        'matched': 0,
        'deleted': 0,
        'errors': 0,
        'skipped_system': 0
    }
    
    deleted_files = []
    error_files = []
    
    print(f"{'[DRY RUN] ' if dry_run else ''}Scanning directory: {directory}")
    print(f"Target MIME types: {len(UNCONVERTIBLE_MIME_TYPES)} unconvertible types")
    print(f"Skipping system directories: {', '.join(sorted(SKIP_DIRS))}")
    print("-" * 80)
    
    for root, dirs, files in os.walk(directory):
        # Skip system directories
        original_dirs = len(dirs)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        stats['skipped_system'] += original_dirs - len(dirs)
        
        for file in files:
            file_path = os.path.join(root, file)
            stats['total_scanned'] += 1
            
            try:
                # Get MIME type
                mime_type = get_mime_type(file_path, mime_detector)
                
                # Check if this MIME type should be deleted
                if mime_type in UNCONVERTIBLE_MIME_TYPES:
                    stats['matched'] += 1
                    
                    if dry_run:
                        print(f"[DRY RUN] Would delete: {file_path} ({mime_type})")
                        deleted_files.append((file_path, mime_type))
                    else:
                        try:
                            os.remove(file_path)
                            print(f"Deleted: {file_path} ({mime_type})")
                            deleted_files.append((file_path, mime_type))
                            stats['deleted'] += 1
                        except Exception as e:
                            print(f"Error deleting {file_path}: {e}")
                            error_files.append((file_path, str(e)))
                            stats['errors'] += 1
                            
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                error_files.append((file_path, str(e)))
                stats['errors'] += 1
    
    return stats, deleted_files, error_files


def write_log(log_file, deleted_files, error_files, stats, dry_run):
    """Write deletion log file."""
    with open(log_file, 'w') as f:
        f.write(f"# Unconvertible Files Deletion Log\n")
        f.write(f"# Generated: {datetime.now().isoformat()}\n")
        f.write(f"# Mode: {'DRY RUN' if dry_run else 'ACTUAL DELETION'}\n")
        f.write(f"#\n")
        f.write(f"# Statistics:\n")
        f.write(f"#   Total files scanned: {stats['total_scanned']}\n")
        f.write(f"#   Files matched: {stats['matched']}\n")
        f.write(f"#   Files deleted: {stats['deleted']}\n")
        f.write(f"#   Errors: {stats['errors']}\n")
        f.write(f"#   System directories skipped: {stats['skipped_system']}\n")
        f.write(f"#\n")
        f.write(f"# Unconvertible MIME types ({len(UNCONVERTIBLE_MIME_TYPES)}):\n")
        for mime_type in UNCONVERTIBLE_MIME_TYPES:
            f.write(f"#   - {mime_type}\n")
        f.write(f"#" + "="*78 + "\n\n")
        
        if deleted_files:
            f.write(f"## {'Files that would be deleted' if dry_run else 'Deleted files'}\n\n")
            # Group by mime type
            by_type = {}
            for file_path, mime_type in deleted_files:
                if mime_type not in by_type:
                    by_type[mime_type] = []
                by_type[mime_type].append(file_path)
            
            for mime_type in sorted(by_type.keys()):
                f.write(f"\n### {mime_type} ({len(by_type[mime_type])} files)\n\n")
                for file_path in by_type[mime_type]:
                    f.write(f"{file_path}\n")
            f.write("\n")
        
        if error_files:
            f.write(f"## Errors\n\n")
            for file_path, error in error_files:
                f.write(f"{file_path} | {error}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Delete files with unconvertible MIME types (cannot be converted to PDF, MP3, JPEG, or MP4).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Unconvertible file types include:
  - Archives: gzip
  - Binary/Unknown: octet-stream
  - Proprietary: OneNote, MS Office legacy, AppleWorks, SQLite databases
  - Source code: C, C++, Java, JavaScript
  - CAD: DWG, HPGL
  - Specialized: MIDI, MATLAB data, etc.

Examples:
  # Dry run to see what would be deleted
  python delete_unconvertible_files.py /path/to/directory --dry-run

  # Actually delete the files
  python delete_unconvertible_files.py /path/to/directory

  # Delete with custom log file
  python delete_unconvertible_files.py /path/to/directory --log deletion.log
        """
    )
    
    parser.add_argument(
        "directory",
        type=str,
        help="Directory to scan for unconvertible files to delete"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be deleted without actually deleting"
    )
    parser.add_argument(
        "--log",
        type=str,
        default=f"unconvertible_deletion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        help="Log file for deletion records (default: unconvertible_deletion_<timestamp>.log)"
    )
    
    args = parser.parse_args()
    
    # Validate directory
    if not os.path.exists(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist.")
        return 1
    
    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a directory.")
        return 1
    
    directory = os.path.abspath(args.directory)
    
    # Scan and delete
    stats, deleted_files, error_files = delete_unconvertible_files(directory, args.dry_run)
    
    # Write log
    write_log(args.log, deleted_files, error_files, stats, args.dry_run)
    
    # Print summary
    print("-" * 80)
    print("Summary:")
    print(f"  Total files scanned: {stats['total_scanned']}")
    print(f"  System directories skipped: {stats['skipped_system']}")
    print(f"  Files matched: {stats['matched']}")
    print(f"  Files {'that would be ' if args.dry_run else ''}deleted: {stats['deleted'] if not args.dry_run else stats['matched']}")
    print(f"  Errors: {stats['errors']}")
    print(f"\nLog written to: {args.log}")
    
    if args.dry_run:
        print("\nThis was a dry run. Run without --dry-run to actually delete files.")
    
    return 0


if __name__ == "__main__":
    exit(main())
