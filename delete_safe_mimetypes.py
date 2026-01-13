#!/usr/bin/env python3
"""
Script to recursively delete files with safe-to-delete MIME types.
Uses libmagic for definitive MIME type detection.
"""

import os
import sys
from pathlib import Path
from collections import defaultdict
import magic
from tqdm import tqdm
import argparse


# MIME types that are safe to delete
SAFE_TO_DELETE = {
    'inode/x-empty',                    # Empty files (13,578 files)
    'application/x-bplist',             # macOS binary property lists/cache (23,533 files)
    'application/x-ms-shortcut',        # Windows shortcuts (.lnk) (533 files)
    'application/x-mswinurl',           # Windows URL shortcuts (98 files)
    'application/x-terminfo',           # Terminal info files (92 files)
    'application/etl',                  # Windows Event Trace Logs (71 files)
    'application/mbox',                 # Mailbox files (66 files)
    'application/x-ms-pdb',             # Debug symbol files (104 files)
    'application/x-wine-extension-ini', # Wine configuration files (2,944 files)
    'application/x-ole-storage',        # Old Office file fragments (367 files)
    'application/x-dosexec',            # Old DOS executables (505 files)
    'application/x-commodore-basic',    # Commodore files (238 files)
    'inode/symlink',                    # Symbolic links (19 files)
    'application/zlib',                 # Compressed data/cache (1,951 files)
    'application/x-bytecode.python',    # Python cache files .pyc (12 files)
    'application/x-ms-ese',             # Windows Extensible Storage Engine cache (30 files)
    'application/x-compress-ttcomp',    # Compressed temporary data (40 files)
    'application/x-setupscript',        # Old setup scripts (34 files)
    'application/x-dosdriver',          # Old DOS drivers (9 files)
    'text/x-mozilla-mork',              # Mozilla cache format (85 files)
    'application/x-dmp',                # Windows dump files (12 files)
    'application/x-stargallery-thm',    # StarOffice Gallery thumbnails (17 files)
    'application/x-java-applet',        # Java class files (446,569 files)
}


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


def scan_and_delete(directory_path, dry_run=True, verbose=False):
    """
    Scan directory and delete files with safe-to-delete MIME types.
    
    Args:
        directory_path: Path to the directory to scan
        dry_run: If True, only show what would be deleted without actually deleting
        verbose: If True, show each file being processed
        
    Returns:
        Tuple of (files_deleted, space_freed, mime_type_counts)
    """
    # Create multiple magic detectors for better accuracy
    mime_detector = magic.Magic(mime=True, uncompress=True)
    mime_encoding_detector = magic.Magic(mime_encoding=True)
    description_detector = magic.Magic()
    
    root_path = Path(directory_path).resolve()
    
    if not root_path.exists():
        print(f"Error: Directory '{directory_path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not root_path.is_dir():
        print(f"Error: '{directory_path}' is not a directory", file=sys.stderr)
        sys.exit(1)
    
    print(f"Scanning directory: {root_path}")
    if dry_run:
        print("DRY RUN MODE - No files will be deleted")
    else:
        print("⚠️  DELETION MODE - Files will be permanently deleted!")
    
    print("\nCounting files...")
    
    # Collect all file paths
    file_paths = [f for f in root_path.rglob('*') if f.is_file()]
    total_files = len(file_paths)
    
    print(f"Found {total_files} files to process")
    print("-" * 60)
    
    # Track statistics
    files_to_delete = []
    mime_counts = defaultdict(int)
    total_size = 0
    
    # Scan files with progress bar
    for file_path in tqdm(file_paths, desc="Scanning files", unit="file"):
        try:
            # Get detailed MIME type using multiple detection methods
            mime_type = get_detailed_mime_type(
                file_path, 
                mime_detector, 
                mime_encoding_detector, 
                description_detector
            )
            
            if mime_type in SAFE_TO_DELETE:
                file_size = file_path.stat().st_size
                files_to_delete.append((file_path, mime_type, file_size))
                mime_counts[mime_type] += 1
                total_size += file_size
                
                if verbose:
                    tqdm.write(f"  {'[DRY RUN]' if dry_run else '[DELETE]'} {file_path} ({mime_type})")
                    
        except Exception as e:
            if verbose:
                tqdm.write(f"Warning: Could not process {file_path}: {e}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if not files_to_delete:
        print("No files found matching safe-to-delete MIME types.")
        return 0, 0, mime_counts
    
    print(f"\nFiles to delete by MIME type:")
    print("-" * 60)
    for mime_type in sorted(mime_counts.keys()):
        count = mime_counts[mime_type]
        print(f"  {mime_type:<40} {count:>6} files")
    
    print("-" * 60)
    print(f"  {'TOTAL':<40} {len(files_to_delete):>6} files")
    print(f"  {'Space to be freed':<40} {format_size(total_size):>6}")
    print("=" * 60)
    
    # Perform deletion if not dry run
    if not dry_run:
        print("\n⚠️  Deleting files...")
        deleted_count = 0
        deleted_size = 0
        
        for file_path, mime_type, file_size in tqdm(files_to_delete, desc="Deleting files", unit="file"):
            try:
                file_path.unlink()
                deleted_count += 1
                deleted_size += file_size
            except Exception as e:
                tqdm.write(f"Error deleting {file_path}: {e}")
        
        print(f"\n✓ Successfully deleted {deleted_count} files")
        print(f"✓ Freed {format_size(deleted_size)} of space")
        
        return deleted_count, deleted_size, mime_counts
    else:
        print("\nℹ️  This was a dry run. No files were deleted.")
        print("   Run with --delete flag to actually delete files.")
        return 0, 0, mime_counts


def format_size(size_bytes):
    """Format bytes into human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Recursively delete files with safe-to-delete MIME types',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Safe-to-delete MIME types:
  - inode/x-empty (empty files)
  - application/x-bplist (macOS cache files)
  - application/x-ms-shortcut (Windows shortcuts)
  - application/x-mswinurl (Windows URL shortcuts)
  - application/x-terminfo (terminal info files)
  - application/etl (Windows event logs)
  - application/mbox (mailbox files)
  - application/x-ms-pdb (debug symbols)
  - application/x-wine-extension-ini (Wine config)
  - application/x-ole-storage (old Office fragments)
  - application/x-dosexec (DOS executables)
  - application/x-commodore-basic (Commodore files)
  - inode/symlink (symbolic links)
  - application/zlib (compressed cache)
  - application/x-bytecode.python (Python .pyc files)

Examples:
  # Dry run (default) - see what would be deleted
  python delete_safe_mimetypes.py /path/to/directory
  
  # Actually delete files
  python delete_safe_mimetypes.py /path/to/directory --delete
  
  # Show verbose output
  python delete_safe_mimetypes.py /path/to/directory --delete --verbose
        '''
    )
    
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument('--delete', action='store_true', 
                       help='Actually delete files (default is dry-run)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show each file being processed')
    
    args = parser.parse_args()
    
    # Confirm if not dry run
    if args.delete:
        print("\n⚠️  WARNING: This will permanently delete files!")
        print(f"   Directory: {args.directory}")
        response = input("\nAre you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            sys.exit(0)
        print()
    
    # Scan and delete
    scan_and_delete(args.directory, dry_run=not args.delete, verbose=args.verbose)


if __name__ == "__main__":
    main()
