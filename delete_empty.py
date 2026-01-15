#!/usr/bin/env python3
"""
Script to recursively scan a directory and delete all empty files and folders.
"""

import os
import argparse
from pathlib import Path


def delete_empty_files(directory, dry_run=False):
    """Delete all empty files in the directory tree."""
    deleted_files = []
    
    for root, dirs, files in os.walk(directory, topdown=False):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                if os.path.getsize(file_path) == 0:
                    if dry_run:
                        print(f"[DRY RUN] Would delete empty file: {file_path}")
                        deleted_files.append(file_path)
                    else:
                        os.remove(file_path)
                        print(f"Deleted empty file: {file_path}")
                        deleted_files.append(file_path)
            except (OSError, FileNotFoundError) as e:
                print(f"Error processing file {file_path}: {e}")
    
    return deleted_files


def delete_empty_directories(directory, dry_run=False):
    """Delete all empty directories in the directory tree."""
    deleted_dirs = []
    
    # Walk bottom-up to handle nested empty directories
    for root, dirs, files in os.walk(directory, topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                # Check if directory is empty
                if not os.listdir(dir_path):
                    if dry_run:
                        print(f"[DRY RUN] Would delete empty directory: {dir_path}")
                        deleted_dirs.append(dir_path)
                    else:
                        os.rmdir(dir_path)
                        print(f"Deleted empty directory: {dir_path}")
                        deleted_dirs.append(dir_path)
            except (OSError, FileNotFoundError) as e:
                print(f"Error processing directory {dir_path}: {e}")
    
    return deleted_dirs


def main():
    parser = argparse.ArgumentParser(
        description="Recursively scan a directory and delete all empty files and folders.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (preview what would be deleted)
  python delete_empty.py /path/to/directory --dry-run

  # Actually delete empty files and folders
  python delete_empty.py /path/to/directory

  # Current directory
  python delete_empty.py .
        """
    )
    parser.add_argument(
        "directory",
        type=str,
        help="Directory to scan for empty files and folders"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be deleted without actually deleting anything"
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
    
    print(f"{'[DRY RUN] ' if args.dry_run else ''}Scanning directory: {directory}")
    print("-" * 80)
    
    # First delete empty files
    deleted_files = delete_empty_files(directory, args.dry_run)
    
    # Then delete empty directories (may become empty after files are deleted)
    deleted_dirs = delete_empty_directories(directory, args.dry_run)
    
    # Summary
    print("-" * 80)
    print(f"Summary:")
    print(f"  Empty files {'that would be ' if args.dry_run else ''}deleted: {len(deleted_files)}")
    print(f"  Empty directories {'that would be ' if args.dry_run else ''}deleted: {len(deleted_dirs)}")
    print(f"  Total: {len(deleted_files) + len(deleted_dirs)}")
    
    if args.dry_run:
        print("\nThis was a dry run. Run without --dry-run to actually delete files and folders.")
    
    return 0


if __name__ == "__main__":
    exit(main())
