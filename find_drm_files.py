#!/usr/bin/env python3
"""
Script to find DRM-protected media files (typically iTunes purchases/rentals).
These files cannot be converted and may need to be handled separately.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path


def check_for_drm(file_path):
    """Check if a media file has DRM protection using ffmpeg."""
    try:
        result = subprocess.run(
            ['ffmpeg', '-i', str(file_path)],
            capture_output=True,
            text=True,
            errors='replace',
            timeout=10
        )
        
        # Check for DRM markers in ffmpeg output
        output = result.stderr.lower()
        if 'drms' in output or 'drmi' in output:
            return True, "DRM-protected (drms/drmi codec)"
        
        # Additional checks for FairPlay and other DRM
        if 'fairplay' in output:
            return True, "FairPlay DRM"
        if 'encrypted' in output:
            return True, "Encrypted content"
            
        return False, None
        
    except subprocess.TimeoutExpired:
        return None, "Timeout"
    except Exception as e:
        return None, str(e)


def scan_for_drm(directory, dry_run=False):
    """Scan directory for DRM-protected media files."""
    
    # Common DRM-protected file extensions
    media_extensions = {'.m4v', '.m4a', '.m4p', '.aax', '.aa'}
    
    drm_files = []
    checked = 0
    errors = 0
    
    print(f"Scanning for DRM-protected files in: {directory}")
    print("-" * 80)
    
    for root, dirs, files in os.walk(directory):
        # Skip system directories
        skip_dirs = {'.fseventsd', '.Spotlight-V100', '.Trashes', 'AppData', '__pycache__'}
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            file_path = Path(root) / file
            
            # Check only media files
            if file_path.suffix.lower() in media_extensions:
                checked += 1
                
                has_drm, reason = check_for_drm(file_path)
                
                if has_drm:
                    print(f"✗ DRM: {file_path}")
                    print(f"  Reason: {reason}")
                    drm_files.append((str(file_path), reason))
                elif has_drm is None:
                    errors += 1
                    print(f"⚠ ERROR checking: {file_path}")
                    print(f"  Reason: {reason}")
                else:
                    print(f"✓ Clean: {file_path}")
    
    print("\n" + "=" * 80)
    print(f"Summary:")
    print(f"  Files checked: {checked}")
    print(f"  DRM-protected: {len(drm_files)}")
    print(f"  Errors: {errors}")
    print(f"  Clean files: {checked - len(drm_files) - errors}")
    
    if drm_files:
        print("\n" + "=" * 80)
        print("DRM-protected files found:")
        for file_path, reason in drm_files:
            print(f"  {file_path}")
            print(f"    → {reason}")
    
    return drm_files


def main():
    parser = argparse.ArgumentParser(
        description='Find DRM-protected media files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan directory for DRM files
  python find_drm_files.py /path/to/media

  # Scan with detailed output
  python find_drm_files.py /Volumes/ssd/austinc/Backups --verbose
        """
    )
    
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument('--dry-run', action='store_true', 
                        help='Show what would be found without taking action')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show verbose output')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a valid directory")
        sys.exit(1)
    
    drm_files = scan_for_drm(args.directory, args.dry_run)
    
    if drm_files:
        print(f"\nFound {len(drm_files)} DRM-protected files.")
        print("These files cannot be converted due to copyright protection.")
        print("\nOptions:")
        print("  1. Keep them in iTunes/Apple Music for playback")
        print("  2. Delete them if you no longer need them")
        print("  3. Use authorized devices/apps to play them")
    else:
        print("\n✓ No DRM-protected files found!")


if __name__ == '__main__':
    main()
