#!/usr/bin/env python3
"""
Script to delete small images (icons, thumbnails, garbage).
Deletes any image smaller than 256x256 pixels.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from collections import defaultdict
import magic
from tqdm import tqdm

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("ERROR: PIL/Pillow not installed. Install with: pip install Pillow")
    sys.exit(1)


def identify_with_binwalk(file_path):
    """
    Use binwalk to identify file signatures.
    Returns a more specific type if found, None otherwise.
    """
    try:
        result = subprocess.run(
            ['binwalk', '-B', str(file_path)],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout:
            output = result.stdout.lower()
            # Parse binwalk output for common signatures
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
            elif 'elf' in output or 'executable' in output:
                return 'application/x-executable'
            elif 'sqlite' in output:
                return 'application/vnd.sqlite3'
            elif 'certificate' in output or 'private key' in output:
                return 'application/x-pem-file'
            elif 'tar archive' in output:
                return 'application/x-tar'
            elif '7-zip' in output:
                return 'application/x-7z-compressed'
            elif 'rar archive' in output:
                return 'application/x-rar'
            
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return None


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
            if mime_type and mime_type != 'application/octet-stream':
                return mime_type
                
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return None


def identify_by_extension(file_path):
    """
    Fallback: identify by file extension.
    """
    extension_map = {
        # Images
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.tiff': 'image/tiff',
        '.tif': 'image/tiff',
        '.webp': 'image/webp',
        '.ico': 'image/vnd.microsoft.icon',
        '.svg': 'image/svg+xml',
        '.tn': 'image/x-thumbnail',
        '.heic': 'image/heic',
        '.heif': 'image/heif',
    }
    
    suffix = file_path.suffix.lower()
    return extension_map.get(suffix)


def identify_by_content_analysis(file_path):
    """
    Analyze file content for magic bytes and patterns.
    More comprehensive header analysis.
    """
    try:
        with open(file_path, 'rb') as f:
            header = f.read(512)  # Read first 512 bytes
            
            if len(header) < 4:
                return None
            
            # Images
            if header.startswith(b'\xff\xd8\xff'):
                return 'image/jpeg'
            elif header.startswith(b'\x89PNG\r\n\x1a\n'):
                return 'image/png'
            elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
                return 'image/gif'
            elif header.startswith(b'BM'):
                return 'image/bmp'
            elif header.startswith(b'II\x2a\x00') or header.startswith(b'MM\x00\x2a'):
                return 'image/tiff'
            elif header.startswith(b'RIFF') and b'WEBP' in header[:16]:
                return 'image/webp'
            elif header.startswith(b'\x00\x00\x01\x00'):
                return 'image/vnd.microsoft.icon'
            elif header.startswith(b'\x00\x00\x02\x00'):
                return 'image/vnd.microsoft.icon'
                
    except Exception:
        pass
    
    return None


def get_enhanced_mime_type(file_path, mime_detector):
    """
    Get MIME type using multiple detection methods.
    Prioritizes accuracy over generic octet-stream results.
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
        # Only use this for proprietary formats that have no magic bytes
        specific_type = identify_by_extension(file_path)
        if specific_type:
            return specific_type
    
    return mime_type


def get_image_dimensions(file_path):
    """
    Get image dimensions (width, height).
    Returns None if unable to read image.
    """
    try:
        with Image.open(file_path) as img:
            return img.size  # (width, height)
    except Exception:
        return None


def scan_and_delete_small_images(directory_path, min_width=256, min_height=256, dry_run=True, verbose=False):
    """
    Scan directory and delete images smaller than specified dimensions.
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
    if dry_run:
        print("DRY RUN MODE - No files will be deleted")
    else:
        print("⚠️  DELETION MODE - Files will be permanently deleted!")
    
    print(f"\nDeleting images smaller than {min_width}x{min_height} pixels")
    print("(Icons, thumbnails, and other garbage images)")
    print("\nCounting files...")
    
    # Collect all files
    all_files = [f for f in root_path.rglob('*') if f.is_file()]
    
    # Filter image files
    print("Identifying images...")
    image_files = []
    for file_path in tqdm(all_files, desc="Checking MIME types", unit="file"):
        mime_type = get_enhanced_mime_type(file_path, mime_detector)
        # Check if it's ANY image file (starts with "image/")
        if mime_type and mime_type.startswith('image/'):
            image_files.append((file_path, mime_type))
    
    print(f"\nFound {len(image_files)} images to analyze")
    print("-" * 80)
    
    # MIME types that are always garbage (icons, thumbnails)
    ALWAYS_DELETE_TYPES = {
        'image/vnd.microsoft.icon',  # .ico files
        'image/x-icon',
        'image/x-thumbnail',  # .tn files
    }
    
    # Analyze images
    images_to_delete = []
    images_to_keep = []
    errors = []
    
    progress_bar = tqdm(image_files, desc="Analyzing images", unit="file")
    for file_path, mime_type in progress_bar:
        # Always delete icons and thumbnails regardless of size
        if mime_type in ALWAYS_DELETE_TYPES:
            file_size = file_path.stat().st_size
            images_to_delete.append((file_path, None, None, file_size, f"icon/thumbnail ({mime_type})"))
            if verbose:
                tqdm.write(f"  [DELETE] {file_path.name} - {mime_type}")
            continue
        
        # For other images, check dimensions
        dimensions = get_image_dimensions(file_path)
        # For other images, check dimensions
        dimensions = get_image_dimensions(file_path)
        
        if dimensions is None:
            errors.append((file_path, "cannot_read"))
            if verbose:
                tqdm.write(f"  [ERROR] {file_path.name}: Cannot read image")
            continue
        
        width, height = dimensions
        file_size = file_path.stat().st_size
        
        # Delete if either dimension is smaller than threshold
        if width < min_width or height < min_height:
            images_to_delete.append((file_path, width, height, file_size, f"{width}x{height}"))
            if verbose:
                tqdm.write(f"  [DELETE] {file_path.name} ({width}x{height})")
        else:
            images_to_keep.append((file_path, width, height, file_size, f"{width}x{height}"))
            if verbose:
                tqdm.write(f"  [KEEP] {file_path.name} ({width}x{height})")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    print(f"\n✗ Images to DELETE ({len(images_to_delete)} files):")
    print("-" * 80)
    if images_to_delete:
        # Separate icons/thumbnails from size-based deletions
        icons_and_thumbs = [(f, reason) for f, w, h, s, reason in images_to_delete if w is None]
        size_based = [(f, w, h, reason) for f, w, h, s, reason in images_to_delete if w is not None]
        
        if icons_and_thumbs:
            print(f"\n  Icons/Thumbnails (always deleted): {len(icons_and_thumbs)} files")
            if verbose:
                for file_path, reason in icons_and_thumbs[:10]:
                    print(f"    {file_path.name} - {reason}")
                if len(icons_and_thumbs) > 10:
                    print(f"    ... and {len(icons_and_thumbs) - 10} more")
        
        if size_based:
            print(f"\n  Small images (< {min_width}x{min_height}): {len(size_based)} files")
            # Group by size ranges
            size_groups = {
                'tiny (< 32x32)': [],
                'small (32-64)': [],
                'medium (64-128)': [],
                'large (128-256)': []
            }
            
            for file_path, width, height, reason in size_based:
                max_dim = max(width, height)
                if max_dim < 32:
                    size_groups['tiny (< 32x32)'].append((file_path, width, height))
                elif max_dim < 64:
                    size_groups['small (32-64)'].append((file_path, width, height))
                elif max_dim < 128:
                    size_groups['medium (64-128)'].append((file_path, width, height))
                else:
                    size_groups['large (128-256)'].append((file_path, width, height))
            
            for group_name, items in size_groups.items():
                if items:
                    print(f"\n    {group_name}: {len(items)} files")
                    if verbose:
                        for file_path, width, height in items[:5]:
                            print(f"      {file_path.name} ({width}x{height})")
                        if len(items) > 5:
                            print(f"      ... and {len(items) - 5} more")
    
    print(f"\n✓ Images to KEEP ({len(images_to_keep)} files):")
    print(f"  All images >= {min_width}x{min_height} pixels")
    
    if errors:
        print(f"\n⚠️  ERRORS ({len(errors)} files):")
        print("-" * 80)
        for file_path, reason in errors[:20]:
            print(f"  {file_path.name}: {reason}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more errors")
    
    print("-" * 80)
    total_delete_size = sum(f[3] for f in images_to_delete)
    total_keep_size = sum(f[3] for f in images_to_keep)
    print(f"  {'Images to DELETE':<60} {len(images_to_delete):>6} files ({format_size(total_delete_size)})")
    print(f"  {'Images to KEEP':<60} {len(images_to_keep):>6} files ({format_size(total_keep_size)})")
    print("=" * 80)
    
    # Perform deletion if not dry run
    if not dry_run and images_to_delete:
        print("\n⚠️  Deleting small images...")
        deleted_count = 0
        
        progress_bar = tqdm(images_to_delete, desc="Deleting images", unit="file")
        for file_path, width, height, file_size, reason in progress_bar:
            try:
                file_path.unlink()
                deleted_count += 1
                if verbose:
                    display_reason = reason if width is None else f"{width}x{height}"
                    tqdm.write(f"  ✓ Deleted: {file_path.name} ({display_reason})")
            except Exception as e:
                tqdm.write(f"  ✗ Error deleting {file_path.name}: {e}")
        
        print(f"\n✓ Successfully deleted {deleted_count} of {len(images_to_delete)} images")
        print(f"✓ Freed {format_size(total_delete_size)} of space")
        print(f"✓ Kept {len(images_to_keep)} images")
    elif not images_to_delete:
        print("\nℹ️  No small images found to delete.")
    else:
        print("\nℹ️  This was a dry run. No files were deleted.")
        print("   Run with --delete flag to actually delete images.")


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
        description='Delete small images (icons, thumbnails, garbage)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
This script identifies and deletes images smaller than a specified size.

Default threshold: 256x256 pixels

Images to DELETE:
  - Icons (16x16, 32x32, 48x48, etc.)
  - Thumbnails (< 256 pixels)
  - Garbage/placeholder images
  - Any image with width < 256 OR height < 256

Images to KEEP:
  - All images >= 256x256 pixels
  - Photos, screenshots, artwork, etc.

Examples:
  # Dry run (default) - see what would be deleted
  python delete_small_images.py /path/to/directory
  
  # Show detailed output
  python delete_small_images.py /path/to/directory --verbose
  
  # Actually delete images
  python delete_small_images.py /path/to/directory --delete
  
  # Custom threshold (delete images < 512x512)
  python delete_small_images.py /path/to/directory --min-size 512
        '''
    )
    
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument('--delete', action='store_true',
                       help='Actually delete images (default is dry-run)')
    parser.add_argument('--min-size', type=int, default=256,
                       help='Minimum width/height in pixels (default: 256)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed output for each file')
    
    args = parser.parse_args()
    
    # Validate min-size
    if args.min_size < 1:
        print("Error: --min-size must be at least 1", file=sys.stderr)
        sys.exit(1)
    
    # Confirm if not dry run
    if args.delete:
        print(f"\n⚠️  WARNING: This will permanently delete all images smaller than {args.min_size}x{args.min_size} pixels!")
        print(f"   Directory: {args.directory}")
        print("\n   Files to DELETE: Icons, thumbnails, small images")
        print("   Files to KEEP: All images >= threshold")
        response = input("\nAre you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            sys.exit(0)
        print()
    
    # Scan and delete
    scan_and_delete_small_images(
        args.directory, 
        min_width=args.min_size, 
        min_height=args.min_size,
        dry_run=not args.delete, 
        verbose=args.verbose
    )


if __name__ == "__main__":
    main()
