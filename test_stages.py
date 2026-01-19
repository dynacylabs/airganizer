#!/usr/bin/env python3
"""Test script for Stage 1 and Stage 2."""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.stage1 import Stage1Scanner
from src.stage2 import Stage2Processor
from src.cache import CacheManager


def setup_logging():
    """Setup logging for the test script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    """Main test function."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Load configuration
    config_path = Path(__file__).parent / 'config.example.yaml'
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        return 1
    
    logger.info(f"Loading config from: {config_path}")
    config = Config(str(config_path))
    
    # Initialize cache manager
    cache_manager = CacheManager(
        cache_dir='.test_cache',
        enabled=True
    )
    
    # Create test directory with sample files
    test_dir = Path(__file__).parent / 'test_files'
    test_dir.mkdir(exist_ok=True)
    
    # Create some test files
    (test_dir / 'test.txt').write_text('Hello, World!')
    (test_dir / 'data.json').write_text('{"key": "value"}')
    (test_dir / 'script.py').write_text('print("Hello")')
    
    logger.info(f"Created test files in: {test_dir}")
    
    # Test Stage 1
    logger.info("=" * 60)
    logger.info("Testing Stage 1: File Enumeration and Metadata")
    logger.info("=" * 60)
    
    scanner = Stage1Scanner(config, cache_manager)
    stage1_result = scanner.scan(str(test_dir), use_cache=True)
    
    logger.info("\nStage 1 Results:")
    logger.info(f"  Total files: {stage1_result.total_files}")
    logger.info(f"  Unique MIME types: {stage1_result.unique_mime_types}")
    logger.info(f"  Errors: {len(stage1_result.errors)}")
    
    logger.info("\nFiles found:")
    for file_info in stage1_result.files:
        logger.info(f"  - {file_info.file_name}")
        logger.info(f"    Path: {file_info.file_path}")
        logger.info(f"    MIME: {file_info.mime_type}")
        logger.info(f"    Size: {file_info.file_size} bytes")
        if file_info.exif_data:
            logger.info(f"    EXIF: {len(file_info.exif_data)} fields")
        if file_info.metadata:
            logger.info(f"    Metadata: {file_info.metadata}")
        if file_info.binwalk_output and file_info.binwalk_output != "Binwalk not available":
            logger.info(f"    Binwalk: {len(file_info.binwalk_output)} chars")
    
    # Test Stage 2
    logger.info("\n" + "=" * 60)
    logger.info("Testing Stage 2: AI Model Discovery and Mapping")
    logger.info("=" * 60)
    
    processor = Stage2Processor(config, cache_manager)
    stage2_result = processor.process(stage1_result, use_cache=True)
    
    logger.info("\nStage 2 Results:")
    logger.info(f"  Models discovered: {len(stage2_result.available_models)}")
    logger.info(f"  MIME mappings: {len(stage2_result.mime_to_model_mapping)}")
    logger.info(f"  Model connectivity: {sum(stage2_result.model_connectivity.values())}/{len(stage2_result.model_connectivity)}")
    
    if stage2_result.available_models:
        logger.info("\nAvailable models:")
        for model in stage2_result.available_models:
            logger.info(f"  - {model.name} ({model.type}/{model.provider})")
    
    if stage2_result.mime_to_model_mapping:
        logger.info("\nMIME-to-Model mapping:")
        for mime_type, model_name in stage2_result.mime_to_model_mapping.items():
            logger.info(f"  {mime_type} -> {model_name}")
    
    if stage2_result.model_connectivity:
        logger.info("\nModel connectivity:")
        for model_name, is_connected in stage2_result.model_connectivity.items():
            status = "✓" if is_connected else "✗"
            logger.info(f"  {status} {model_name}")
    
    # Test get_model_for_file method
    logger.info("\nTesting file-to-model lookup:")
    for file_info in stage2_result.stage1_result.files:
        model = stage2_result.get_model_for_file(file_info)
        logger.info(f"  {file_info.file_name} -> {model if model else 'No model'}")
    
    logger.info("\n" + "=" * 60)
    logger.info("All tests completed successfully!")
    logger.info("=" * 60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
