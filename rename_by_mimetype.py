#!/usr/bin/env python3
"""
Script to rename files based on their actual MIME type.
Analyzes file content and adds/fixes file extensions accordingly.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from collections import defaultdict
import magic
from tqdm import tqdm


# Comprehensive MIME type to extension mapping
MIME_TO_EXTENSION = {
    # Images
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
    'image/bmp': '.bmp',
    'image/tiff': '.tiff',
    'image/webp': '.webp',
    'image/svg+xml': '.svg',
    'image/x-icon': '.ico',
    'image/vnd.microsoft.icon': '.ico',
    'image/x-icns': '.icns',
    'image/x-tga': '.tga',
    'image/vnd.adobe.photoshop': '.psd',
    'image/x-xcf': '.xcf',
    'image/heic': '.heic',
    'image/jxl': '.jxl',
    'image/x-pict': '.pict',
    'image/wmf': '.wmf',
    'image/vnd.dwg': '.dwg',
    'image/x-win-bitmap': '.cur',
    'image/x-xpixmap': '.xpm',
    'image/x-atari-degas': '.pi1',
    'image/g3fax': '.g3',
    'image/x-award-bioslogo': '.bin',
    
    # Videos
    'video/mp4': '.mp4',
    'video/quicktime': '.mov',
    'video/x-msvideo': '.avi',
    'video/x-ms-wmv': '.wmv',
    'video/x-ms-asf': '.asf',
    'video/webm': '.webm',
    'video/ogg': '.ogv',
    'video/3gpp': '.3gp',
    'video/3gpp2': '.3g2',
    'video/x-flv': '.flv',
    'video/x-m4v': '.m4v',
    'video/mpeg': '.mpeg',
    'video/MP2T': '.ts',
    'video/mpeg4-generic': '.mp4',
    
    # Audio
    'audio/mpeg': '.mp3',
    'audio/ogg': '.ogg',
    'audio/x-wav': '.wav',
    'audio/x-m4a': '.m4a',
    'audio/x-aiff': '.aiff',
    'audio/midi': '.mid',
    'audio/AMR': '.amr',
    'audio/x-mp4a-latm': '.m4a',
    'audio/x-hx-aac-adts': '.aac',
    'audio/x-syx': '.syx',
    
    # Documents
    'application/pdf': '.pdf',
    'application/msword': '.doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'application/vnd.ms-excel': '.xls',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
    'application/vnd.ms-powerpoint': '.ppt',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
    'application/rtf': '.rtf',
    'text/rtf': '.rtf',
    'application/vnd.oasis.opendocument.text': '.odt',
    'application/vnd.oasis.opendocument.spreadsheet': '.ods',
    'application/vnd.oasis.opendocument.presentation': '.odp',
    'application/vnd.ms-office': '.doc',
    'application/onenote': '.one',
    
    # Archives
    'application/zip': '.zip',
    'application/x-rar': '.rar',
    'application/x-7z-compressed': '.7z',
    'application/gzip': '.gz',
    'application/x-tar': '.tar',
    'application/x-bzip2': '.bz2',
    'application/x-xz': '.xz',
    'application/x-lzma': '.lzma',
    'application/x-lzop': '.lzo',
    'application/x-archive': '.ar',
    'application/x-cpio': '.cpio',
    'application/x-xar': '.xar',
    'application/vnd.ms-cab-compressed': '.cab',
    'application/x-arc': '.arc',
    'application/x-lz4+json': '.lz4',
    
    # Executables & Libraries
    'application/x-executable': '.elf',
    'application/x-sharedlib': '.so',
    'application/x-mach-binary': '.bin',
    'application/vnd.microsoft.portable-executable': '.exe',
    'application/x-dosexec': '.exe',
    'application/x-ms-dos-executable': '.exe',
    'application/x-msdownload': '.exe',
    'application/java-archive': '.jar',
    'application/x-java-applet': '.class',
    'application/x-java-pack200': '.pack',
    'application/vnd.android.package-archive': '.apk',
    'application/x-ios-app': '.app',
    
    # Text & Code
    'text/plain': '.txt',
    'text/html': '.html',
    'text/xml': '.xml',
    'application/xml': '.xml',
    'application/json': '.json',
    'application/javascript': '.js',
    'text/css': '.css',
    'text/csv': '.csv',
    'text/x-java': '.java',
    'text/x-c': '.c',
    'text/x-c++': '.cpp',
    'text/x-python': '.py',
    'text/x-script.python': '.py',
    'text/x-ruby': '.rb',
    'text/x-perl': '.pl',
    'text/x-php': '.php',
    'text/x-shellscript': '.sh',
    'text/x-makefile': '.mk',
    'text/x-asm': '.asm',
    'text/x-tcl': '.tcl',
    'text/x-m4': '.m4',
    'application/x-sh': '.sh',
    'application/x-csh': '.csh',
    
    # Databases
    'application/vnd.sqlite3': '.sqlite',
    'application/x-sqlite3': '.sqlite',
    'application/x-msaccess': '.mdb',
    'application/x-dbf': '.dbf',
    
    # Fonts
    'font/ttf': '.ttf',
    'font/otf': '.otf',
    'font/woff': '.woff',
    'font/woff2': '.woff2',
    'font/sfnt': '.ttf',
    'application/vnd.ms-fontobject': '.eot',
    'application/vnd.ms-opentype': '.otf',
    
    # Other
    'application/x-shockwave-flash': '.swf',
    'application/postscript': '.ps',
    'application/dicom': '.dcm',
    'application/x-bittorrent': '.torrent',
    'application/x-apple-diskimage': '.dmg',
    'application/x-iso9660-image': '.iso',
    'application/x-msi': '.msi',
    'application/vnd.ms-msi': '.msi',
    'application/x-pem-file': '.pem',
    'text/x-ssh-private-key': '.key',
    'text/x-ssl-private-key': '.key',
    'application/pgp-keys': '.asc',
    'text/PGP': '.pgp',
    'application/vnd.iccprofile': '.icc',
    'message/rfc822': '.eml',
}


def identify_by_content_analysis(file_path):
    """Analyze file content for magic bytes and patterns."""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(512)
            
            if header.startswith(b'PK\x03\x04') or header.startswith(b'PK\x05\x06'):
                return 'application/zip'
            elif header.startswith(b'\x1f\x8b'):
                return 'application/gzip'
            elif header.startswith(b'\x7fELF'):
                return 'application/x-executable'
            elif header.startswith(b'%PDF'):
                return 'application/pdf'
            elif header.startswith(b'\xff\xd8\xff'):
                return 'image/jpeg'
            elif header.startswith(b'\x89PNG'):
                return 'image/png'
            elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
                return 'image/gif'
            elif header.startswith(b'SQLite format 3'):
                return 'application/vnd.sqlite3'
            elif header.startswith(b'MZ'):
                return 'application/vnd.microsoft.portable-executable'
            elif header.startswith(b'\xca\xfe\xba\xbe'):
                return 'application/x-mach-binary'
            elif header.startswith(b'Rar!'):
                return 'application/x-rar'
            elif header.startswith(b'7z\xbc\xaf\x27\x1c'):
                return 'application/x-7z-compressed'
                
    except Exception:
        pass
    
    return None


def get_enhanced_mime_type(file_path, mime_detector):
    """Get MIME type using multiple detection methods."""
    try:
        mime_type = mime_detector.from_file(str(file_path))
    except Exception:
        mime_type = 'application/octet-stream'
    
    if mime_type == 'application/octet-stream':
        specific_type = identify_by_content_analysis(file_path)
        if specific_type:
            return specific_type
    
    return mime_type


def get_extension_for_mime(mime_type):
    """Get the appropriate file extension for a MIME type."""
    return MIME_TO_EXTENSION.get(mime_type, None)


def should_rename(file_path, mime_type, new_extension):
    """Determine if a file should be renamed."""
    current_extension = file_path.suffix.lower()
    
    # Don't rename if already has correct extension
    if current_extension == new_extension:
        return False
    
    # Don't rename if no extension mapping exists
    if not new_extension:
        return False
    
    return True


def generate_new_filename(file_path, new_extension):
    """Generate a new filename with the correct extension."""
    # If file has no extension, just add it
    if not file_path.suffix:
        return file_path.parent / (file_path.name + new_extension)
    
    # Replace existing extension
    new_name = file_path.stem + new_extension
    new_path = file_path.parent / new_name
    
    # Handle conflicts - add number if file exists
    counter = 1
    while new_path.exists() and new_path != file_path:
        new_name = f"{file_path.stem}_{counter}{new_extension}"
        new_path = file_path.parent / new_name
        counter += 1
    
    return new_path


def scan_and_rename(directory_path, dry_run=True, verbose=False):
    """
    Scan directory and rename files based on MIME type.
    
    Args:
        directory_path: Path to the directory to scan
        dry_run: If True, only show what would be renamed without actually renaming
        verbose: If True, show each file being processed
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
        print("DRY RUN MODE - No files will be renamed")
    else:
        print("⚠️  RENAME MODE - Files will be renamed!")
    
    print("\nCounting files...")
    
    # Collect all file paths
    file_paths = [f for f in root_path.rglob('*') if f.is_file()]
    total_files = len(file_paths)
    
    print(f"Found {total_files} files to process")
    print("-" * 60)
    
    # Track statistics
    files_to_rename = []
    mime_type_stats = defaultdict(int)
    
    # Scan files with progress bar
    progress_bar = tqdm(file_paths, desc="Analyzing files", unit="file", disable=False)
    for file_path in progress_bar:
        try:
            mime_type = get_enhanced_mime_type(file_path, mime_detector)
            new_extension = get_extension_for_mime(mime_type)
            
            if should_rename(file_path, mime_type, new_extension):
                new_path = generate_new_filename(file_path, new_extension)
                files_to_rename.append((file_path, new_path, mime_type))
                mime_type_stats[mime_type] += 1
                
                if verbose:
                    tqdm.write(f"  [WILL RENAME] {file_path.name} -> {new_path.name} ({mime_type})")
            elif verbose:
                # Show files that don't need renaming in verbose mode
                tqdm.write(f"  [OK] {file_path.name} ({mime_type})")
                    
        except Exception as e:
            if verbose:
                tqdm.write(f"  [ERROR] Could not process {file_path}: {e}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if not files_to_rename:
        print("No files need to be renamed.")
        return
    
    print(f"\nFiles to rename by MIME type:")
    print("-" * 60)
    for mime_type in sorted(mime_type_stats.keys()):
        count = mime_type_stats[mime_type]
        ext = MIME_TO_EXTENSION.get(mime_type, '?')
        print(f"  {mime_type:<50} {count:>6} files -> {ext}")
    
    print("-" * 60)
    print(f"  {'TOTAL':<50} {len(files_to_rename):>6} files")
    print("=" * 60)
    
    # Perform renaming if not dry run
    if not dry_run:
        print("\n⚠️  Renaming files...")
        renamed_count = 0
        
        progress_bar = tqdm(files_to_rename, desc="Renaming files", unit="file", disable=False)
        for old_path, new_path, mime_type in progress_bar:
            try:
                old_path.rename(new_path)
                renamed_count += 1
                if verbose:
                    tqdm.write(f"  ✓ Renamed: {old_path.name} -> {new_path.name}")
            except Exception as e:
                tqdm.write(f"  ✗ Error renaming {old_path.name}: {e}")
        
        print(f"\n✓ Successfully renamed {renamed_count} of {len(files_to_rename)} files")
    else:
        print("\nℹ️  This was a dry run. No files were renamed.")
        print("   Run with --rename flag to actually rename files.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Rename files based on their actual MIME type content',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Dry run (default) - see what would be renamed
  python rename_by_mimetype.py /path/to/directory
  
  # Actually rename files
  python rename_by_mimetype.py /path/to/directory --rename
  
  # Show verbose output
  python rename_by_mimetype.py /path/to/directory --rename --verbose
        '''
    )
    
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument('--rename', action='store_true', 
                       help='Actually rename files (default is dry-run)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed output for each file being processed')
    parser.add_argument('--debug', action='store_true',
                       help='Alias for --verbose (show detailed output)')
    
    args = parser.parse_args()
    
    # Enable verbose if debug flag is set
    if args.debug:
        args.verbose = True
    
    # Confirm if not dry run
    if args.rename:
        print("\n⚠️  WARNING: This will rename files based on their content!")
        print(f"   Directory: {args.directory}")
        response = input("\nAre you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            sys.exit(0)
        print()
    
    # Scan and rename
    scan_and_rename(args.directory, dry_run=not args.rename, verbose=args.verbose)


if __name__ == "__main__":
    main()
