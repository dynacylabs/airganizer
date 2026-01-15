#!/usr/bin/env python3
"""
Diagnostic script to test conversion of non-standard files.
Tests each convertible mime type to see what's actually working.
"""

import os
import sys
import magic
from pathlib import Path
from collections import defaultdict


def scan_convertible_files(directory):
    """Scan for files that need conversion and group by mime type."""
    mime = magic.Magic(mime=True)
    
    convertible_types = {
        'image/x-tga': 'jpeg',
        'text/csv': 'pdf',
        'image/svg+xml': 'jpeg',
        'audio/x-mp4a-latm': 'mp3',
        'image/wmf': 'jpeg',
        'video/x-m4v': 'mp4',
        'application/msword': 'pdf',
        'image/x-pict': 'jpeg',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'pdf',
        'audio/x-m4a': 'mp3',
        'image/g3fax': 'jpeg',
        'video/x-ms-asf': 'mp4',
        'audio/x-hx-aac-adts': 'mp3',
        'image/jxl': 'jpeg',
        'image/png': 'jpeg',
        'video/mpeg': 'mp4',
        'video/mpeg4-generic': 'mp4',
        'video/x-flv': 'mp4',
        'text/plain': 'pdf',
    }
    
    skip_dirs = {'.fseventsd', '.Spotlight-V100', '.Trashes', 'AppData', '__pycache__',
                 '.AndroidStudio', '.AndroidStudio1.5', '.android'}
    
    files_by_type = defaultdict(list)
    
    print("Scanning for convertible files...")
    print("-" * 80)
    
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            file_path = os.path.join(root, file)
            
            try:
                mime_type = mime.from_file(file_path)
                
                if mime_type in convertible_types:
                    files_by_type[mime_type].append(file_path)
                    
            except Exception as e:
                pass
    
    return files_by_type, convertible_types


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_conversions.py /path/to/directory")
        sys.exit(1)
    
    directory = sys.argv[1]
    
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory")
        sys.exit(1)
    
    files_by_type, convertible_types = scan_convertible_files(directory)
    
    print("\n" + "=" * 80)
    print("Convertible files found:")
    print("=" * 80)
    
    total_files = 0
    
    for mime_type in sorted(files_by_type.keys()):
        count = len(files_by_type[mime_type])
        target = convertible_types[mime_type].upper()
        total_files += count
        
        print(f"\n{mime_type} → {target}")
        print(f"  Count: {count} files")
        print(f"  Examples:")
        
        for file_path in files_by_type[mime_type][:3]:
            print(f"    - {file_path}")
        
        if count > 3:
            print(f"    ... and {count - 3} more")
    
    print("\n" + "=" * 80)
    print(f"Total convertible files: {total_files}")
    print("=" * 80)
    
    # Now test if conversion tools are available
    print("\nChecking conversion tools:")
    print("-" * 80)
    
    import shutil
    
    tools = {
        'ImageMagick (images)': ['magick', 'convert', '/opt/homebrew/bin/magick', '/usr/local/bin/magick'],
        'ffmpeg (audio/video)': ['ffmpeg'],
        'LibreOffice (documents)': ['libreoffice', 'soffice', '/Applications/LibreOffice.app/Contents/MacOS/soffice']
    }
    
    for tool_name, commands in tools.items():
        found = False
        for cmd in commands:
            if os.path.exists(cmd) or shutil.which(cmd):
                print(f"✓ {tool_name}: {cmd}")
                found = True
                break
        if not found:
            print(f"✗ {tool_name}: NOT FOUND")


if __name__ == '__main__':
    main()
