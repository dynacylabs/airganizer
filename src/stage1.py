"""
Stage 1: File Enumeration and Metadata Collection
Main orchestrator for Airganizer Stage 1
"""

import json
import sys
import pickle
import shutil
import logging
import warnings
import contextlib
import io
from pathlib import Path
from typing import List, Dict, Any, Set
from tqdm import tqdm

from .config import Config
from .file_enumerator import FileEnumerator
from .metadata_extractor import MetadataExtractor
from .plan import AirganizerPlan


class Stage1Processor:
    """Process files for Stage 1: enumeration and metadata collection"""
    
    def __init__(self, config: Config):
        """
        Initialize Stage 1 processor
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.file_enumerator = None
        self.metadata_extractor = None
        self.results: List[Dict[str, Any]] = []
        self.processed_files: Set[str] = set()  # Track processed files for resumability
        self.cache_dir = None
        self.cache_file = None
        self.error_files_dir = None
        self.error_count = 0
        self.plan = None
        self.plan_file = None
        self.dry_run = config.is_dry_run()
        self.error_logger = None
    
    def initialize(self):
        """Initialize components"""
        # Validate configuration
        self.config.validate()
        
        # Setup cache directory
        self.cache_dir = Path(self.config.get_cache_directory())
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "stage1_progress.pkl"
        
        # Setup error logging
        self._setup_error_logging()
        
        # Suppress warnings from libraries
        warnings.filterwarnings('ignore')
        
        # Setup error files directory
        self.error_files_dir = Path(self.config.get_error_files_directory())
        self.error_files_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup plan file
        plan_file = self.config.get_plan_file()
        self.plan_file = self.cache_dir / plan_file if not Path(plan_file).is_absolute() else Path(plan_file)
        
        # Load or create plan
        self.plan = AirganizerPlan.load_or_create(self.plan_file)
        
        # Initialize file enumerator
        self.file_enumerator = FileEnumerator(
            source_directory=self.config.get_source_directory(),
            include_patterns=self.config.get_include_patterns(),
            exclude_patterns=self.config.get_exclude_patterns()
        )
        
        # Initialize metadata extractor
        self.metadata_extractor = MetadataExtractor(
            calculate_hash=self.config.should_calculate_hash()
        )
    
    def _setup_error_logging(self):
        """Setup error logging to file"""
        error_log_path = self.cache_dir / "errors.log"
        
        # Create a logger specifically for errors
        self.error_logger = logging.getLogger('airganizer_errors')
        self.error_logger.setLevel(logging.ERROR)
        
        # Remove any existing handlers
        self.error_logger.handlers = []
        
        # Create file handler
        file_handler = logging.FileHandler(error_log_path, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.ERROR)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.error_logger.addHandler(file_handler)
        
        # Don't propagate to root logger
        self.error_logger.propagate = False
        
        # Log session start
        self.error_logger.error("=" * 60)
        self.error_logger.error("Stage 1 Session Started")
        self.error_logger.error("=" * 60)
    
    def _load_cache(self) -> bool:
        """
        Load progress from cache if available
        
        Returns:
            True if cache was loaded successfully
        """
        if not self.cache_file.exists():
            return False
        
        try:
            with open(self.cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            self.results = cache_data.get('results', [])
            self.processed_files = cache_data.get('processed_files', set())
            self.error_count = cache_data.get('error_count', 0)
            
            print(f"Loaded cache: {len(self.results)} files already processed")
            return True
        
        except Exception as e:
            error_msg = f"Could not load cache: {e}"
            self.error_logger.error(error_msg)
            print(f"Warning: {error_msg}")
            return False
    
    def _save_cache(self):
        """Save current progress to cache"""
        try:
            cache_data = {
                'results': self.results,
                'processed_files': self.processed_files,
                'error_count': self.error_count,
            }
            
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
        
        except Exception as e:
            error_msg = f"Could not save cache: {e}"
            self.error_logger.error(error_msg)
            print(f"Warning: {error_msg}")
    
    def _clear_cache(self):
        """Clear cache file"""
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
        except Exception as e:
            error_msg = f"Could not clear cache: {e}"
            self.error_logger.error(error_msg)
            print(f"Warning: {error_msg}")
    
    def _move_error_file(self, file_path: Path, error_message: str = None) -> bool:
        """
        Move a problematic file to the error files directory (or record in plan if dry_run)
        
        Args:
            file_path: Path to the file that had an error
            error_message: The error message that occurred
        
        Returns:
            True if file was moved/recorded successfully
        """
        try:
            # Create a subdirectory structure to preserve relative paths
            source_dir = Path(self.config.get_source_directory())
            relative_path = file_path.relative_to(source_dir)
            
            # Destination path preserves directory structure
            dest_path = self.error_files_dir / relative_path
            
            # In dry run mode, just record in plan
            if self.dry_run:
                self.plan.add_error_file(
                    source_path=str(file_path.absolute()),
                    destination_path=str(dest_path.absolute()),
                    error_message=error_message or "Unknown error",
                    file_metadata={
                        'relative_path': str(relative_path),
                        'source_directory': str(source_dir.absolute())
                    }
                )
                # Debug log
                self.error_logger.error(f"  Added to plan (operation count now: {len(self.plan.operations)})")
                return True
            
            # In real mode, actually move the file
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(file_path), str(dest_path))
            
            # Create a detailed error log file alongside the moved file
            error_log_path = dest_path.with_suffix(dest_path.suffix + '.error.txt')
            with open(error_log_path, 'w') as f:
                from datetime import datetime
                f.write(f"=== File Processing Error ===\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"\n")
                f.write(f"Original Full Path:\n")
                f.write(f"  {file_path.absolute()}\n")
                f.write(f"\n")
                f.write(f"Original Location (relative to source):\n")
                f.write(f"  {relative_path}\n")
                f.write(f"\n")
                f.write(f"Source Directory:\n")
                f.write(f"  {source_dir.absolute()}\n")
                f.write(f"\n")
                f.write(f"Moved To:\n")
                f.write(f"  {dest_path.absolute()}\n")
                f.write(f"\n")
                if error_message:
                    f.write(f"Error Details:\n")
                    f.write(f"  {error_message}\n")
                    f.write(f"\n")
                f.write(f"=== End Error Log ===\n")
            
            return True
        
        except Exception as e:
            error_msg = f"Could not {'record' if self.dry_run else 'move'} error file {file_path}: {e}"
            self.error_logger.error(error_msg)
            return False
    
    def process(self) -> List[Dict[str, Any]]:
        """
        Process all files and collect metadata
        
        Returns:
            List of metadata dictionaries for all files
        """
        print("Stage 1: File Enumeration and Metadata Collection")
        print("=" * 60)
        print(f"Mode: {'DRY RUN (no files will be moved)' if self.dry_run else 'REAL MODE (files will be moved)'}")
        print(f"Source directory: {self.config.get_source_directory()}")
        print(f"Destination directory: {self.config.get_destination_directory()}")
        print(f"Cache directory: {self.cache_dir.absolute()}")
        print(f"Error files directory: {self.error_files_dir.absolute()}")
        print(f"Plan file: {self.plan_file.absolute()}")
        print(f"Error log: {self.cache_dir / 'errors.log'}")
        print()
        
        # Try to resume from cache
        resumed = False
        if self.config.should_resume_from_cache():
            resumed = self._load_cache()
            if resumed:
                print()
        
        # Get all files
        print("Enumerating files...")
        files = self.file_enumerator.get_files_list()
        total_files = len(files)
        
        print(f"Found {total_files} files to process")
        if resumed:
            remaining = total_files - len(self.processed_files)
            print(f"Resuming: {len(self.processed_files)} already processed, {remaining} remaining")
        print()
        
        # Process each file
        print("Extracting metadata...")
        
        max_file_size = self.config.get_max_file_size()
        cache_interval = self.config.get_cache_interval()
        skipped_count = 0
        files_since_cache = 0
        
        for file_path in tqdm(files, desc="Processing files", unit="file"):
            try:
                # Skip if already processed (from cache)
                file_path_str = str(file_path.absolute())
                if file_path_str in self.processed_files:
                    continue
                
                # Check file size limit
                if max_file_size > 0 and file_path.stat().st_size > max_file_size:
                    skipped_count += 1
                    self.processed_files.add(file_path_str)
                    continue
                
                # Extract metadata with stderr suppression
                # Suppress stderr to prevent library errors from appearing in console
                stderr_capture = io.StringIO()
                try:
                    with contextlib.redirect_stderr(stderr_capture):
                        file_metadata = self.metadata_extractor.extract_all_metadata(
                            file_path=file_path,
                            extract_exif=self.config.should_extract_exif(),
                            extract_audio=self.config.should_extract_audio_metadata(),
                            extract_video=self.config.should_extract_video_metadata(),
                            extract_document=self.config.should_extract_document_metadata()
                        )
                    
                    # Check if any stderr output was captured (indicates library errors)
                    stderr_output = stderr_capture.getvalue()
                    if stderr_output and ('error' in stderr_output.lower() or 'invalid' in stderr_output.lower()):
                        # Library had errors - treat as failed
                        raise Exception(f"Library error: {stderr_output.strip()[:200]}")  # Limit error message length
                    elif stderr_output:
                        # Just warnings - log but don't fail
                        self.error_logger.error(f"Library warnings for {file_path.name}:")
                        self.error_logger.error(f"  {stderr_output.strip()[:500]}")
                    
                    self.results.append(file_metadata.to_dict())
                    self.processed_files.add(file_path_str)
                    files_since_cache += 1
                    
                    # Save cache periodically
                    if files_since_cache >= cache_interval:
                        self._save_cache()
                        files_since_cache = 0
                
                except KeyboardInterrupt:
                    raise
                
                except Exception as e:
                    # This catches all extraction errors
                    self.error_count += 1
                    error_msg = str(e)
                    
                    # Get stderr output if any
                    stderr_output = stderr_capture.getvalue()
                    if stderr_output:
                        error_msg = f"{error_msg}\nLibrary output: {stderr_output.strip()}"
                    
                    # Get relative path for clearer output
                    try:
                        source_dir = Path(self.config.get_source_directory())
                        relative_path = file_path.relative_to(source_dir)
                        display_path = str(relative_path)
                    except:
                        display_path = str(file_path)
                    
                    # Log error to file
                    self.error_logger.error(f"Error processing file: {display_path}")
                    self.error_logger.error(f"  Full path: {file_path.absolute()}")
                    self.error_logger.error(f"  Error: {error_msg}")
                    
                    # Move/record the problematic file
                    if self._move_error_file(file_path, error_msg):
                        error_dest = self.error_files_dir / Path(display_path)
                        action = "Recorded in plan" if self.dry_run else f"Moved to {error_dest}"
                        self.error_logger.error(f"  Action: {action}")
                        
                        # Save plan immediately after adding error operation
                        self.plan.save(self.plan_file)
                    
                    # Mark as processed to avoid retrying
                    # IMPORTANT: Do NOT add to results - file had an error
                    self.processed_files.add(file_path_str)
                    files_since_cache += 1
                    
                    # Save cache after error to ensure we don't retry this file
                    if files_since_cache >= cache_interval:
                        self._save_cache()
                        files_since_cache = 0
            
            except KeyboardInterrupt:
                # Allow user to interrupt
                print("\n\nProcess interrupted by user")
                raise
            
            except Exception as outer_e:
                # Catch-all for unexpected errors in the outer loop
                print(f"\nUnexpected error in processing loop: {outer_e}", file=sys.stderr)
                self.error_logger.error(f"Unexpected outer loop error: {outer_e}")
        
        # Final cache save
        if files_since_cache > 0:
            self._save_cache()
        
        # Save the plan
        self.plan.mark_stage_complete('stage1')
        self.plan.save(self.plan_file)
        
        # Close error logger
        if self.error_logger:
            self.error_logger.error("=" * 60)
            self.error_logger.error("Stage 1 Session Completed")
            self.error_logger.error("=" * 60)
            for handler in self.error_logger.handlers:
                handler.close()
        
        print()
        print("=" * 60)
        print(f"Processing complete!")
        print(f"Total files found: {total_files}")
        print(f"Successfully processed: {len(self.results)}")
        if skipped_count > 0:
            print(f"Skipped (size limit): {skipped_count}")
        if self.error_count > 0:
            action = "recorded in plan" if self.dry_run else f"moved to {self.error_files_dir}"
            print(f"Errors ({action}): {self.error_count}")
            print(f"  See error details in: {self.cache_dir / 'errors.log'}")
            if self.dry_run:
                print(f"  These errors have been added to the plan file")
        print()
        
        return self.results
    
    def save_results(self, output_file: str = None):
        """
        Save results to JSON file
        
        Args:
            output_file: Output file path (uses config if not specified)
        """
        if output_file is None:
            output_file = self.config.get_stage1_output_file()
        
        output_path = Path(output_file)
        
        # If output path is relative, place it in the cache directory
        if not output_path.is_absolute():
            output_path = self.cache_dir / output_path
        
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare output data
        output_data = {
            'stage': 1,
            'description': 'File enumeration and metadata collection',
            'source_directory': self.config.get_source_directory(),
            'destination_directory': self.config.get_destination_directory(),
            'total_files': len(self.results),
            'files': self.results
        }
        
        # Save to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        print(f"Results saved to: {output_path.absolute()}")
        
        # Clear cache after successful completion
        self._clear_cache()
        
        # Print plan summary
        print()
        print("Plan Summary:")
        plan_summary = self.plan.get_summary()
        print(f"  Total operations planned: {plan_summary['total_operations']}")
        
        # Debug: Check if operations exist
        if hasattr(self.plan, 'operations'):
            print(f"  Debug: Plan has {len(self.plan.operations)} operation objects")
        
        if plan_summary['total_operations'] > 0:
            for op_type, count in plan_summary.get('by_type', {}).items():
                print(f"    {op_type}: {count}")
            print(f"  Plan saved to: {self.plan_file.absolute()}")
            
            # If there are error operations, show details
            if 'error' in plan_summary.get('by_type', {}):
                print()
                error_count = plan_summary['by_type']['error']
                print(f"  ⚠ {error_count} file(s) with errors will be moved to error directory when plan is executed:")
                error_ops = self.plan.get_error_operations_summary()
                for i, op in enumerate(error_ops[:5], 1):  # Show first 5
                    source_path = Path(op['source'])
                    print(f"    {i}. {source_path.name}")
                if len(error_ops) > 5:
                    print(f"    ... and {len(error_ops) - 5} more (see plan file for full list)")
                print()
                print(f"  Set dry_run: false in config to execute these operations")
        else:
            print(f"  No operations to execute")
        
        # Print statistics
        total_size = sum(file['file_size'] for file in self.results)
        total_size_human = MetadataExtractor._human_readable_size(total_size)
        
        print()
        print("Statistics:")
        print(f"  Total files: {len(self.results)}")
        print(f"  Total size: {total_size_human}")
        
        # Count by media type
        media_types = {}
        for file in self.results:
            media_type = file.get('media_type', 'unknown')
            media_types[media_type] = media_types.get(media_type, 0) + 1
        
        if media_types:
            print()
            print("Files by media type:")
            for media_type, count in sorted(media_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  {media_type or 'unknown'}: {count}")
    
    def run(self):
        """Run the complete Stage 1 process"""
        try:
            self.initialize()
            self.process()
            self.save_results()
        except Exception as e:
            error_msg = f"Error during Stage 1 processing: {e}"
            print(error_msg, file=sys.stderr)
            if self.error_logger:
                self.error_logger.error(error_msg)
                self.error_logger.error("=" * 60)
                self.error_logger.error("Stage 1 Session Failed")
                self.error_logger.error("=" * 60)
            raise


def main():
    """Main entry point for Stage 1"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Airganizer Stage 1: File Enumeration and Metadata Collection'
    )
    parser.add_argument(
        '--config',
        '-c',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    parser.add_argument(
        '--output',
        '-o',
        help='Output file path (overrides config)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = Config(args.config)
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {args.config}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Run Stage 1
    processor = Stage1Processor(config)
    
    try:
        processor.initialize()
        processor.process()
        processor.save_results(args.output)
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
