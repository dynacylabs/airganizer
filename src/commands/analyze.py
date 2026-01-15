"""Command for analyzing files and getting model recommendations."""

import sys
import json
from pathlib import Path
from typing import List

from ..core import FileScanner, MetadataCollector, FileItem
from ..ai import create_model_recommender
from ..models import get_model_registry
from ..config import get_config


def load_metadata_to_file_items(metadata_path: str) -> List[FileItem]:
    """Load FileItem objects from metadata JSON."""
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


def analyze_command(args):
    """Execute the analyze command with the new workflow."""
    print("🔬 File Analysis & Model Recommendation")
    print("=" * 60)
    
    config = get_config()
    registry = get_model_registry()
    
    # Step 1: Load or scan files
    print(f"\n📂 Step 1: Loading files...")
    if args.metadata:
        if not Path(args.metadata).exists():
            print(f"Error: Metadata file not found: {args.metadata}", file=sys.stderr)
            return 1
        files = load_metadata_to_file_items(args.metadata)
        print(f"✓ Loaded {len(files)} files from metadata: {args.metadata}")
    elif args.directory:
        # Scan and collect metadata on-the-fly
        scanner = FileScanner(args.directory)
        collector = MetadataCollector(use_binwalk=False)
        
        files = []
        file_count = scanner.count_files()
        print(f"✓ Found {file_count} files in directory")
        print(f"⏳ Collecting metadata...")
        
        processed = 0
        for file_path in scanner.scan():
            metadata = collector.collect_metadata(file_path)
            files.append(FileItem(
                file_path=str(file_path),
                file_name=file_path.name,
                mime_type=metadata.mime_type,
                file_size=metadata.file_size
            ))
            processed += 1
            if processed % 10 == 0:
                print(f"  Processed {processed}/{file_count}...", end='\r')
        
        print(f"✓ Collected metadata for {len(files)} files      ")
    else:
        print("Error: Must specify either --metadata or --directory", file=sys.stderr)
        return 1
    
    if not files:
        print("No files found to analyze.")
        return 0
    
    # Step 2: Get AI recommendations for models
    print(f"\n🤖 Step 2: Getting model recommendations...")
    
    # Check configuration
    if config.is_local_mode():
        print(f"   Using local AI: {config.get('ai.local.default_model')}")
    else:
        print(f"   Using online AI: {config.get('ai.default_provider')}")
    
    if not config.get('analyze.ask_ai_for_models', True):
        print("   (AI recommendations disabled in config)")
        return 0
    
    try:
        recommender = create_model_recommender(provider=args.provider)
    except ValueError as e:
        print(f"\nError: {e}", file=sys.stderr)
        print("\nPlease set the appropriate environment variable:")
        print(f"  export OPENAI_API_KEY='your-key-here'  (for OpenAI)")
        print(f"  export ANTHROPIC_API_KEY='your-key-here'  (for Anthropic)")
        return 1
    except Exception as e:
        print(f"\nError initializing AI client: {e}", file=sys.stderr)
        return 1
    
    # Progress callback
    def progress_callback(batch_num, total_batches, message):
        progress_pct = (batch_num / total_batches) * 100
        print(f"⏳ [{progress_pct:5.1f}%] {message}")
    
    try:
        recommendations = recommender.recommend_models(
            files,
            progress_callback=progress_callback
        )
    except Exception as e:
        print(f"\nError during recommendation: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    
    # Step 3: Save results
    print(f"\n💾 Step 3: Saving analysis results...")
    
    output_data = {
        "files": [],
        "summary": {
            "total_files": len(files),
            "files_with_recommendations": len(recommendations),
            "models_recommended": {}
        }
    }
    
    # Aggregate results
    for file_item in files:
        rec = recommendations.get(file_item.file_path, {})
        
        file_entry = {
            "file_path": file_item.file_path,
            "file_name": file_item.file_name,
            "mime_type": file_item.mime_type,
            "file_size": file_item.file_size,
            "recommendation": rec
        }
        
        output_data["files"].append(file_entry)
        
        # Track model usage
        primary_model = rec.get('primary_model', 'unknown')
        output_data["summary"]["models_recommended"][primary_model] = \
            output_data["summary"]["models_recommended"].get(primary_model, 0) + 1
    
    # Save to file
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Analysis saved to: {args.output}")
    
    # Display summary
    print(f"\n📊 Analysis Summary:")
    print("=" * 60)
    print(f"Total files analyzed:         {output_data['summary']['total_files']}")
    print(f"Files with recommendations:   {output_data['summary']['files_with_recommendations']}")
    
    print(f"\nRecommended models:")
    for model, count in sorted(
        output_data['summary']['models_recommended'].items(),
        key=lambda x: x[1],
        reverse=True
    ):
        print(f"  {model:<40} {count:>5} files")
    
    # Show recommendation sources
    sources = {}
    for file_entry in output_data["files"]:
        source = file_entry.get("recommendation", {}).get("source", "unknown")
        sources[source] = sources.get(source, 0) + 1
    
    print(f"\nRecommendation sources:")
    for source, count in sources.items():
        print(f"  {source:<25} {count:>5} files")
    
    print(f"\n✨ Analysis complete!")
    print(f"\nNext steps:")
    print(f"  1. Review recommendations: {args.output}")
    print(f"  2. Configure explicit model mappings if needed")
    print(f"  3. Download required local models (if using local mode)")
    print(f"  4. Run actual file analysis (coming in Phase 4)")
    
    return 0
