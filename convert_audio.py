#!/usr/bin/env python3
"""
Script to convert all audio files to a uniform format (MP3).
Uses ffmpeg to convert while preserving metadata.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from collections import defaultdict
import magic
from tqdm import tqdm
import shutil


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


def check_ffmpeg():
    """Check if ffmpeg is installed."""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def convert_audio(input_path, output_path, quality='192k', verbose=False):
    """
    Convert audio file to MP3 using ffmpeg.
    Preserves all metadata tags.
    
    Returns: (success, error_message)
    """
    try:
        # ffmpeg command with metadata preservation
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-vn',  # No video
            '-acodec', 'libmp3lame',  # MP3 codec
            '-b:a', quality,  # Audio bitrate
            '-map_metadata', '0',  # Copy all metadata
            '-id3v2_version', '3',  # ID3v2.3 for compatibility
            '-y',  # Overwrite output
            str(output_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per file
        )
        
        if result.returncode == 0:
            return True, None
        else:
            error = result.stderr.split('\n')[-3] if result.stderr else "Unknown error"
            return False, error
            
    except subprocess.TimeoutExpired:
        return False, "Conversion timeout (5 minutes)"
    except Exception as e:
        return False, str(e)


def scan_and_convert_audio(directory_path, quality='192k', delete_original=False, dry_run=True, verbose=False):
    """
    Scan directory and convert all audio files to MP3.
    """
    if not check_ffmpeg():
        print("ERROR: ffmpeg is not installed or not in PATH", file=sys.stderr)
        print("Install with: sudo apt-get install ffmpeg", file=sys.stderr)
        sys.exit(1)
    
    mime_detector = magic.Magic(mime=True)
    root_path = Path(directory_path).resolve()
    
    if not root_path.exists():
        print(f"Error: Directory '{directory_path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not root_path.is_dir():
        print(f"Error: '{directory_path}' is not a directory", file=sys.stderr)
        sys.exit(1)
    
    print(f"Scanning directory: {root_path}")
    print(f"Target format: MP3 @ {quality}")
    if dry_run:
        print("DRY RUN MODE - No files will be converted")
    else:
        print("⚠️  CONVERSION MODE - Files will be converted!")
    
    print("\nCounting files...")
    
    # Collect all files
    all_files = [f for f in root_path.rglob('*') if f.is_file()]
    
    # Filter audio files
    print("Identifying audio files...")
    audio_files = []
    for file_path in tqdm(all_files, desc="Checking MIME types", unit="file"):
        mime_type = get_enhanced_mime_type(file_path, mime_detector)
        if mime_type and mime_type.startswith('audio/'):
            audio_files.append((file_path, mime_type))
    
    print(f"\nFound {len(audio_files)} audio files to process")
    print("-" * 80)
    
    # Separate files
    already_mp3 = []
    to_convert = []
    
    for file_path, mime_type in audio_files:
        if mime_type == 'audio/mpeg' and file_path.suffix.lower() == '.mp3':
            already_mp3.append((file_path, mime_type))
        else:
            to_convert.append((file_path, mime_type))
    
    print(f"\nAlready MP3: {len(already_mp3)} files (will skip)")
    print(f"To convert: {len(to_convert)} files")
    
    if not to_convert:
        print("\nℹ️  All audio files are already in MP3 format!")
        return
    
    # Show breakdown by format
    format_counts = defaultdict(int)
    for file_path, mime_type in to_convert:
        format_counts[mime_type] += 1
    
    print("\nFormats to convert:")
    for mime_type, count in sorted(format_counts.items(), key=lambda x: -x[1]):
        print(f"  {mime_type:<30} {count:>6} files")
    
    print("-" * 80)
    
    if dry_run:
        print("\nℹ️  This was a dry run. No files were converted.")
        print("   Run with --convert flag to actually convert files.")
        return
    
    # Convert files
    print("\n⚠️  Converting audio files...")
    converted = []
    skipped = []
    errors = []
    
    progress_bar = tqdm(to_convert, desc="Converting", unit="file")
    for file_path, mime_type in progress_bar:
        # Generate output path (same location, .mp3 extension)
        output_path = file_path.with_suffix('.mp3')
        
        # If output already exists and is different from input, skip
        if output_path.exists() and output_path != file_path:
            skipped.append((file_path, "output already exists"))
            if verbose:
                tqdm.write(f"  [SKIP] {file_path.name} - output exists")
            continue
        
        # If input and output are same (shouldn't happen but check anyway)
        if output_path == file_path:
            skipped.append((file_path, "already .mp3"))
            continue
        
        # Convert
        success, error = convert_audio(file_path, output_path, quality, verbose)
        
        if success:
            converted.append((file_path, output_path))
            if verbose:
                tqdm.write(f"  ✓ Converted: {file_path.name} → {output_path.name}")
            
            # Delete original if requested
            if delete_original:
                try:
                    file_path.unlink()
                    if verbose:
                        tqdm.write(f"    Deleted original: {file_path.name}")
                except Exception as e:
                    if verbose:
                        tqdm.write(f"    Warning: Could not delete original: {e}")
        else:
            errors.append((file_path, error))
            if verbose:
                tqdm.write(f"  ✗ Error: {file_path.name} - {error}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\n✓ Successfully converted: {len(converted)} files")
    print(f"⊘ Skipped: {len(skipped)} files")
    print(f"✗ Errors: {len(errors)} files")
    
    if errors and verbose:
        print("\nErrors:")
        for file_path, error in errors[:10]:
            print(f"  {file_path.name}: {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
    
    print("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Convert all audio files to MP3 format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
This script converts all audio files to MP3 format using ffmpeg.

Target format: MP3 (MPEG-1 Audio Layer III)
Default quality: 192 kbps (good balance of quality and size)
Metadata: All tags are preserved (artist, album, title, etc.)

Supported input formats:
  - FLAC, WAV, OGG, M4A, AAC, WMA, OPUS, AMR
  - And any other format ffmpeg supports

Examples:
  # Dry run (default) - see what would be converted
  python convert_audio.py /path/to/directory
  
  # Actually convert files
  python convert_audio.py /path/to/directory --convert
  
  # Convert and delete originals
  python convert_audio.py /path/to/directory --convert --delete-original
  
  # Higher quality (320 kbps)
  python convert_audio.py /path/to/directory --convert --quality 320k
  
  # Show detailed output
  python convert_audio.py /path/to/directory --convert --verbose
        '''
    )
    
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument('--convert', action='store_true',
                       help='Actually convert files (default is dry-run)')
    parser.add_argument('--quality', default='192k',
                       help='MP3 bitrate quality (default: 192k, good: 256k, best: 320k)')
    parser.add_argument('--delete-original', action='store_true',
                       help='Delete original files after successful conversion')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed output for each file')
    
    args = parser.parse_args()
    
    # Confirm if not dry run
    if args.convert:
        print(f"\n⚠️  WARNING: This will convert all audio files to MP3 @ {args.quality}!")
        print(f"   Directory: {args.directory}")
        if args.delete_original:
            print("   ⚠️  ORIGINALS WILL BE DELETED after conversion!")
        else:
            print("   Originals will be kept (you'll have both files)")
        response = input("\nAre you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            sys.exit(0)
        print()
    
    # Scan and convert
    scan_and_convert_audio(
        args.directory,
        quality=args.quality,
        delete_original=args.delete_original,
        dry_run=not args.convert,
        verbose=args.verbose
    )


if __name__ == "__main__":
    main()
