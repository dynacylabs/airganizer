#!/usr/bin/env python3
"""
Script to check video files for corruption or issues.
"""

import os
import sys
import argparse
import magic
import subprocess
from pathlib import Path


def check_file(file_path):
    """Check if a file exists, is readable, and is a valid video."""
    issues = []
    
    # Check if file exists
    if not os.path.exists(file_path):
        return ["File does not exist"]
    
    # Check file size
    size = os.path.getsize(file_path)
    if size == 0:
        return ["File is empty (0 bytes)"]
    
    # Check if readable
    try:
        with open(file_path, 'rb') as f:
            f.read(1)
    except Exception as e:
        return [f"File not readable: {e}"]
    
    # Check mime type
    try:
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(str(file_path))
        if not mime_type.startswith('video/'):
            issues.append(f"Not a video file (mime: {mime_type})")
    except Exception as e:
        issues.append(f"Cannot detect mime type: {e}")
    
    # Try to probe with ffprobe
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(file_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            issues.append(f"ffprobe failed: {result.stderr.strip()}")
        else:
            duration = result.stdout.strip()
            if duration and float(duration) == 0:
                issues.append("Video has 0 duration (corrupted)")
    except subprocess.TimeoutExpired:
        issues.append("ffprobe timeout (file may be corrupted)")
    except Exception as e:
        issues.append(f"ffprobe error: {e}")
    
    return issues if issues else ["OK"]


def main():
    parser = argparse.ArgumentParser(description="Check video files for issues")
    parser.add_argument("files", nargs="+", help="Video files to check")
    args = parser.parse_args()
    
    print("Checking video files...")
    print("=" * 80)
    
    for file_path in args.files:
        print(f"\n{file_path}")
        print(f"  Size: {os.path.getsize(file_path) if os.path.exists(file_path) else 'N/A'} bytes")
        
        issues = check_file(file_path)
        for issue in issues:
            status = "✓" if issue == "OK" else "✗"
            print(f"  {status} {issue}")


if __name__ == "__main__":
    main()
