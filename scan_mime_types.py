#!/usr/bin/env python3
"""
Script to recursively scan a directory and count files by MIME type.
Uses multiple detection methods to accurately identify files, especially octet-stream.
"""

import os
import sys
import subprocess
from pathlib import Path
from collections import defaultdict
import magic
from tqdm import tqdm


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
        '.zip': 'application/zip',
        '.gz': 'application/gzip',
        '.tar': 'application/x-tar',
        '.7z': 'application/x-7z-compressed',
        '.rar': 'application/x-rar',
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.mp4': 'video/mp4',
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/x-wav',
        '.db': 'application/vnd.sqlite3',
        '.sqlite': 'application/vnd.sqlite3',
        '.sqlite3': 'application/vnd.sqlite3',
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
    }
    
    suffix = file_path.suffix.lower()
    return extension_map.get(suffix)


def identify_by_content_analysis(file_path):
    """
    Analyze file content for magic bytes and patterns.
    """
    try:
        with open(file_path, 'rb') as f:
            header = f.read(512)  # Read first 512 bytes
            
            # Check for common magic bytes
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
            elif header.startswith(b'MZ') or header.startswith(b'PE\x00\x00'):
                return 'application/vnd.microsoft.portable-executable'
            elif header.startswith(b'\xca\xfe\xba\xbe'):
                return 'application/x-mach-binary'
            elif header.startswith(b'Rar!'):
                return 'application/x-rar'
            elif header.startswith(b'7z\xbc\xaf\x27\x1c'):
                return 'application/x-7z-compressed'
            elif b'<html' in header.lower() or b'<!doctype html' in header.lower():
                return 'text/html'
            elif header.startswith(b'<?xml'):
                return 'text/xml'
            elif header.startswith(b'{') and b'"' in header:
                # Likely JSON
                return 'application/json'
                
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
        # Try content analysis first (fastest)
        specific_type = identify_by_content_analysis(file_path)
        if specific_type:
            return specific_type
        
        # Try file command
        specific_type = identify_with_file_command(file_path)
        if specific_type:
            return specific_type
        
        # Try binwalk if available
        specific_type = identify_with_binwalk(file_path)
        if specific_type:
            return specific_type
        
        # Last resort: check file extension
        specific_type = identify_by_extension(file_path)
        if specific_type:
            return specific_type
    
    return mime_type


def scan_directory(directory_path):
    """
    Recursively scan a directory and count files by MIME type.
    
    Args:
        directory_path: Path to the directory to scan
        
    Returns:
        Dictionary mapping MIME types to file counts
    """
    mime_counts = defaultdict(int)
    mime_detector = magic.Magic(mime=True)
    
    # Convert to Path object
    root_path = Path(directory_path).resolve()
    
    if not root_path.exists():
        print(f"Error: Directory '{directory_path}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not root_path.is_dir():
        print(f"Error: '{directory_path}' is not a directory", file=sys.stderr)
        sys.exit(1)
    
    print(f"Scanning directory: {root_path}")
    print("Counting files...")
    
    # First, collect all file paths to get total count
    file_paths = [f for f in root_path.rglob('*') if f.is_file()]
    total_files = len(file_paths)
    
    print(f"Found {total_files} files to process")
    print("-" * 60)
    
    # Process files with progress bar
    for file_path in tqdm(file_paths, desc="Processing files", unit="file"):
        try:
            # Get enhanced MIME type using multiple detection methods
            mime_type = get_enhanced_mime_type(file_path, mime_detector)
            mime_counts[mime_type] += 1
        except Exception as e:
            # Handle files that can't be read
            tqdm.write(f"Warning: Could not determine MIME type for {file_path}: {e}")
            mime_counts['error/unknown'] += 1
    
    return mime_counts


def print_results(mime_counts):
    """
    Print the MIME type counts in a formatted table.
    
    Args:
        mime_counts: Dictionary mapping MIME types to counts
    """
    if not mime_counts:
        print("No files found.")
        return
    
    # Sort by count (descending), then by MIME type (ascending)
    sorted_counts = sorted(mime_counts.items(), key=lambda x: (-x[1], x[0]))
    
    # Calculate total
    total_files = sum(mime_counts.values())
    
    # Print results
    print("\nMIME Type Distribution:")
    print("=" * 60)
    print(f"{'MIME Type':<40} {'Count':>10}")
    print("-" * 60)
    
    for mime_type, count in sorted_counts:
        percentage = (count / total_files) * 100
        print(f"{mime_type:<40} {count:>10} ({percentage:>5.1f}%)")
    
    print("-" * 60)
    print(f"{'TOTAL':<40} {total_files:>10}")
    print("=" * 60)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python mime_counter.py <directory_path>")
        print("\nExample:")
        print("  python mime_counter.py /path/to/directory")
        sys.exit(1)
    
    directory_path = sys.argv[1]
    
    # Scan directory and count MIME types
    mime_counts = scan_directory(directory_path)
    
    # Print results
    print_results(mime_counts)


if __name__ == "__main__":
    main()