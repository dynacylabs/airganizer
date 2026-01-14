#!/usr/bin/env python3
"""
Script to delete files by MIME type.
Uses same MIME detection as scan_mime_types.py.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from collections import defaultdict
import magic
from tqdm import tqdm


def identify_with_binwalk(file_path):
    """Use binwalk to identify file signatures."""
    try:
        result = subprocess.run(
            ['binwalk', '-B', str(file_path)],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout:
            output = result.stdout.lower()
            if 'zip archive' in output or 'pk\x03\x04' in output:
                return 'application/zip'
            elif 'gzip' in output:
                return 'application/gzip'
            elif 'jpeg image' in output:
                return 'image/jpeg'
            elif 'png image' in output:
                return 'image/png'
            elif 'pdf document' in output:
                return 'application/pdf'
            
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return None


def identify_with_file_command(file_path):
    """Use the file command with MIME type detection."""
    try:
        result = subprocess.run(
            ['file', '--mime-type', '-b', str(file_path)],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            mime_type = result.stdout.strip()
            if mime_type and mime_type != 'application/octet-stream':
                return mime_type
                
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return None


def identify_by_extension(file_path):
    """Fallback: identify by file extension."""
    extension_map = {
        # Archives
        '.zip': 'application/zip',
        '.gz': 'application/gzip',
        '.tar': 'application/x-tar',
        '.7z': 'application/x-7z-compressed',
        '.rar': 'application/x-rar',
        
        # Documents
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        
        # Web/Data
        '.html': 'text/html',
        '.htm': 'text/html',
        '.xml': 'text/xml',
        '.json': 'application/json',
        '.js': 'application/javascript',
        
        # Code
        '.c': 'text/x-c',
        '.cpp': 'text/x-c++',
        '.h': 'text/x-c',
        '.java': 'text/x-java',
        '.m': 'application/x-matlab-data',
        
        # Images
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        
        # Videos
        '.mp4': 'video/mp4',
        '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime',
        
        # Audio
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/x-wav',
        '.m4a': 'audio/x-m4a',
    }
    
    suffix = file_path.suffix.lower()
    return extension_map.get(suffix)


def identify_by_content_analysis(file_path):
    """Analyze file content for magic bytes and patterns."""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(512)
            
            if len(header) < 4:
                return None
            
            # Archives
            if header.startswith(b'PK\x03\x04') or header.startswith(b'PK\x05\x06'):
                return 'application/zip'
            elif header.startswith(b'\x1f\x8b'):
                return 'application/gzip'
            
            # Documents
            elif header.startswith(b'%PDF'):
                return 'application/pdf'
            
            # Images
            elif header.startswith(b'\xff\xd8\xff'):
                return 'image/jpeg'
            elif header.startswith(b'\x89PNG\r\n\x1a\n'):
                return 'image/png'
            elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
                return 'image/gif'
            elif header.startswith(b'BM'):
                return 'image/bmp'
            
            # Videos
            elif header.startswith(b'RIFF') and b'AVI ' in header[:16]:
                return 'video/x-msvideo'
            
            # Audio
            elif header.startswith(b'ID3') or (len(header) >= 2 and header[0:2] == b'\xff\xfb'):
                return 'audio/mpeg'
            elif header.startswith(b'RIFF') and b'WAVE' in header[:16]:
                return 'audio/x-wav'
                
    except Exception:
        pass
    
    return None


def get_enhanced_mime_type(file_path, mime_detector):
    """
    Get MIME type using multiple detection methods.
    Same logic as scan_mime_types.py.
    """
    # First try: python-magic (libmagic)
    try:
        mime_type = mime_detector.from_file(str(file_path))
    except Exception:
        mime_type = 'error/unknown'
    
    # If we get generic octet-stream, try harder
    if mime_type == 'application/octet-stream':
        # Try content analysis first (fastest, most reliable)
        specific_type = identify_by_content_analysis(file_path)
        if specific_type:
            return specific_type
        
        # Try file command (very good at obscure formats)
        specific_type = identify_with_file_command(file_path)
        if specific_type:
            return specific_type
        
        # Try binwalk if available (good for embedded/firmware)
        specific_type = identify_with_binwalk(file_path)
        if specific_type:
            return specific_type
        
        # LAST RESORT ONLY: check file extension for truly unknown formats
        specific_type = identify_by_extension(file_path)
        if specific_type:
            return specific_type
    
    return mime_type


def delete_by_mimetype(directory_path, mime_types_to_delete, dry_run=True, verbose=False):
    """
    Scan directory and delete files with specified MIME types.
    """
    mime_detector = magic.Magic(mime=True)
    root_path = Path(directory_path).resolve()
    
    if not root_path.exists():
        print(f"Error: Directory '{directory_path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not root_path.is_dir():
        print(f"Error: '{directory_path}' is not a directory", file=sys.stderr)
        sys.exit(1)
    
    print(f"Scanning directory: {root_path}")
    print(f"MIME types to delete: {', '.join(mime_types_to_delete)}")
    if dry_run:
        print("DRY RUN MODE - No files will be deleted")
    else:
        print("⚠️  DELETE MODE - Files will be permanently removed!")
    
    print("\nCounting files...")
    
    # Collect all files (same as scan_mime_types.py)
    all_files = [f for f in root_path.rglob('*') if f.is_file()]
    
    print(f"Found {len(all_files)} total files")
    print("Checking MIME types...")
    
    # Check MIME type for ALL files and filter
    to_delete = []
    mime_counts = defaultdict(int)
    mime_sizes = defaultdict(int)
    skipped_missing = 0
    
    for file_path in tqdm(all_files, desc="Processing", unit="file"):
        try:
            # Check if file still exists
            if not file_path.exists():
                skipped_missing += 1
                continue
            
            mime_type = get_enhanced_mime_type(file_path, mime_detector)
            file_size = file_path.stat().st_size
            
            mime_counts[mime_type] += 1
            mime_sizes[mime_type] += file_size
            
            if mime_type in mime_types_to_delete:
                to_delete.append({
                    'path': file_path,
                    'mime_type': mime_type,
                    'size': file_size
                })
        except (FileNotFoundError, PermissionError):
            skipped_missing += 1
            continue
    
    # Print summary
    print("\n" + "=" * 80)
    print("DELETION SUMMARY")
    print("=" * 80)
    
    total_delete_size = sum(item['size'] for item in to_delete)
    
    print(f"\nTotal files scanned: {len(all_files)}")
    if skipped_missing > 0:
        print(f"Files no longer accessible: {skipped_missing}")
    print(f"Files to delete: {len(to_delete)} ({total_delete_size / (1024*1024):.1f} MB)")
    
    print("\nBreakdown by MIME type:")
    for mime_type in sorted(mime_types_to_delete):
        count = mime_counts[mime_type]
        size = mime_sizes[mime_type]
        if count > 0:
            print(f"  {mime_type:<50} {count:>6} files ({size / (1024*1024):>8.1f} MB)")
    
    print("-" * 80)
    
    if not to_delete:
        print("\nℹ️  No files to delete!")
        return
    
    if dry_run:
        print("\nℹ️  This was a dry run. No files were deleted.")
        print("   Run with --delete flag to actually delete files.")
        
        if verbose:
            print("\nExample files that would be deleted:")
            for item in to_delete[:10]:
                rel_path = item['path'].relative_to(root_path)
                print(f"  [{item['mime_type']}] {rel_path}")
        return
    
    # Actually delete files
    print(f"\n⚠️  Deleting {len(to_delete)} files...")
    deleted = []
    errors = []
    
    progress_bar = tqdm(to_delete, desc="Deleting", unit="file")
    for item in progress_bar:
        file_path = item['path']
        try:
            # Check if file still exists before trying to delete
            if not file_path.exists():
                if verbose:
                    tqdm.write(f"  - Skipped: {file_path.name} (already deleted)")
                continue
                
            file_path.unlink()
            deleted.append(file_path)
            if verbose:
                tqdm.write(f"  ✓ Deleted: {file_path.name} [{item['mime_type']}]")
        except FileNotFoundError:
            if verbose:
                tqdm.write(f"  - Skipped: {file_path.name} (already deleted)")
        except Exception as e:
            errors.append((file_path, str(e)))
            if verbose:
                tqdm.write(f"  ✗ Error: {file_path.name} - {e}")
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"\n✓ Successfully deleted: {len(deleted)} files")
    print(f"✗ Errors: {len(errors)} files")
    
    if errors:
        print("\nErrors:")
        for file_path, error in errors[:10]:
            print(f"  {file_path.name}: {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
    
    print("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Delete files by MIME type',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
This script deletes files based on their MIME type.
Uses same detection logic as scan_mime_types.py.

Examples:
  # Dry run - see what would be deleted
  python delete_by_mimetype.py /path/to/directory --mime-types text/html text/xml
  
  # Actually delete files
  python delete_by_mimetype.py /path/to/directory --mime-types text/html text/xml --delete
  
  # Delete multiple types
  python delete_by_mimetype.py /path/to/directory \\
    --mime-types text/html text/xml application/json error/unknown --delete
  
  # Verbose output
  python delete_by_mimetype.py /path/to/directory --mime-types text/html --delete --verbose
        '''
    )
    
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument('--mime-types', nargs='+', required=True,
                       help='MIME types to delete (e.g., text/html text/xml)')
    parser.add_argument('--delete', action='store_true',
                       help='Actually delete files (default is dry-run)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed output for each file')
    
    args = parser.parse_args()
    
    # Confirm if not dry run
    if args.delete:
        print(f"\n⚠️  WARNING: This will permanently delete files!")
        print(f"   Directory: {args.directory}")
        print(f"   MIME types: {', '.join(args.mime_types)}")
        response = input("\nAre you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            sys.exit(0)
        print()
    
    # Delete files
    delete_by_mimetype(
        args.directory,
        mime_types_to_delete=args.mime_types,
        dry_run=not args.delete,
        verbose=args.verbose
    )


if __name__ == "__main__":
    main()
