#!/usr/bin/env python3
"""
Archive Expander - Recursively extracts all archives in a directory

This script scans a directory recursively, attempts to extract all archives
(regardless of file extension), and recursively processes nested archives.
Original archive files are deleted after successful extraction.
"""

import os
import sys
from pathlib import Path
from tqdm import tqdm
import patoolib
from collections import deque


def get_extraction_dir(file_path):
    """Get the extraction directory for a file (same name as file without extension)"""
    file_path = Path(file_path)
    dir_name = file_path.stem
    extraction_dir = file_path.parent / dir_name
    return extraction_dir


def collect_files(directory):
    """Collect all files in a directory recursively"""
    files = []
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            files.append(os.path.join(root, filename))
    return files


def try_extract_file(file_path):
    """
    Try to extract a file using patool.
    Returns list of new files created if extraction successful, empty list otherwise.
    """
    try:
        extraction_dir = get_extraction_dir(file_path)
        extraction_dir.mkdir(exist_ok=True)
        
        # Try to extract the archive
        patoolib.extract_archive(str(file_path), outdir=str(extraction_dir))
        
        # Collect all new files from extraction directory
        new_files = collect_files(extraction_dir)
        
        # Delete the original archive file after successful extraction
        os.remove(file_path)
        
        return new_files
    except Exception:
        # Not an archive or extraction failed - silently continue
        return []


def main():
    if len(sys.argv) < 2:
        print("Usage: python expand_archives.py <directory>")
        print("\nRecursively extracts all archives found in the specified directory.")
        print("Archives are extracted to folders with the same name as the archive file.")
        sys.exit(1)
    
    target_dir = sys.argv[1]
    
    if not os.path.isdir(target_dir):
        print(f"Error: {target_dir} is not a directory")
        sys.exit(1)
    
    print(f"Scanning {target_dir}...")
    
    # Initialize queue with all files in the directory
    file_queue = deque(collect_files(target_dir))
    total_files = len(file_queue)
    
    print(f"Found {total_files} files to process\n")
    
    processed = 0
    extracted = 0
    
    with tqdm(total=total_files, desc="Processing files", unit="file") as pbar:
        while file_queue:
            file_path = file_queue.popleft()
            
            # Check if file still exists (might have been deleted as part of extraction)
            if os.path.exists(file_path):
                new_files = try_extract_file(file_path)
                
                if new_files:
                    # Archive was extracted successfully
                    extracted += 1
                    # Add new files to queue and update total count
                    file_queue.extend(new_files)
                    total_files += len(new_files) - 1  # -1 because we deleted the original
                    pbar.total = total_files
                    pbar.refresh()
            
            processed += 1
            pbar.update(1)
    
    print(f"\n✓ Done! Processed {processed} files, extracted {extracted} archives.")


if __name__ == "__main__":
    main()
