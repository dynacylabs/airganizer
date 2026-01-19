#!/usr/bin/env python3
"""AI File Organizer - Main entry point."""

import argparse
import logging
import sys
import json
from pathlib import Path

from src.config import Config
from src.stage1 import Stage1Scanner
from src.stage2 import Stage2Processor
from src.cache import CacheManager


def setup_logging(log_level: str) -> None:
    """
    Setup logging configuration.
    
    Args:
        log_level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description='AI File Organizer - Automatically organize files using AI',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--config',
        required=True,
        help='Path to the configuration file (YAML format)'
    )
    
    parser.add_argument(
        '--src',
        required=True,
        help='Source directory to scan for files'
    )
    
    parser.add_argument(
        '--dst',
        required=True,
        help='Destination directory for organized files'
    )
    
    parser.add_argument(
        '--output',
        help='Path to save final results as JSON (optional)',
        default=None
    )
    
    parser.add_argument(
        '--stage1-output',
        help='Path to save Stage 1 results as JSON (optional)',
        default=None
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output (DEBUG level logging)'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable cache (process all files from scratch)'
    )
    
    parser.add_argument(
        '--clear-cache',
        choices=['all', 'stage1', 'stage2'],
        help='Clear cache before running (all/stage1/stage2)'
    )
    
    parser.add_argument(
        '--cache-dir',
        help='Override cache directory location',
        default=None
    )
    
    parser.add_argument(
        '--cache-stats',
        action='store_true',
        help='Display cache statistics and exit'
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main entry point for the AI File Organizer.
    
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    # Parse command line arguments
    args = parse_arguments()
    
    try:
        # Load configuration
        config = Config(args.config)
        
        # Setup logging
        log_level = 'DEBUG' if args.verbose else config.log_level
        setup_logging(log_level)
        
        logger = logging.getLogger(__name__)
        logger.info("AI File Organizer starting...")
        logger.info(f"Config file: {args.config}")
        logger.info(f"Source directory: {args.src}")
        logger.info(f"Destination directory: {args.dst}")
        
        # Initialize cache manager
        cache_dir = args.cache_dir or config.cache_directory
        cache_enabled = config.cache_enabled and not args.no_cache
        
        cache_manager = CacheManager(
            cache_dir=cache_dir,
            enabled=cache_enabled,
            ttl_hours=config.cache_ttl_hours
        )
        
        # Handle --cache-stats
        if args.cache_stats:
            stats = cache_manager.get_cache_stats()
            logger.info("=" * 60)
            logger.info("CACHE STATISTICS")
            logger.info("=" * 60)
            logger.info(f"Enabled: {stats['enabled']}")
            if stats['enabled']:
                logger.info(f"Cache directory: {stats['cache_dir']}")
                logger.info(f"TTL: {stats['ttl_hours']} hours")
                logger.info(f"Stage 1 results: {stats['stage1_results']}")
                logger.info(f"Stage 2 results: {stats['stage2_results']}")
                logger.info(f"File caches: {stats['file_caches']}")
                logger.info(f"Total files: {stats['total_files']}")
                logger.info(f"Total size: {stats['total_size_mb']} MB")
            logger.info("=" * 60)
            return 0
        
        # Handle --clear-cache
        if args.clear_cache:
            logger.info(f"Clearing {args.clear_cache} cache...")
            stage = None if args.clear_cache == 'all' else args.clear_cache
            count = cache_manager.clear_cache(stage)
            logger.info(f"Cleared {count} cache file(s)")
        
        # Validate source directory
        source_path = Path(args.src)
        if not source_path.exists():
            logger.error(f"Source directory does not exist: {args.src}")
            return 1
        
        if not source_path.is_dir():
            logger.error(f"Source path is not a directory: {args.src}")
            return 1
        
        # Validate destination directory (will be used in later stages)
        dest_path = Path(args.dst)
        if not dest_path.exists():
            logger.warning(f"Destination directory does not exist: {args.dst}")
            logger.info("Destination directory will be created when needed in later stages")
        
        # Execute Stage 1: File enumeration and metadata collection
        logger.info("=" * 60)
        logger.info("STAGE 1: File Enumeration and Metadata Collection")
        logger.info("=" * 60)
        
        scanner = Stage1Scanner(config, cache_manager)
        use_cache = cache_enabled
        stage1_result = scanner.scan(args.src, use_cache=use_cache)
        
        # Display Stage 1 summary
        logger.info("")
        logger.info("STAGE 1 SUMMARY:")
        logger.info(f"  Total files: {stage1_result.total_files}")
        logger.info(f"  Unique MIME types: {len(stage1_result.unique_mime_types)}")
        logger.info(f"  Errors: {len(stage1_result.errors)}")
        
        if stage1_result.total_files > 0:
            logger.info(f"\n  Sample files:")
            for file_info in stage1_result.files[:3]:
                logger.info(f"    - {file_info.file_name} ({file_info.mime_type}, {file_info.file_size} bytes)")
                if file_info.exif_data:
                    logger.info(f"      EXIF fields: {len(file_info.exif_data)}")
                if file_info.metadata:
                    logger.info(f"      Metadata: {file_info.metadata}")
        
        # Save Stage 1 results if requested
        if args.stage1_output:
            output_path = Path(args.stage1_output)
            logger.info(f"\nSaving Stage 1 results to: {output_path}")
            with open(output_path, 'w') as f:
                json.dump(stage1_result.to_dict(), f, indent=2)
            logger.info("Stage 1 results saved")
        
        # Execute Stage 2: AI model discovery and mapping
        logger.info("")
        logger.info("=" * 60)
        logger.info("STAGE 2: AI Model Discovery and Mapping")
        logger.info("=" * 60)
        
        processor = Stage2Processor(config, cache_manager)
        stage2_result = processor.process(stage1_result, use_cache=use_cache)
        
        # Display Stage 2 summary
        logger.info("")
        logger.info("STAGE 2 SUMMARY:")
        logger.info(f"  Models discovered: {len(stage2_result.available_models)}")
        logger.info(f"  MIME mappings: {len(stage2_result.mime_to_model_mapping)}")
        logger.info(f"  Connected models: {sum(stage2_result.model_connectivity.values())}/{len(stage2_result.model_connectivity)}")
        
        # Display available models
        if stage2_result.available_models:
            logger.info(f"\n  Available AI models:")
            for model in stage2_result.available_models:
                logger.info(f"    - {model.name} ({model.type}/{model.provider})")
        
        # Display MIME-to-model mapping
        if stage2_result.mime_to_model_mapping:
            logger.info(f"\n  MIME-to-Model Mapping:")
            for mime_type, model_name in stage2_result.mime_to_model_mapping.items():
                count = sum(1 for f in stage2_result.stage1_result.files if f.mime_type == mime_type)
                logger.info(f"    {mime_type} ({count} files) -> {model_name}")
        
        # Display model connectivity
        if stage2_result.model_connectivity:
            logger.info(f"\n  Model Connectivity:")
            for model_name, is_connected in stage2_result.model_connectivity.items():
                status = "✓ Connected" if is_connected else "✗ Failed"
                logger.info(f"    {model_name}: {status}")
            
            # Check if all required models are connected
            required_models = set(stage2_result.mime_to_model_mapping.values())
            all_connected = all(
                stage2_result.model_connectivity.get(m, False)
                for m in required_models
            )
            
            if all_connected:
                logger.info("\n  ✓ All required models are connected and ready")
            else:
                failed = [m for m in required_models if not stage2_result.model_connectivity.get(m, False)]
                logger.warning(f"\n  ✗ Some required models not accessible: {', '.join(failed)}")
        
        # Display final summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("FINAL SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Stage 1 - Files: {stage2_result.stage1_result.total_files}")
        logger.info(f"Stage 1 - MIME types: {len(stage2_result.stage1_result.unique_mime_types)}")
        logger.info(f"Stage 2 - Models: {len(stage2_result.available_models)}")
        logger.info(f"Stage 2 - Mappings: {len(stage2_result.mime_to_model_mapping)}")
        logger.info("=" * 60)
        
        # Save final results if requested
        if args.output:
            output_path = Path(args.output)
            logger.info(f"\nSaving final results to: {output_path}")
            with open(output_path, 'w') as f:
                json.dump(stage2_result.to_dict(), f, indent=2)
            logger.info("Results saved successfully")
        
        # TODO: Stage 3+ will be implemented next
        logger.info("\nStage 3 and beyond will be implemented in future updates")
        
        return 0
        
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
