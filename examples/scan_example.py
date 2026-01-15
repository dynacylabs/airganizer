"""Example usage script for Airganizer."""

from src.core import FileScanner, MetadataCollector, MetadataStore

def scan_directory(directory_path, output_path='data/metadata.json', use_binwalk=True):
    """
    Scan a directory and collect file metadata.
    
    Args:
        directory_path: Path to the directory to scan
        output_path: Path to save the metadata JSON file
        use_binwalk: Whether to run binwalk analysis
    """
    # Initialize components
    scanner = FileScanner(directory_path)
    collector = MetadataCollector(use_binwalk=use_binwalk)
    store = MetadataStore(storage_path=output_path)
    
    print(f"Scanning: {directory_path}")
    print("-" * 60)
    
    # Process each file
    file_count = 0
    for file_path in scanner.scan():
        metadata = collector.collect_metadata(file_path)
        store.add_metadata(metadata)
        file_count += 1
        print(f"Processed: {file_path.name}")
    
    # Save results
    store.save()
    
    # Display summary
    summary = store.get_summary()
    print("\n" + "=" * 60)
    print("SCAN COMPLETE")
    print("=" * 60)
    print(f"Total files:      {summary['total_files']}")
    print(f"Total size:       {summary['total_size_mb']} MB")
    print(f"Output saved to:  {output_path}")
    print("\nMIME types found:")
    for mime_type, count in summary['mime_types'].items():
        print(f"  {mime_type}: {count}")


if __name__ == '__main__':
    # Example: scan the test_data directory
    scan_directory('test_data', output_path='data/example_output.json', use_binwalk=False)
