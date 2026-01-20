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
from src.stage3 import Stage3Processor
from src.stage4 import Stage4Processor
from src.stage5 import Stage5Processor
from src.cache import CacheManager
from src.progress import ProgressManager


def setup_logging(log_level: str, use_rich: bool = False, progress_mode: bool = False) -> None:
    """
    Setup logging configuration.
    
    Args:
        log_level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_rich: Whether to use Rich's logging handler for better formatting with progress bars
        progress_mode: If True, don't add any handlers (will be added later for progress display)
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    if progress_mode:
        # When using progress bars with integrated logging, don't add any handlers here
        # The ProgressLoggingHandler will be added later to display logs in the progress panel
        logging.basicConfig(
            level=numeric_level,
            format='%(message)s',
            handlers=[]  # No handlers - will be added after progress manager is created
        )
    elif use_rich:
        # Use Rich's logging handler to integrate with progress bars
        from rich.logging import RichHandler
        logging.basicConfig(
            level=numeric_level,
            format='%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[RichHandler(
                rich_tracebacks=True,
                show_time=False,
                show_path=False,
                markup=True
            )]
        )
    else:
        # Standard logging
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
        help='Enable verbose output (INFO+ level logging with progress)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output (DEBUG level logging with detailed information)'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable cache (process all files from scratch)'
    )
    
    parser.add_argument(
        '--clear-cache',
        choices=['all', 'stage1', 'stage2', 'stage3', 'stage4', 'stage5'],
        help='Clear cache before running (all/stage1/stage2/stage3/stage4/stage5)'
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
    
    parser.add_argument(
        '--skip-stage3',
        action='store_true',
        help='Skip Stage 3 (AI file analysis)'
    )
    
    parser.add_argument(
        '--max-files',
        type=int,
        help='Maximum number of files to analyze in Stage 3 (for testing)',
        default=None
    )
    
    parser.add_argument(
        '--stage3-output',
        help='Path to save Stage 3 unified results as JSON (optional)',
        default=None
    )
    
    parser.add_argument(
        '--skip-stage4',
        action='store_true',
        help='Skip Stage 4 (taxonomic structure planning)'
    )
    
    parser.add_argument(
        '--stage4-output',
        help='Path to save Stage 4 results with taxonomy as JSON (optional)',
        default=None
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        help='Batch size for Stage 4 taxonomy generation (overrides config)',
        default=None
    )
    
    parser.add_argument(
        '--skip-stage5',
        action='store_true',
        help='Skip Stage 5 (physical file organization)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate file moves without actually moving files (Stage 5)'
    )
    
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing files at destination (Stage 5)'
    )
    
    parser.add_argument(
        '--stage5-output',
        help='Path to save Stage 5 move operations as JSON (optional)',
        default=None
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
        if args.debug:
            log_level = 'DEBUG'
        elif args.verbose:
            log_level = 'INFO'
        else:
            log_level = config.log_level
        
        # Determine if progress bars will be enabled (disabled in debug mode)
        progress_will_be_enabled = not args.debug
        
        # If progress bars are enabled, use progress_mode to avoid duplicate log handlers
        # The ProgressLoggingHandler will be added after ProgressManager is created
        setup_logging(log_level, use_rich=False, progress_mode=progress_will_be_enabled)
        
        logger = logging.getLogger(__name__)
        logger.info("AI File Organizer starting...")
        logger.debug(f"Debug mode enabled")
        logger.debug(f"Arguments: {vars(args)}")
        logger.info(f"Config file: {args.config}")
        logger.info(f"Source directory: {args.src}")
        logger.info(f"Destination directory: {args.dst}")
        
        # Initialize cache manager
        cache_dir = args.cache_dir or config.cache_directory
        cache_enabled = config.cache_enabled and not args.no_cache
        
        cache_manager = CacheManager(
            cache_dir=cache_dir,
            enabled=cache_enabled
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
                logger.info(f"Stage 1 results: {stats['stage1_results']}")
                logger.info(f"Stage 2 results: {stats['stage2_results']}")
                logger.info(f"Stage 3 results: {stats.get('stage3_results', 0)}")
                logger.info(f"Stage 4 results: {stats.get('stage4_results', 0)}")
                logger.info(f"Stage 5 results: {stats.get('stage5_results', 0)}")
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
        
        # Create progress manager (disabled if debug mode is on)
        # Progress bars interfere with debug logging
        progress_enabled = not args.debug
        progress_manager = ProgressManager(total_stages=5, enabled=progress_enabled)
        
        # If progress is enabled, add custom logging handler to route logs through progress display
        if progress_enabled:
            from src.progress import ProgressLoggingHandler
            progress_handler = ProgressLoggingHandler(progress_manager)
            progress_handler.setFormatter(logging.Formatter('%(message)s'))
            progress_handler.setLevel(logging.INFO)
            
            # Add handler to root logger
            root_logger = logging.getLogger()
            root_logger.addHandler(progress_handler)
        
        # Execute the pipeline with progress tracking
        with progress_manager:
            # Execute Stage 1: File enumeration and metadata collection
            logger.info("=" * 60)
            logger.info("STAGE 1: File Enumeration and Metadata Collection")
            logger.info("=" * 60)
            
            scanner = Stage1Scanner(config, cache_manager, progress_manager)
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
            
            # Mark Stage 1 complete
            progress_manager.complete_stage()
            
            # Execute Stage 2: AI model discovery and mapping
            logger.info("")
            logger.info("=" * 60)
            logger.info("STAGE 2: AI Model Discovery and Mapping")
            logger.info("=" * 60)
        
            processor = Stage2Processor(config, cache_manager, progress_manager)
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
        
            # Mark Stage 2 complete
            progress_manager.complete_stage()
        
            # Execute Stage 3: AI-powered file analysis (unless skipped)
            if not args.skip_stage3:
                logger.info("")
                logger.info("=" * 60)
                logger.info("STAGE 3: AI-Powered File Analysis")
                logger.info("=" * 60)
            
                stage3_processor = Stage3Processor(config, cache_manager, progress_manager)
                # Use CLI arg if specified, otherwise use config default
                max_files = args.max_files if args.max_files else config.stage3_max_files
                stage3_result = stage3_processor.process(
                    stage2_result,
                    use_cache=use_cache,
                    max_files=max_files
                )
            
                # Display Stage 3 summary
                logger.info("")
                logger.info("STAGE 3 SUMMARY:")
                logger.info(f"  Total files: {len(stage3_result.file_analyses)}")
                logger.info(f"  Successfully analyzed: {stage3_result.total_analyzed}")
                logger.info(f"  Errors: {stage3_result.total_errors}")
            
                # Display sample analyses
                if stage3_result.file_analyses:
                    logger.info(f"\n  Sample analyses:")
                    for analysis in stage3_result.file_analyses[:3]:
                        if not analysis.error:
                            logger.info(f"    File: {Path(analysis.file_path).name}")
                            logger.info(f"      Proposed name: {analysis.proposed_filename}")
                            logger.info(f"      Description: {analysis.description[:80]}...")
                            logger.info(f"      Tags: {', '.join(analysis.tags[:5])}")
            
                # Save Stage 3 results if requested
                if args.stage3_output:
                    output_path = Path(args.stage3_output)
                    logger.info(f"\nSaving Stage 3 unified results to: {output_path}")
                
                    # Get unified data combining all stages
                    unified_data = stage3_result.get_all_unified_data()
                
                    output_data = {
                        'summary': {
                            'source_directory': stage2_result.stage1_result.source_directory,
                            'total_files': stage2_result.stage1_result.total_files,
                            'analyzed_files': stage3_result.total_analyzed,
                            'errors': stage3_result.total_errors,
                            'unique_mime_types': stage2_result.stage1_result.unique_mime_types,
                            'available_models': [m.to_dict() for m in stage2_result.available_models],
                            'mime_to_model_mapping': stage2_result.mime_to_model_mapping
                        },
                        'files': unified_data
                    }
                
                    with open(output_path, 'w') as f:
                        json.dump(output_data, f, indent=2)
                    logger.info("Stage 3 results saved")
            
                # Update final summary
                logger.info("")
                logger.info("=" * 60)
                logger.info("FINAL SUMMARY")
                logger.info("=" * 60)
                logger.info(f"Stage 1 - Files scanned: {stage2_result.stage1_result.total_files}")
                logger.info(f"Stage 1 - MIME types: {len(stage2_result.stage1_result.unique_mime_types)}")
                logger.info(f"Stage 2 - Models discovered: {len(stage2_result.available_models)}")
                logger.info(f"Stage 2 - Model mappings: {len(stage2_result.mime_to_model_mapping)}")
                logger.info(f"Stage 3 - Files analyzed: {stage3_result.total_analyzed}")
                logger.info(f"Stage 3 - Analysis errors: {stage3_result.total_errors}")
                logger.info("=" * 60)
            
                # Mark Stage 3 complete
                progress_manager.complete_stage()
            
                # Execute Stage 4: Taxonomic structure planning (unless skipped)
                if not args.skip_stage4:
                    logger.info("")
                    logger.info("=" * 60)
                    logger.info("STAGE 4: Taxonomic Structure Planning")
                    logger.info("=" * 60)
                
                    stage3_processor = Stage3Processor(config, cache_manager, progress_manager)
                    # Use CLI arg if specified, otherwise use config default
                    batch_size = args.batch_size if args.batch_size else config.stage4_batch_size
                    stage4_result = stage4_processor.process(
                        stage3_result,
                        batch_size=batch_size
                    )
                
                    # Display Stage 4 summary
                    logger.info("")
                    logger.info("STAGE 4 SUMMARY:")
                    logger.info(f"  Total categories: {stage4_result.total_categories}")
                    logger.info(f"  Files assigned: {stage4_result.total_assigned}")
                
                    # Display taxonomy structure
                    if stage4_result.taxonomy:
                        max_depth = max(len(n.path.split('/')) for n in stage4_result.taxonomy)
                        logger.info(f"  Max depth: {max_depth} levels")
                    
                        # Show top-level categories
                        top_level = [n for n in stage4_result.taxonomy if '/' not in n.path]
                        logger.info(f"\n  Top-level categories ({len(top_level)}):")
                        for node in sorted(top_level, key=lambda n: n.file_count, reverse=True)[:10]:
                            logger.info(f"    - {node.path}: {node.file_count} files")
                            logger.info(f"      {node.description}")
                
                    # Show sample assignments
                    if stage4_result.file_assignments:
                        logger.info(f"\n  Sample file assignments:")
                        for assignment in stage4_result.file_assignments[:5]:
                            logger.info(f"    {Path(assignment.file_path).name}")
                            logger.info(f"      → {assignment.target_path}/{assignment.proposed_filename}")
                            logger.info(f"      Reason: {assignment.reasoning[:80]}...")
                
                    # Save Stage 4 results if requested
                    if args.stage4_output:
                        output_path = Path(args.stage4_output)
                        logger.info(f"\nSaving Stage 4 results to: {output_path}")
                    
                        # Get unified data with assignments
                        unified_data = stage4_result.get_all_unified_data()
                    
                        output_data = {
                            'summary': {
                                'source_directory': stage2_result.stage1_result.source_directory,
                                'total_files': stage2_result.stage1_result.total_files,
                                'analyzed_files': stage3_result.total_analyzed,
                                'assigned_files': stage4_result.total_assigned,
                                'total_categories': stage4_result.total_categories,
                                'max_depth': max(len(n.path.split('/')) for n in stage4_result.taxonomy) if stage4_result.taxonomy else 0
                            },
                            'taxonomy': [t.to_dict() for t in stage4_result.taxonomy],
                            'taxonomy_tree': stage4_result.get_taxonomy_tree(),
                            'files': unified_data
                        }
                    
                        with open(output_path, 'w') as f:
                            json.dump(output_data, f, indent=2)
                        logger.info("Stage 4 results saved")
                
                    # Mark Stage 4 complete
                    progress_manager.complete_stage()
                
                    # Execute Stage 5: Physical file organization (unless skipped)
                    if not args.skip_stage5:
                        logger.info("")
                        logger.info("=" * 60)
                        logger.info("STAGE 5: Physical File Organization")
                        logger.info("=" * 60)
                    
                        stage5_processor = Stage5Processor(config, cache_manager, progress_manager)
                        # Use CLI args if specified, otherwise use config defaults
                        dry_run = args.dry_run if args.dry_run else config.stage5_dry_run
                        overwrite = args.overwrite if args.overwrite else config.stage5_overwrite
                        stage5_result = stage5_processor.process(
                            stage4_result,
                            destination_root=args.dst,
                            dry_run=dry_run,
                            overwrite=overwrite
                        )
                    
                        # Display Stage 5 summary
                        logger.info("")
                        logger.info("STAGE 5 SUMMARY:")
                        logger.info(f"  Total files processed: {stage5_result.total_files}")
                        logger.info(f"  Organized files: {stage5_result.successful_moves}")
                        logger.info(f"  Excluded files: {stage5_result.excluded_moves}")
                        logger.info(f"  Error files: {stage5_result.error_moves}")
                        logger.info(f"  Failed moves: {stage5_result.failed_moves}")
                        logger.info(f"  Skipped moves: {stage5_result.skipped_moves}")
                    
                        if args.dry_run or dry_run:
                            logger.info(f"\n  *** DRY-RUN MODE: No files were moved ***")
                        else:
                            logger.info(f"\n  *** All files moved from source directory ***")
                    
                        # Show sample organized moves
                        organized_ops = [op for op in stage5_result.operations if op.success and op.category == "organized"]
                        if organized_ops:
                            logger.info(f"\n  Sample organized moves:")
                            for op in organized_ops[:3]:
                                logger.info(f"    {Path(op.source_path).name}")
                                logger.info(f"      → {op.target_path}/{op.target_filename}")
                    
                        # Show excluded files info
                        excluded_ops = [op for op in stage5_result.operations if op.category == "excluded"]
                        if excluded_ops:
                            logger.info(f"\n  Excluded files moved to _excluded/ ({len(excluded_ops)} files)")
                            logger.info(f"    See _excluded/exclusions_log.json for details")
                    
                        # Show error files info
                        error_ops = [op for op in stage5_result.operations if op.category == "error"]
                        if error_ops:
                            logger.info(f"\n  Error files moved to _errors/ ({len(error_ops)} files)")
                            logger.info(f"    See _errors/errors_log.json for details")
                    
                        # Show all failures
                        failed_ops = [op for op in stage5_result.operations if op.error and not op.success]
                        if failed_ops:
                            logger.warning(f"\n  Failed moves ({len(failed_ops)}):")
                            for op in failed_ops:
                                logger.warning(f"    {Path(op.source_path).name}")
                                logger.warning(f"      Error: {op.error}")
                    
                        # Save Stage 5 results if requested
                        if args.stage5_output:
                            output_path = Path(args.stage5_output)
                            logger.info(f"\nSaving Stage 5 results to: {output_path}")
                        
                            output_data = {
                                'summary': {
                                    'source_directory': stage2_result.stage1_result.source_directory,
                                    'destination_directory': args.dst,
                                    'total_files': stage5_result.total_files,
                                    'successful_moves': stage5_result.successful_moves,
                                    'failed_moves': stage5_result.failed_moves,
                                    'skipped_moves': stage5_result.skipped_moves,
                                    'dry_run': stage5_result.dry_run
                                },
                                'operations': [op.to_dict() for op in stage5_result.operations]
                            }
                        
                            with open(output_path, 'w') as f:
                                json.dump(output_data, f, indent=2)
                            logger.info("Stage 5 results saved")
                    
                        # Update final summary
                        logger.info("")
                        logger.info("=" * 60)
                        logger.info("FINAL SUMMARY")
                        logger.info("=" * 60)
                        logger.info(f"Stage 1 - Files scanned: {stage2_result.stage1_result.total_files}")
                        logger.info(f"Stage 1 - Files excluded: {len(stage2_result.stage1_result.excluded_files)}")
                        logger.info(f"Stage 1 - MIME types: {len(stage2_result.stage1_result.unique_mime_types)}")
                        logger.info(f"Stage 2 - Models discovered: {len(stage2_result.available_models)}")
                        logger.info(f"Stage 2 - Model mappings: {len(stage2_result.mime_to_model_mapping)}")
                        logger.info(f"Stage 3 - Files analyzed: {stage3_result.total_analyzed}")
                        logger.info(f"Stage 3 - Analysis errors: {stage3_result.total_errors}")
                        logger.info(f"Stage 4 - Categories created: {stage4_result.total_categories}")
                        logger.info(f"Stage 4 - Files assigned: {stage4_result.total_assigned}")
                        logger.info(f"Stage 5 - Organized files: {stage5_result.successful_moves}")
                        logger.info(f"Stage 5 - Garbage files: {stage5_result.garbage_moves}")
                        logger.info(f"Stage 5 - Excluded files: {stage5_result.excluded_moves}")
                        logger.info(f"Stage 5 - Error files: {stage5_result.error_moves}")
                        logger.info(f"Stage 5 - Move failures: {stage5_result.failed_moves}")
                        logger.info("=" * 60)
                    
                        # Mark Stage 5 complete
                        progress_manager.complete_stage()
                    
                        # Save complete results if requested (backward compatible)
                        if args.output and not args.stage5_output:
                            output_path = Path(args.output)
                            logger.info(f"\nSaving complete results to: {output_path}")
                            with open(output_path, 'w') as f:
                                json.dump(stage5_result.to_dict(), f, indent=2)
                            logger.info("Complete results saved")
                
                    else:
                        # Stage 5 skipped
                        logger.info("")
                        logger.info("=" * 60)
                        logger.info("FINAL SUMMARY (Stage 5 skipped)")
                        logger.info("=" * 60)
                        logger.info(f"Stage 1 - Files scanned: {stage2_result.stage1_result.total_files}")
                        logger.info(f"Stage 1 - MIME types: {len(stage2_result.stage1_result.unique_mime_types)}")
                        logger.info(f"Stage 2 - Models discovered: {len(stage2_result.available_models)}")
                        logger.info(f"Stage 2 - Model mappings: {len(stage2_result.mime_to_model_mapping)}")
                        logger.info(f"Stage 3 - Files analyzed: {stage3_result.total_analyzed}")
                        logger.info(f"Stage 3 - Analysis errors: {stage3_result.total_errors}")
                        logger.info(f"Stage 4 - Categories created: {stage4_result.total_categories}")
                        logger.info(f"Stage 4 - Files assigned: {stage4_result.total_assigned}")
                        logger.info("=" * 60)
                    
                        # Save complete results if requested (backward compatible)
                        if args.output and not args.stage4_output:
                            output_path = Path(args.output)
                            logger.info(f"\nSaving complete results to: {output_path}")
                            with open(output_path, 'w') as f:
                                json.dump(stage4_result.to_dict(), f, indent=2)
                            logger.info("Complete results saved")
            
                else:
                    # Stage 4 skipped
                    logger.info("")
                    logger.info("=" * 60)
                    logger.info("FINAL SUMMARY (Stage 4 skipped)")
                    logger.info("=" * 60)
                    logger.info(f"Stage 1 - Files scanned: {stage2_result.stage1_result.total_files}")
                    logger.info(f"Stage 1 - MIME types: {len(stage2_result.stage1_result.unique_mime_types)}")
                    logger.info(f"Stage 2 - Models discovered: {len(stage2_result.available_models)}")
                    logger.info(f"Stage 2 - Model mappings: {len(stage2_result.mime_to_model_mapping)}")
                    logger.info(f"Stage 3 - Files analyzed: {stage3_result.total_analyzed}")
                    logger.info(f"Stage 3 - Analysis errors: {stage3_result.total_errors}")
                    logger.info("=" * 60)
                
                    # Save complete results if requested (backward compatible)
                    if args.output and not args.stage3_output:
                        output_path = Path(args.output)
                        logger.info(f"\nSaving complete results to: {output_path}")
                        with open(output_path, 'w') as f:
                            json.dump(stage3_result.to_dict(), f, indent=2)
                        logger.info("Complete results saved")
            
            else:
                # Stage 3 skipped - display Stage 2 summary
                logger.info("")
                logger.info("=" * 60)
                logger.info("FINAL SUMMARY (Stage 3 skipped)")
                logger.info("=" * 60)
                logger.info(f"Stage 1 - Files scanned: {stage2_result.stage1_result.total_files}")
                logger.info(f"Stage 1 - MIME types: {len(stage2_result.stage1_result.unique_mime_types)}")
                logger.info(f"Stage 2 - Models discovered: {len(stage2_result.available_models)}")
                logger.info(f"Stage 2 - Model mappings: {len(stage2_result.mime_to_model_mapping)}")
                logger.info("=" * 60)
            
                # Save Stage 2 results if requested
                if args.output:
                    output_path = Path(args.output)
                    logger.info(f"\nSaving Stage 2 results to: {output_path}")
                    with open(output_path, 'w') as f:
                        json.dump(stage2_result.to_dict(), f, indent=2)
                    logger.info("Results saved successfully")
        
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
