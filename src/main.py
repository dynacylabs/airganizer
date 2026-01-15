"""Main CLI entry point for Airganizer."""

import argparse
import sys
from pathlib import Path
from .core import FileScanner, MetadataCollector, MetadataStore
from .commands import propose_command, analyze_command


def scan_command(args):
    """Execute the scan command."""
    # Validate directory
    try:
        scanner = FileScanner(args.directory)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    print(f"🔍 Scanning directory: {args.directory}")
    print("-" * 60)
    
    # Count files first
    file_count = scanner.count_files()
    print(f"Found {file_count} files to analyze\n")
    
    if file_count == 0:
        print("No files found in directory.")
        return 0
    
    # Initialize metadata collector and storage
    use_binwalk = not args.no_binwalk
    collector = MetadataCollector(use_binwalk=use_binwalk)
    store = MetadataStore(storage_path=args.output)
    
    if not collector.binwalk_available and use_binwalk:
        print("⚠️  Warning: binwalk not found. Install it for deeper analysis:")
        print("   sudo apt-get install binwalk\n")
    
    # Process files
    processed = 0
    for file_path in scanner.scan():
        if args.verbose:
            print(f"Processing: {file_path.name}")
        
        metadata = collector.collect_metadata(file_path)
        store.add_metadata(metadata)
        
        processed += 1
        if not args.verbose and processed % 10 == 0:
            print(f"Processed {processed}/{file_count} files...", end='\r')
    
    print(f"\n✅ Processed {processed} files\n")
    
    # Save results
    store.save()
    print(f"💾 Metadata saved to: {args.output}\n")
    
    # Display summary
    summary = store.get_summary()
    print("📊 Summary:")
    print("-" * 60)
    print(f"Total files:     {summary['total_files']}")
    print(f"Total size:      {summary['total_size_mb']} MB")
    print(f"\nMIME types found:")
    for mime_type, count in sorted(summary['mime_types'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {mime_type:<40} {count:>5} files")
    
    return 0


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description='Airganizer - AI-powered file system organizing tool',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan directory and collect file metadata')
    scan_parser.add_argument(
        'directory',
        type=str,
        help='Directory to scan'
    )
    scan_parser.add_argument(
        '-o', '--output',
        type=str,
        default='data/metadata.json',
        help='Output file for metadata (default: data/metadata.json)'
    )
    scan_parser.add_argument(
        '--no-binwalk',
        action='store_true',
        help='Skip binwalk analysis (faster but less detailed)'
    )
    scan_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    # Propose command
    propose_parser = subparsers.add_parser(
        'propose',
        help='Use AI to propose an organizational structure'
    )
    propose_parser.add_argument(
        '-m', '--metadata',
        type=str,
        help='Path to metadata JSON file from scan command'
    )
    propose_parser.add_argument(
        '-d', '--directory',
        type=str,
        help='Directory to scan (alternative to --metadata)'
    )
    propose_parser.add_argument(
        '-o', '--output',
        type=str,
        default='data/proposed_structure.json',
        help='Output file for proposed structure (default: data/proposed_structure.json)'
    )
    propose_parser.add_argument(
        '--provider',
        type=str,
        default='openai',
        choices=['openai', 'anthropic', 'claude'],
        help='AI provider to use (default: openai)'
    )
    propose_parser.add_argument(
        '--chunk-size',
        type=int,
        default=50,
        help='Number of files to process per AI call (default: 50)'
    )
    propose_parser.add_argument(
        '--temperature',
        type=float,
        default=0.3,
        help='AI temperature for creativity (0.0-1.0, default: 0.3)'
    )
    
    # Analyze command
    analyze_parser = subparsers.add_parser(
        'analyze',
        help='Analyze files and get AI model recommendations'
    )
    analyze_parser.add_argument(
        '-m', '--metadata',
        type=str,
        help='Path to metadata JSON file from scan command'
    )
    analyze_parser.add_argument(
        '-d', '--directory',
        type=str,
        help='Directory to scan and analyze (alternative to --metadata)'
    )
    analyze_parser.add_argument(
        '-o', '--output',
        type=str,
        default='data/analysis_results.json',
        help='Output file for analysis results (default: data/analysis_results.json)'
    )
    analyze_parser.add_argument(
        '--provider',
        type=str,
        choices=['openai', 'anthropic', 'ollama'],
        help='AI provider to use (default: from config)'
    )
    
    args = parser.parse_args()
    
    # Handle no command specified (backward compatibility)
    if not args.command:
        # If only one positional arg and it looks like a directory, assume scan
        if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
            # Convert old-style direct scan to new subcommand format
            sys.argv.insert(1, 'scan')
            return main()
        else:
            parser.print_help()
            return 1
    
    # Route to appropriate command
    if args.command == 'scan':
        return scan_command(args)
    elif args.command == 'propose':
        return propose_command(args)
    elif args.command == 'analyze':
        return analyze_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
