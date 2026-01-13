#!/usr/bin/env python3
"""
Script to delete files that are NOT photos, videos, music, or documents.
Keeps only the essential media and document files.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from collections import defaultdict
import magic
from tqdm import tqdm


# MIME types to KEEP (everything else will be deleted)
KEEP_MIME_TYPES = {
    # Photos/Images
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/tiff',
    'image/bmp',
    'image/webp',
    'image/svg+xml',
    'image/heic',
    'image/jxl',
    'image/x-tga',
    'image/x-icns',
    'image/vnd.microsoft.icon',
    'image/g3fax',
    'image/vnd.dwg',
    'image/wmf',
    'image/x-win-bitmap',
    'image/x-atari-degas',
    'image/vnd.adobe.photoshop',
    'image/x-award-bioslogo',
    'image/x-pict',
    'image/x-xcf',
    'image/x-xpixmap',
    
    # Videos
    'video/mp4',
    'video/quicktime',
    'video/x-msvideo',
    'video/x-ms-asf',
    'video/x-ms-wmv',
    'video/webm',
    'video/ogg',
    'video/3gpp',
    'video/3gpp2',
    'video/x-flv',
    'video/x-m4v',
    'video/mpeg',
    'video/MP2T',
    'video/mpeg4-generic',
    'video/x-matroska',
    
    # Music/Audio
    'audio/mpeg',
    'audio/ogg',
    'audio/x-m4a',
    'audio/x-wav',
    'audio/x-aiff',
    'audio/midi',
    'audio/AMR',
    'audio/x-mp4a-latm',
    'audio/x-hx-aac-adts',
    'audio/x-syx',
    'audio/flac',
    'audio/aac',
    'audio/x-ms-wma',
    
    # Documents (human-readable)
    'text/plain',
    'text/html',
    'text/xml',
    'application/xml',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/vnd.ms-office',
    'application/onenote',
    'text/rtf',
    'application/rtf',
    'text/csv',
    'application/vnd.oasis.opendocument.text',
    'application/vnd.oasis.opendocument.spreadsheet',
    'application/vnd.oasis.opendocument.presentation',
    'application/json',  # Data files
}


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
        # Archives
        '.zip': 'application/zip',
        '.gz': 'application/gzip',
        '.tar': 'application/x-tar',
        '.7z': 'application/x-7z-compressed',
        '.rar': 'application/x-rar',
        '.arc': 'application/x-archive',
        
        # Documents
        '.pdf': 'application/pdf',
        
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
        
        # Videos
        '.mp4': 'video/mp4',
        '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime',
        '.wmv': 'video/x-ms-wmv',
        '.flv': 'video/x-flv',
        '.mkv': 'video/x-matroska',
        '.webm': 'video/webm',
        '.m4v': 'video/x-m4v',
        '.3gp': 'video/3gpp',
        '.3g2': 'video/3gpp2',
        '.mpg': 'video/mpeg',
        '.mpeg': 'video/mpeg',
        
        # Audio
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/x-wav',
        '.m4a': 'audio/x-m4a',
        '.ogg': 'audio/ogg',
        '.flac': 'audio/flac',
        '.aac': 'audio/aac',
        '.wma': 'audio/x-ms-wma',
        
        # Databases
        '.db': 'application/vnd.sqlite3',
        '.sqlite': 'application/vnd.sqlite3',
        '.sqlite3': 'application/vnd.sqlite3',
        
        # Executables
        '.exe': 'application/vnd.microsoft.portable-executable',
        '.dll': 'application/x-sharedlib',
        '.so': 'application/x-sharedlib',
        '.dylib': 'application/x-sharedlib',
        '.jar': 'application/java-archive',
        '.class': 'application/x-java-applet',
        '.apk': 'application/vnd.android.package-archive',
        '.deb': 'application/x-debian-package',
        '.rpm': 'application/x-rpm',
        '.dmg': 'application/x-apple-diskimage',
        '.iso': 'application/x-iso9660-image',
        
        # Apple proprietary
        '.itl': 'application/x-itunes-library',
        '.itdb': 'application/x-itunes-database',
        '.ipa': 'application/x-ios-app',
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
            
            # Archives
            if header.startswith(b'PK\x03\x04') or header.startswith(b'PK\x05\x06'):
                return 'application/zip'
            elif header.startswith(b'\x1f\x8b'):
                return 'application/gzip'
            elif header.startswith(b'Rar!'):
                return 'application/x-rar'
            elif header.startswith(b'7z\xbc\xaf\x27\x1c'):
                return 'application/x-7z-compressed'
            
            # Executables
            elif header.startswith(b'\x7fELF'):
                return 'application/x-executable'
            elif header.startswith(b'MZ'):
                return 'application/vnd.microsoft.portable-executable'
            elif header.startswith(b'\xca\xfe\xba\xbe'):
                return 'application/x-mach-binary'
            
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
            elif header.startswith(b'II\x2a\x00') or header.startswith(b'MM\x00\x2a'):
                return 'image/tiff'
            elif header.startswith(b'RIFF') and b'WEBP' in header[:16]:
                return 'image/webp'
            
            # Videos - More thorough detection
            elif header.startswith(b'RIFF') and b'AVI ' in header[:16]:
                return 'video/x-msvideo'
            
            # QuickTime/MOV - check for ftyp atom
            elif len(header) >= 12:
                # QuickTime files have atoms with 4-byte size + 4-byte type
                if header[4:8] == b'ftyp':
                    # Check for QuickTime/MOV signature
                    if b'qt  ' in header[:32] or b'isom' in header[:32] or b'mp42' in header[:32]:
                        # Could be MOV or MP4
                        if b'qt  ' in header[:32]:
                            return 'video/quicktime'
                        else:
                            return 'video/mp4'
                elif header[4:8] == b'moov' or header[4:8] == b'mdat':
                    return 'video/quicktime'
            
            # ASF/WMV/WMA files
            elif header.startswith(b'\x30\x26\xb2\x75\x8e\x66\xcf\x11\xa6\xd9\x00\xaa\x00\x62\xce\x6c'):
                # ASF format - check if it's video or audio
                # Would need deeper parsing, but generally WMV
                return 'video/x-ms-asf'
            
            # FLV (Flash Video)
            elif header.startswith(b'FLV\x01'):
                return 'video/x-flv'
            
            # Matroska/WebM (MKV)
            elif header.startswith(b'\x1a\x45\xdf\xa3'):
                return 'video/x-matroska'
            
            # MPEG video
            elif header.startswith(b'\x00\x00\x01\xba') or header.startswith(b'\x00\x00\x01\xb3'):
                return 'video/mpeg'
            
            # Audio files
            elif header.startswith(b'ID3') or (len(header) >= 2 and header[0:2] == b'\xff\xfb'):
                return 'audio/mpeg'  # MP3
            elif header.startswith(b'OggS'):
                # Could be audio or video, check for vorbis
                if b'vorbis' in header:
                    return 'audio/ogg'
                elif b'theora' in header:
                    return 'video/ogg'
                return 'audio/ogg'  # Default to audio
            elif header.startswith(b'RIFF') and b'WAVE' in header[:16]:
                return 'audio/x-wav'
            elif len(header) >= 8 and header[4:8] == b'ftyp' and b'M4A' in header[:32]:
                return 'audio/x-m4a'
            elif header.startswith(b'fLaC'):
                return 'audio/flac'
            
            # Database
            elif header.startswith(b'SQLite format 3'):
                return 'application/vnd.sqlite3'
            
            # Text-based formats
            elif b'<html' in header.lower() or b'<!doctype html' in header.lower():
                return 'text/html'
            elif header.startswith(b'<?xml'):
                return 'text/xml'
            elif header.startswith(b'{') and b'"' in header:
                # Likely JSON
                return 'application/json'
            
            # iTunes Library files - proprietary format
            # These typically don't have a standard magic number
            # Let file command handle these
                
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


def scan_and_delete(directory_path, dry_run=True, verbose=False):
    """
    Scan directory and delete files that are NOT photos, videos, music, or documents.
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
    
    print("\nKeeping ONLY: Photos, Videos, Music, and Documents")
    print("Everything else will be deleted")
    print("\nCounting files...")
    
    # Collect all file paths
    file_paths = [f for f in root_path.rglob('*') if f.is_file()]
    total_files = len(file_paths)
    
    print(f"Found {total_files} files to process")
    print("-" * 60)
    
    # Track statistics
    files_to_delete = []
    files_to_keep = []
    mime_counts_delete = defaultdict(int)
    mime_counts_keep = defaultdict(int)
    total_size = 0
    
    # Scan files with progress bar
    progress_bar = tqdm(file_paths, desc="Analyzing files", unit="file")
    for file_path in progress_bar:
        try:
            mime_type = get_enhanced_mime_type(file_path, mime_detector)
            file_size = file_path.stat().st_size
            
            if mime_type in KEEP_MIME_TYPES:
                files_to_keep.append((file_path, mime_type))
                mime_counts_keep[mime_type] += 1
                if verbose:
                    tqdm.write(f"  [KEEP] {file_path.name} ({mime_type})")
            else:
                files_to_delete.append((file_path, mime_type, file_size))
                mime_counts_delete[mime_type] += 1
                total_size += file_size
                if verbose:
                    tqdm.write(f"  [DELETE] {file_path.name} ({mime_type})")
                    
        except Exception as e:
            if verbose:
                tqdm.write(f"  [ERROR] Could not process {file_path}: {e}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    print(f"\n✓ Files to KEEP ({len(files_to_keep)} files):")
    print("-" * 80)
    for mime_type in sorted(mime_counts_keep.keys()):
        count = mime_counts_keep[mime_type]
        print(f"  {mime_type:<60} {count:>6} files")
    
    print(f"\n✗ Files to DELETE ({len(files_to_delete)} files):")
    print("-" * 80)
    for mime_type in sorted(mime_counts_delete.keys()):
        count = mime_counts_delete[mime_type]
        print(f"  {mime_type:<60} {count:>6} files")
    
    print("-" * 80)
    print(f"  {'TOTAL to KEEP':<60} {len(files_to_keep):>6} files")
    print(f"  {'TOTAL to DELETE':<60} {len(files_to_delete):>6} files")
    print(f"  {'Space to be freed':<60} {format_size(total_size):>6}")
    print("=" * 80)
    
    # Perform deletion if not dry run
    if not dry_run and files_to_delete:
        print("\n⚠️  Deleting files...")
        deleted_count = 0
        deleted_size = 0
        
        progress_bar = tqdm(files_to_delete, desc="Deleting files", unit="file")
        for file_path, mime_type, file_size in progress_bar:
            try:
                file_path.unlink()
                deleted_count += 1
                deleted_size += file_size
                if verbose:
                    tqdm.write(f"  ✓ Deleted: {file_path.name}")
            except Exception as e:
                tqdm.write(f"  ✗ Error deleting {file_path.name}: {e}")
        
        print(f"\n✓ Successfully deleted {deleted_count} of {len(files_to_delete)} files")
        print(f"✓ Freed {format_size(deleted_size)} of space")
        print(f"✓ Kept {len(files_to_keep)} media and document files")
    elif not files_to_delete:
        print("\nℹ️  No files need to be deleted.")
    else:
        print("\nℹ️  This was a dry run. No files were deleted.")
        print("   Run with --delete flag to actually delete files.")


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
        description='Delete all files except photos, videos, music, and documents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Files that will be KEPT:
  - Photos: JPEG, PNG, GIF, TIFF, BMP, WebP, SVG, HEIC, PSD, etc.
  - Videos: MP4, MOV, AVI, WMV, MKV, FLV, MPEG, WebM, etc.
  - Music: MP3, OGG, M4A, WAV, FLAC, AAC, MIDI, etc.
  - Documents: PDF, Word, Excel, PowerPoint, Text, HTML, XML, CSV, etc.

Everything else will be DELETED:
  - Source code (Java, C, C++, JavaScript, Python, etc.)
  - Archives (ZIP, GZIP, TAR, RAR, etc.)
  - Executables and applications
  - Databases
  - System files
  - And more...

Examples:
  # Dry run (default) - see what would be deleted
  python delete_unnecessary_files.py /path/to/directory
  
  # Actually delete files
  python delete_unnecessary_files.py /path/to/directory --delete
  
  # Show verbose output
  python delete_unnecessary_files.py /path/to/directory --delete --verbose
        '''
    )
    
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument('--delete', action='store_true', 
                       help='Actually delete files (default is dry-run)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed output for each file')
    parser.add_argument('--debug', action='store_true',
                       help='Alias for --verbose')
    
    args = parser.parse_args()
    
    if args.debug:
        args.verbose = True
    
    # Confirm if not dry run
    if args.delete:
        print("\n⚠️  WARNING: This will permanently delete all files except photos, videos, music, and documents!")
        print(f"   Directory: {args.directory}")
        print("\n   Files to KEEP: Photos, Videos, Music, Documents")
        print("   Files to DELETE: Everything else (source code, archives, executables, etc.)")
        response = input("\nAre you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            sys.exit(0)
        print()
    
    # Scan and delete
    scan_and_delete(args.directory, dry_run=not args.delete, verbose=args.verbose)


if __name__ == "__main__":
    main()
