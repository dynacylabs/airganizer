#!/usr/bin/env python3
"""Test script for the analyze command."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core import FileScanner, MetadataCollector
from src.ai import create_model_recommender
from src.models import get_model_registry
from src.config import get_config

def test_analyze():
    """Test the analyze functionality."""
    print("🧪 Testing Airganizer Analyze Feature")
    print("=" * 60)
    print()
    
    # Check configuration
    config = get_config()
    print(f"📋 Configuration:")
    print(f"  AI Mode: {'Local' if config.is_local_mode() else 'Online'}")
    print(f"  Auto-download: {config.should_auto_download()}")
    print()
    
    # Scan test directory
    test_dir = "test_data"
    if not Path(test_dir).exists():
        print(f"❌ Test directory not found: {test_dir}")
        return 1
    
    print(f"📁 Scanning: {test_dir}")
    scanner = FileScanner(test_dir)
    files = scanner.get_all_files()
    print(f"  Found {len(files)} files")
    print()
    
    # Collect metadata
    print("📊 Collecting metadata...")
    collector = MetadataCollector(use_binwalk=False)
    for file in files:
        metadata = collector.collect_metadata(file.file_path)
        file.mime_type = metadata.mime_type
        file.file_size = metadata.file_size
        print(f"  {file.file_name}: {file.mime_type}")
    print()
    
    # Get model recommendations
    print("🤖 Getting AI model recommendations...")
    
    # Check for API keys
    provider = None
    if os.getenv('OPENAI_API_KEY'):
        provider = 'openai'
        print("  Using OpenAI")
    elif os.getenv('ANTHROPIC_API_KEY'):
        provider = 'anthropic'
        print("  Using Anthropic")
    else:
        print("  ⚠️  No API keys found. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY")
        print("     Example: export OPENAI_API_KEY='your-key-here'")
        print()
        print("  Skipping AI recommendation test.")
        return 0
    
    try:
        recommender = create_model_recommender(provider=provider)
        
        def progress_cb(batch_num, total_batches, message):
            print(f"  [{batch_num}/{total_batches}] {message}")
        
        recommendations = recommender.recommend_models(
            files,
            progress_callback=progress_cb
        )
        
        print()
        print("✅ Recommendations generated!")
        print()
        print("📊 Results:")
        print("-" * 60)
        
        for file in files:
            rec = recommendations.get(file.file_path, {})
            print(f"\n{file.file_name}:")
            print(f"  MIME Type: {file.mime_type}")
            print(f"  Primary Model: {rec.get('primary_model', 'none')}")
            print(f"  Analysis Types: {', '.join(rec.get('analysis_types', []))}")
            print(f"  Source: {rec.get('source', 'unknown')}")
        
        print()
        print("✨ Test complete!")
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(test_analyze())
