#!/usr/bin/env python3
"""
Demonstration of Airganizer's file metadata collection capabilities.

This script shows how to use the Airganizer library to:
1. Recursively scan a directory
2. Collect detailed file metadata (path, name, MIME type, binwalk output)
3. Store the metadata in JSON format
4. Display summary statistics
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import FileScanner, MetadataCollector, MetadataStore


def demo_basic_scan():
    """Demonstrate basic file scanning."""
    print("=" * 70)
    print("DEMO 1: Basic File Scanning")
    print("=" * 70)
    
    scanner = FileScanner('test_data')
    files = scanner.get_all_files()
    
    print(f"\nFound {len(files)} files:")
    for file in files:
        print(f"  - {file}")
    print()


def demo_metadata_collection():
    """Demonstrate metadata collection for a single file."""
    print("=" * 70)
    print("DEMO 2: Detailed Metadata Collection")
    print("=" * 70)
    
    # Get first file from test data
    scanner = FileScanner('test_data')
    first_file = next(scanner.scan())
    
    collector = MetadataCollector(use_binwalk=False)
    metadata = collector.collect_metadata(first_file)
    
    print(f"\nFile: {metadata.file_name}")
    print(f"Path: {metadata.file_path}")
    print(f"MIME Type: {metadata.mime_type}")
    print(f"Encoding: {metadata.mime_encoding}")
    print(f"Size: {metadata.file_size} bytes")
    print(f"\nFull metadata as JSON:")
    print(metadata.to_json())
    print()


def demo_full_directory_scan():
    """Demonstrate full directory scan with storage."""
    print("=" * 70)
    print("DEMO 3: Complete Directory Scan with Storage")
    print("=" * 70)
    
    # Initialize components
    scanner = FileScanner('test_data')
    collector = MetadataCollector(use_binwalk=False)
    store = MetadataStore(storage_path='data/demo_output.json')
    
    print("\nScanning directory: test_data")
    print("-" * 70)
    
    # Collect metadata for all files
    for file_path in scanner.scan():
        print(f"Processing: {file_path.name:30} ", end="")
        metadata = collector.collect_metadata(file_path)
        store.add_metadata(metadata)
        print(f"✓ [{metadata.mime_type}]")
    
    # Save to disk
    store.save()
    print(f"\n✓ Metadata saved to: data/demo_output.json")
    
    # Display summary
    summary = store.get_summary()
    print("\n" + "=" * 70)
    print("SUMMARY STATISTICS")
    print("=" * 70)
    print(f"Total files:        {summary['total_files']}")
    print(f"Total size:         {summary['total_size']} bytes")
    print(f"Total size (MB):    {summary['total_size_mb']}")
    print(f"\nFile types (MIME):")
    for mime_type, count in sorted(summary['mime_types'].items()):
        print(f"  {mime_type:40} {count:>5} file(s)")
    print()


def demo_reading_saved_data():
    """Demonstrate loading previously saved metadata."""
    print("=" * 70)
    print("DEMO 4: Loading Saved Metadata")
    print("=" * 70)
    
    store = MetadataStore(storage_path='data/demo_output.json')
    data = store.load()
    
    print(f"\nLoaded data from: data/demo_output.json")
    print(f"Scan date:    {data.get('scan_date', 'N/A')}")
    print(f"Total files:  {data.get('total_files', 0)}")
    print(f"\nFirst 3 files:")
    
    for i, file_data in enumerate(data.get('files', [])[:3], 1):
        print(f"\n  File {i}:")
        print(f"    Name:     {file_data['file_name']}")
        print(f"    Type:     {file_data['mime_type']}")
        print(f"    Size:     {file_data['file_size']} bytes")
    print()


def main():
    """Run all demonstrations."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "AIRGANIZER DEMONSTRATION" + " " * 29 + "║")
    print("║" + " " * 12 + "File Metadata Collection System" + " " * 25 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    try:
        demo_basic_scan()
        input("Press Enter to continue to next demo...")
        
        demo_metadata_collection()
        input("Press Enter to continue to next demo...")
        
        demo_full_directory_scan()
        input("Press Enter to continue to next demo...")
        
        demo_reading_saved_data()
        
        print("=" * 70)
        print("ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. Try scanning your own directories:")
        print("     python -m src /path/to/your/directory")
        print("  2. Examine the output JSON files in the data/ directory")
        print("  3. Install binwalk for deeper binary analysis")
        print()
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError during demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
