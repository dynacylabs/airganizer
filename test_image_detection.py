#!/usr/bin/env python3
"""
Test script to verify convert_images.py finds the same images as scan_mime_types.py
"""

import sys
from pathlib import Path
import magic
from tqdm import tqdm

# Import detection functions from both scripts
sys.path.insert(0, '/workspaces/airganizer')

# We'll use the scan_mime_types version as the reference
from scan_mime_types import get_enhanced_mime_type as scan_get_mime

def test_directory(directory_path):
    """Compare image detection between scan and convert approaches."""
    
    mime_detector = magic.Magic(mime=True)
    root_path = Path(directory_path).resolve()
    
    if not root_path.exists():
        print(f"Error: Directory '{directory_path}' does not exist")
        return
    
    print(f"Testing directory: {root_path}")
    print("Collecting files...")
    
    # Collect all files
    all_files = [f for f in root_path.rglob('*') if f.is_file()]
    print(f"Found {len(all_files)} total files\n")
    
    # Scan for images
    print("Checking MIME types...")
    image_files = []
    mime_counts = {}
    
    for file_path in tqdm(all_files, desc="Processing", unit="file"):
        try:
            mime_type = scan_get_mime(file_path, mime_detector)
            
            # Count all MIME types
            mime_counts[mime_type] = mime_counts.get(mime_type, 0) + 1
            
            # Track images
            if mime_type and mime_type.startswith('image/'):
                image_files.append((file_path, mime_type))
                
        except Exception as e:
            pass
    
    # Print results
    print(f"\n{'='*80}")
    print(f"RESULTS")
    print(f"{'='*80}")
    print(f"Total files: {len(all_files)}")
    print(f"Image files: {len(image_files)}")
    print(f"\nImage MIME types found:")
    
    image_mime_counts = {}
    for _, mime_type in image_files:
        image_mime_counts[mime_type] = image_mime_counts.get(mime_type, 0) + 1
    
    for mime_type in sorted(image_mime_counts.keys()):
        count = image_mime_counts[mime_type]
        print(f"  {mime_type:<40} {count:>6} files")
    
    print(f"{'='*80}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_image_detection.py <directory>")
        sys.exit(1)
    
    test_directory(sys.argv[1])
