#!/usr/bin/env python3
"""
Script to delete PNG files from a directory recursively.
Use this after converting PNG files to JPEG.
"""

import os
import sys
import argparse
from pathlib import Path


def find_png_files(directory):
    """Find all PNG files in directory."""
    png_files = []
    total_size = 0
    
    print(f"Scanning for PNG files in: {directory}")
    print("-" * 80)
    
    for root, dirs, files in os.walk(directory):
        # Skip system directories
        skip_dirs = {'.fseventsd', '.Spotlight-V100', '.Trashes', 'AppData', '__pycache__', '.git'}
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            if file.lower().endswith('.png'):
                file_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(file_path)
                    png_files.append((file_path, size))
                    total_size += size
                except Exception as e:
                    print(f"Error checking {file_path}: {e}")
    
    return png_files, total_size


def delete_png_files(png_files, total_size, dry_run=False):
    """Delete PNG files."""
    size_mb = total_size / (1024 * 1024)
    size_gb = size_mb / 1024
    
    print("\n" + "=" * 80)
    print(f"Summary:")
    print(f"  PNG files found: {len(png_files)}")
    print(f"  Total size: {size_mb:.2f} MB ({size_gb:.2f} GB)")
    
    if dry_run:
        print("\n[DRY RUN] Would delete the following PNG files:")
        for file_path, size in png_files[:20]:  # Show first 20
            print(f"  {file_path} ({size/1024:.1f} KB)")
        if len(png_files) > 20:
            print(f"  ... and {len(png_files) - 20} more files")
        print(f"\nRun without --dry-run to actually delete these files.")
        return
    
    print("\n" + "=" * 80)
    print("Deleting PNG files...")
    
    deleted_count = 0
    errors = []
    
    for file_path, size in png_files:
        try:
            os.remove(file_path)
            deleted_count += 1
            if deleted_count % 100 == 0:
                print(f"  Deleted {deleted_count}/{len(png_files)} files...")
        except Exception as e:
            errors.append((file_path, str(e)))
    
    print("\n" + "=" * 80)
    print(f"Results:")
    print(f"  Successfully deleted: {deleted_count} files")
    print(f"  Errors: {len(errors)}")
    print(f"  Space freed: {size_mb:.2f} MB ({size_gb:.2f} GB)")
    
    if errors:
        print("\nErrors encountered:")
        for file_path, error in errors[:10]:  # Show first 10 errors
            print(f"  {file_path}")
            print(f"    → {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")


def main():
    parser = argparse.ArgumentParser(
        description='Delete PNG files recursively from a directory',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find PNG files (dry run)
  python delete_png_files.py /path/to/scan --dry-run

  # Actually delete PNG files
  python delete_png_files.py /path/to/scan

  # Delete from backup directory
  python delete_png_files.py /Volumes/ssd/austinc
        """
    )
    
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be deleted without actually deleting')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a valid directory")
        sys.exit(1)
    
    # Find PNG files
    png_files, total_size = find_png_files(args.directory)
    
    if not png_files:
        print("\n✓ No PNG files found!")
        return
    
    # Delete (or show what would be deleted)
    delete_png_files(png_files, total_size, args.dry_run)


if __name__ == '__main__':
    main()
