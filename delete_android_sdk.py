#!/usr/bin/env python3
"""
Script to find and delete Android SDK directories (.AndroidStudio, .android)
These directories often contain fake TGA files (XML files) that interfere with conversion.
"""

import os
import sys
import argparse
import shutil
from pathlib import Path


def find_android_dirs(directory):
    """Find all Android SDK directories."""
    android_patterns = ['.AndroidStudio', '.AndroidStudio1.5', '.AndroidStudio2', '.AndroidStudio3', '.android']
    found_dirs = []
    
    print(f"Scanning for Android SDK directories in: {directory}")
    print("-" * 80)
    
    for root, dirs, files in os.walk(directory):
        for dir_name in dirs:
            if any(pattern in dir_name for pattern in android_patterns) or dir_name.startswith('.AndroidStudio'):
                full_path = os.path.join(root, dir_name)
                
                # Get directory size
                try:
                    total_size = sum(
                        os.path.getsize(os.path.join(dirpath, filename))
                        for dirpath, dirnames, filenames in os.walk(full_path)
                        for filename in filenames
                    )
                    size_mb = total_size / (1024 * 1024)
                    found_dirs.append((full_path, size_mb))
                    print(f"Found: {full_path} ({size_mb:.2f} MB)")
                except Exception as e:
                    print(f"Error checking {full_path}: {e}")
    
    return found_dirs


def delete_android_dirs(directories, dry_run=False):
    """Delete Android SDK directories."""
    total_size = sum(size for _, size in directories)
    
    print("\n" + "=" * 80)
    print(f"Summary:")
    print(f"  Directories found: {len(directories)}")
    print(f"  Total size: {total_size:.2f} MB")
    
    if dry_run:
        print("\n[DRY RUN] Would delete:")
        for dir_path, size in directories:
            print(f"  {dir_path} ({size:.2f} MB)")
        print(f"\nRun without --dry-run to actually delete these directories.")
        return
    
    print("\n" + "=" * 80)
    print("Deleting directories...")
    
    deleted_count = 0
    errors = []
    
    for dir_path, size in directories:
        try:
            print(f"Deleting: {dir_path} ({size:.2f} MB)...")
            shutil.rmtree(dir_path)
            deleted_count += 1
            print(f"  ✓ Deleted")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            errors.append((dir_path, str(e)))
    
    print("\n" + "=" * 80)
    print(f"Results:")
    print(f"  Successfully deleted: {deleted_count} directories")
    print(f"  Errors: {len(errors)}")
    print(f"  Space freed: {total_size:.2f} MB ({total_size/1024:.2f} GB)")
    
    if errors:
        print("\nErrors encountered:")
        for dir_path, error in errors:
            print(f"  {dir_path}")
            print(f"    → {error}")


def main():
    parser = argparse.ArgumentParser(
        description='Find and delete Android SDK directories',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find Android directories (dry run)
  python delete_android_sdk.py /path/to/scan --dry-run

  # Actually delete them
  python delete_android_sdk.py /path/to/scan

  # Delete from backup directory
  python delete_android_sdk.py /Volumes/ssd/austinc/Backups
        """
    )
    
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be deleted without actually deleting')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a valid directory")
        sys.exit(1)
    
    # Find Android directories
    android_dirs = find_android_dirs(args.directory)
    
    if not android_dirs:
        print("\n✓ No Android SDK directories found!")
        return
    
    # Delete (or show what would be deleted)
    delete_android_dirs(android_dirs, args.dry_run)


if __name__ == '__main__':
    main()
