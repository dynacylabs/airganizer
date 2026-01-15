"""Command for proposing organizational structures using AI."""

import sys
import json
from pathlib import Path
from typing import List

from ..core import FileScanner, MetadataStore, FileItem
from ..ai import create_structure_proposer


def load_files_from_metadata(metadata_path: str) -> List[FileItem]:
    """Load file information from metadata JSON."""
    with open(metadata_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    files = []
    for file_data in data.get('files', []):
        files.append(FileItem(
            file_path=file_data['file_path'],
            file_name=file_data['file_name'],
            mime_type=file_data.get('mime_type'),
            file_size=file_data.get('file_size')
        ))
    
    return files


def load_files_from_directory(directory: str) -> List[FileItem]:
    """Load file information directly from directory scan."""
    scanner = FileScanner(directory)
    files = []
    
    for file_path in scanner.scan():
        files.append(FileItem(
            file_path=str(file_path),
            file_name=file_path.name
        ))
    
    return files


def propose_command(args):
    """Execute the propose command."""
    print("🤖 AI-Powered Structure Proposal")
    print("=" * 60)
    
    # Load files
    print(f"\n📂 Loading files...")
    if args.metadata:
        if not Path(args.metadata).exists():
            print(f"Error: Metadata file not found: {args.metadata}", file=sys.stderr)
            return 1
        files = load_files_from_metadata(args.metadata)
        print(f"✓ Loaded {len(files)} files from metadata: {args.metadata}")
    elif args.directory:
        files = load_files_from_directory(args.directory)
        print(f"✓ Loaded {len(files)} files from directory: {args.directory}")
    else:
        print("Error: Must specify either --metadata or --directory", file=sys.stderr)
        return 1
    
    if not files:
        print("No files found to organize.")
        return 0
    
    # Create proposer
    print(f"\n🔧 Initializing AI ({args.provider})...")
    try:
        proposer = create_structure_proposer(
            provider=args.provider,
            chunk_size=args.chunk_size,
            temperature=args.temperature
        )
        print(f"✓ AI client initialized")
    except ValueError as e:
        print(f"\nError: {e}", file=sys.stderr)
        print("\nPlease set the appropriate environment variable:")
        print(f"  export OPENAI_API_KEY='your-key-here'  (for OpenAI)")
        print(f"  export ANTHROPIC_API_KEY='your-key-here'  (for Anthropic)")
        return 1
    except ImportError as e:
        print(f"\nError: {e}", file=sys.stderr)
        print("\nPlease install the required library:")
        if 'openai' in str(e).lower():
            print("  pip install openai")
        elif 'anthropic' in str(e).lower():
            print("  pip install anthropic")
        return 1
    
    # Generate proposal
    print(f"\n🎯 Generating organizational structure...")
    print(f"   Files to process: {len(files)}")
    print(f"   Chunk size: {args.chunk_size}")
    print(f"   Temperature: {args.temperature}")
    print()
    
    def progress_callback(chunk_num, total_chunks, message):
        if chunk_num == 0:
            print(f"⏳ {message}")
        else:
            progress_pct = (chunk_num / total_chunks) * 100
            print(f"⏳ [{progress_pct:5.1f}%] {message}")
    
    try:
        structure = proposer.propose_structure(files, progress_callback=progress_callback)
    except Exception as e:
        print(f"\nError during proposal: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    
    # Save structure
    print(f"\n💾 Saving proposed structure...")
    output_path = args.output
    proposer.save_structure(output_path)
    print(f"✓ Structure saved to: {output_path}")
    
    # Display summary
    summary = structure.get_summary()
    print("\n📊 Proposal Summary:")
    print("=" * 60)
    print(f"Total directories proposed: {summary['total_directories']}")
    print(f"Files analyzed:             {summary['processing_stats'].get('total_chunks', 0)} chunks")
    print(f"Created at:                 {summary['created_at']}")
    
    # Display structure overview
    print("\n📁 Proposed Structure Overview:")
    print("=" * 60)
    _print_structure_tree(structure.root, prefix="")
    
    print("\n✨ Proposal complete!")
    print(f"\nNext steps:")
    print(f"  1. Review the proposed structure: {output_path}")
    print(f"  2. The structure can be refined in later phases")
    print(f"  3. Files will be assigned to directories in the next phase")
    
    return 0


def _print_structure_tree(node, prefix="", is_last=True):
    """Print a tree representation of the directory structure."""
    connector = "└── " if is_last else "├── "
    print(f"{prefix}{connector}{node.name}/")
    print(f"{prefix}    ↳ {node.description}")
    
    extension = "    " if is_last else "│   "
    
    for i, subdir in enumerate(node.subdirectories):
        is_last_child = (i == len(node.subdirectories) - 1)
        _print_structure_tree(subdir, prefix + extension, is_last_child)
