#!/usr/bin/env python3
"""
Script to delete text/plain, text/html, text/xml, and application/json files.
Uses the same mime-type detection as scan_mime_types.py.
"""

import os
import sys
import argparse
import magic
from pathlib import Path
from datetime import datetime

# MIME types to delete
TARGET_MIME_TYPES = [
    'text/plain',
    'text/html',
    'text/xml',
    'application/json'
]


def get_mime_type(file_path, mime_detector):
    """
    Get MIME type using python-magic.
    For text files, libmagic should detect them correctly without enhancement.
    """
    # Use python-magic (libmagic) - it handles text files well
    try:
        mime_type = mime_detector.from_file(str(file_path))
        return mime_type
    except Exception as e:
        print(f"Error detecting mime type for {file_path}: {e}")
        return 'error/unknown'


def delete_files_by_mime(directory, dry_run=False):
    """
    Scan directory recursively and delete files matching target MIME types.
    
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
        'errors': 0
    }
    
    deleted_files = []
    error_files = []
    
    print(f"{'[DRY RUN] ' if dry_run else ''}Scanning directory: {directory}")
    print(f"Target MIME types: {', '.join(TARGET_MIME_TYPES)}")
    print("-" * 80)
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            stats['total_scanned'] += 1
            
            try:
                # Get MIME type using python-magic
                mime_type = get_mime_type(file_path, mime_detector)
                
                # Check if this MIME type should be deleted
                if mime_type in TARGET_MIME_TYPES:
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
        f.write(f"# Text Files Deletion Log\n")
        f.write(f"# Generated: {datetime.now().isoformat()}\n")
        f.write(f"# Mode: {'DRY RUN' if dry_run else 'ACTUAL DELETION'}\n")
        f.write(f"#\n")
        f.write(f"# Statistics:\n")
        f.write(f"#   Total files scanned: {stats['total_scanned']}\n")
        f.write(f"#   Files matched: {stats['matched']}\n")
        f.write(f"#   Files deleted: {stats['deleted']}\n")
        f.write(f"#   Errors: {stats['errors']}\n")
        f.write(f"#\n")
        f.write(f"# Target MIME types: {', '.join(TARGET_MIME_TYPES)}\n")
        f.write(f"#" + "="*78 + "\n\n")
        
        if deleted_files:
            f.write(f"## {'Files that would be deleted' if dry_run else 'Deleted files'}\n\n")
            for file_path, mime_type in deleted_files:
                f.write(f"{file_path} | {mime_type}\n")
            f.write("\n")
        
        if error_files:
            f.write(f"## Errors\n\n")
            for file_path, error in error_files:
                f.write(f"{file_path} | {error}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Delete text/plain, text/html, text/xml, and application/json files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to see what would be deleted
  python delete_text_files.py /path/to/directory --dry-run

  # Actually delete the files
  python delete_text_files.py /path/to/directory

  # Delete with custom log file
  python delete_text_files.py /path/to/directory --log deletion.log
        """
    )
    
    parser.add_argument(
        "directory",
        type=str,
        help="Directory to scan for text files to delete"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be deleted without actually deleting"
    )
    parser.add_argument(
        "--log",
        type=str,
        default=f"text_deletion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        help="Log file for deletion records (default: text_deletion_<timestamp>.log)"
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
    stats, deleted_files, error_files = delete_files_by_mime(directory, args.dry_run)
    
    # Write log
    write_log(args.log, deleted_files, error_files, stats, args.dry_run)
    
    # Print summary
    print("-" * 80)
    print("Summary:")
    print(f"  Total files scanned: {stats['total_scanned']}")
    print(f"  Files matched: {stats['matched']}")
    print(f"  Files {'that would be ' if args.dry_run else ''}deleted: {stats['deleted'] if not args.dry_run else stats['matched']}")
    print(f"  Errors: {stats['errors']}")
    print(f"\nLog written to: {args.log}")
    
    if args.dry_run:
        print("\nThis was a dry run. Run without --dry-run to actually delete files.")
    
    return 0


if __name__ == "__main__":
    exit(main())
