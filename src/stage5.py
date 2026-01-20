"""Stage 5: Physical file organization - move files to their target locations."""

import logging
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field

from .config import Config
from .models import Stage4Result, MoveOperation, Stage5Result
from .cache import CacheManager


logger = logging.getLogger(__name__)


class Stage5Processor:
    """Stage 5: Moves files to their organized locations."""
    
    def __init__(self, config: Config, cache_manager: Optional[CacheManager] = None, progress_manager=None):
        """
        Initialize the Stage 5 processor.
        
        Args:
            config: Configuration object
            cache_manager: Optional CacheManager for caching results
            progress_manager: Optional ProgressManager for progress tracking
        """
        self.config = config
        self.cache_manager = cache_manager or CacheManager(
            cache_dir=config.cache_directory,
            enabled=config.cache_enabled
        )
        self.progress_manager = progress_manager
        logger.debug("Stage5Processor initialized")
        logger.debug("  - Physical file organization enabled")
    
    def _create_target_directory(self, target_dir: Path, dry_run: bool) -> bool:
        """
        Create target directory if it doesn't exist.
        
        Args:
            target_dir: Directory to create
            dry_run: If True, don't actually create
            
        Returns:
            True if directory exists or was created, False on error
        """
        try:
            if target_dir.exists():
                logger.debug(f"Target directory already exists: {target_dir}")
                return True
            
            if dry_run:
                logger.debug(f"[DRY-RUN] Would create directory: {target_dir}")
                return True
            
            target_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {target_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create directory {target_dir}: {e}")
            return False
    
    def _move_file(
        self,
        source_path: Path,
        target_path: Path,
        dry_run: bool,
        overwrite: bool = False
    ) -> tuple[bool, Optional[str]]:
        """
        Move a file to its target location.
        
        Args:
            source_path: Original file path
            target_path: Destination file path
            dry_run: If True, don't actually move
            overwrite: If True, overwrite existing files
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Check if source exists
            if not source_path.exists():
                return False, f"Source file not found: {source_path}"
            
            # Check if target already exists
            if target_path.exists() and not overwrite:
                logger.warning(f"Target already exists: {target_path}")
                return False, f"Target already exists: {target_path}"
            
            if dry_run:
                logger.info(f"[DRY-RUN] Would move: {source_path} -> {target_path}")
                return True, None
            
            # Perform the move
            shutil.move(str(source_path), str(target_path))
            logger.info(f"Moved: {source_path.name}")
            logger.info(f"  From: {source_path}")
            logger.info(f"  To:   {target_path}")
            
            return True, None
            
        except PermissionError as e:
            error = f"Permission denied: {e}"
            logger.error(error)
            return False, error
        except OSError as e:
            error = f"OS error: {e}"
            logger.error(error)
            return False, error
        except Exception as e:
            error = f"Unexpected error: {e}"
            logger.error(error)
            return False, error
    
    def _create_log_file(
        self,
        log_dir: Path,
        entries: List[dict],
        log_type: str,
        dry_run: bool
    ) -> None:
        """
        Create a log file with entries.
        
        Args:
            log_dir: Directory where log file should be created
            entries: List of log entries
            log_type: Type of log (excluded or errors)
            dry_run: If True, don't actually create
        """
        if not entries:
            return
        
        if dry_run:
            logger.info(f"[DRY-RUN] Would create {log_type}_log.json in {log_dir}")
            return
        
        try:
            log_file = log_dir / f"{log_type}_log.json"
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'total': len(entries),
                'entries': entries
            }
            
            with open(log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            logger.info(f"Created {log_type} log: {log_file}")
            
        except Exception as e:
            logger.error(f"Failed to create {log_type} log: {e}")
    
    def process(
        self,
        stage4_result: Stage4Result,
        destination_root: str,
        dry_run: bool = False,
        overwrite: bool = False,
        use_cache: bool = True
    ) -> Stage5Result:
        """
        Process Stage 4 results to physically organize files.
        Moves ALL files from source: organized files to taxonomy structure,
        excluded files to _excluded/, error files to _errors/.
        
        Args:
            stage4_result: Results from Stage 4
            destination_root: Root directory for organized files
            dry_run: If True, simulate moves without actually moving files
            overwrite: If True, overwrite existing files at destination
            use_cache: Whether to use cached results if available (only for dry-run)
            
        Returns:
            Stage5Result with move operation details
        """
        logger.info("=" * 60)
        logger.info("Starting Stage 5: Physical File Organization")
        logger.debug(f"Stage5Processor configuration:")
        logger.debug(f"  - destination_root: {destination_root}")
        logger.debug(f"  - dry_run: {dry_run}")
        logger.debug(f"  - overwrite: {overwrite}")
        logger.debug(f"  - cache_enabled: {self.cache_manager.enabled}")
        
        if dry_run:
            logger.info("*** DRY-RUN MODE: No files will be moved ***")
            # Try to load from cache for dry-run
            if use_cache and self.cache_manager.enabled:
                source_dir = stage4_result.stage3_result.stage2_result.stage1_result.source_directory
                cached_result = self.cache_manager.get_stage5_result_cache(source_dir)
                if cached_result:
                    logger.info("✓ Loaded Stage 5 results from cache")
                    logger.info(f"  Total files: {cached_result.total_files}")
                    logger.info(f"  Successful moves: {cached_result.successful_moves}")
                    logger.info(f"  Failed moves: {cached_result.failed_moves}")
                    logger.info(f"  Excluded: {cached_result.excluded_moves}")
                    logger.info(f"  Errors: {cached_result.error_moves}")
                    logger.info("=" * 60)
                    return cached_result
        
        logger.info("=" * 60)
        
        # Initialize result
        result = Stage5Result(
            stage4_result=stage4_result,
            destination_root=destination_root,
            dry_run=dry_run
        )
        
        destination_root_path = Path(destination_root)
        
        # Verify destination root exists or can be created
        if not dry_run:
            try:
                destination_root_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Destination root ready: {destination_root}")
            except Exception as e:
                logger.error(f"Cannot create destination root: {e}")
                return result
        
        # Create special directories
        excluded_dir = destination_root_path / "_excluded"
        errors_dir = destination_root_path / "_errors"
        
        # Track log entries
        excluded_log_entries = []
        error_log_entries = []
        
        # Get Stage 1 result for excluded files
        stage1_result = stage4_result.stage3_result.stage2_result.stage1_result
        
        # Calculate garbage and organized files
        garbage_folder = self.config.get('general.garbage_folder', '_garbage')
        garbage_files = sum(1 for a in stage4_result.file_assignments if a.target_path == garbage_folder)
        organized_files = len(stage4_result.file_assignments) - garbage_files
        
        # Calculate total operations
        total_assignments = len(stage4_result.file_assignments)
        total_excluded = len(stage1_result.excluded_files)
        total_errors = sum(1 for a in stage4_result.stage3_result.file_analyses if a.error)
        total_operations = total_assignments + total_excluded + total_errors
        
        logger.info(f"Total operations: {total_operations}")
        logger.info(f"  - Organized files: {organized_files}")
        logger.info(f"  - Garbage files: {garbage_files}")
        logger.info(f"  - Excluded files: {total_excluded}")
        logger.info(f"  - Error files: {total_errors}")
        
        # Start progress tracking
        if self.progress_manager:
            self.progress_manager.start_stage(5, "File Organization", total_operations)
        
        current_operation = 0
        
        # Process organized files (successfully analyzed and assigned)
        logger.info(f"Processing {total_assignments} organized file assignments")
        
        for idx, assignment in enumerate(stage4_result.file_assignments, 1):
            current_operation += 1
            
            # Update progress
            if self.progress_manager:
                self.progress_manager.update_file_info(
                    f"[{current_operation}/{total_operations}] Moving organized file: {Path(assignment.file_path).name}\n"
                    f"Source: {assignment.file_path}\n"
                    f"Target: {assignment.target_path}/{assignment.proposed_filename}"
                )
                self.progress_manager.update_stage_progress(current_operation)
            
            logger.info("-" * 60)
            logger.info(f"Organized File {idx}/{total_assignments}: {Path(assignment.file_path).name}")
            logger.debug(f"  Original path: {assignment.file_path}")
            logger.debug(f"  Target category: {assignment.target_path}")
            logger.debug(f"  New filename: {assignment.proposed_filename}")
            
            # Construct paths
            source_path = Path(assignment.file_path)
            target_dir = destination_root_path / assignment.target_path
            target_file = target_dir / assignment.proposed_filename
            
            # Determine category based on target path
            garbage_folder = self.config.get('general.garbage_folder', '_garbage')
            category = "garbage" if assignment.target_path == garbage_folder else "organized"
            
            # Create operation record
            operation = MoveOperation(
                source_path=assignment.file_path,
                target_path=assignment.target_path,
                target_filename=assignment.proposed_filename,
                full_target=str(target_file),
                category=category
            )
            
            # Create target directory
            if not self._create_target_directory(target_dir, dry_run):
                operation.error = f"Failed to create directory: {target_dir}"
                result.add_operation(operation)
                continue
            
            # Move the file
            success, error = self._move_file(source_path, target_file, dry_run, overwrite)
            operation.success = success
            operation.error = error
            
            result.add_operation(operation)
        
        # Process excluded files
        total_excluded = len(stage1_result.excluded_files)
        if total_excluded > 0:
            logger.info("")
            logger.info("=" * 60)
            logger.info(f"Processing {total_excluded} excluded files")
            logger.info("=" * 60)
            
            # Create excluded directory
            if not self._create_target_directory(excluded_dir, dry_run):
                logger.error(f"Failed to create excluded directory: {excluded_dir}")
            else:
                for idx, excluded in enumerate(stage1_result.excluded_files, 1):
                    current_operation += 1
                    
                    # Update progress
                    if self.progress_manager:
                        self.progress_manager.update_file_info(
                            f"[{current_operation}/{total_operations}] Moving excluded file: {excluded.file_name}\n"
                            f"Reason: {excluded.reason}\n"
                            f"Rule: {excluded.rule}"
                        )
                        self.progress_manager.update_stage_progress(current_operation)
                    
                    logger.info("-" * 60)
                    logger.info(f"Excluded File {idx}/{total_excluded}: {excluded.file_name}")
                    logger.debug(f"  Reason: {excluded.reason}")
                    logger.debug(f"  Rule: {excluded.rule}")
                    
                    source_path = Path(excluded.file_path)
                    target_file = excluded_dir / excluded.file_name
                    
                    # Handle filename conflicts
                    if target_file.exists() and not overwrite:
                        # Add timestamp to make unique
                        stem = target_file.stem
                        suffix = target_file.suffix
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        target_file = excluded_dir / f"{stem}_{timestamp}{suffix}"
                    
                    operation = MoveOperation(
                        source_path=excluded.file_path,
                        target_path="_excluded",
                        target_filename=target_file.name,
                        full_target=str(target_file),
                        category="excluded"
                    )
                    
                    # Move the file
                    success, error = self._move_file(source_path, target_file, dry_run, overwrite)
                    operation.success = success
                    operation.error = error
                    
                    result.add_operation(operation)
                    
                    # Add to log
                    if success or dry_run:
                        excluded_log_entries.append({
                            'file_name': excluded.file_name,
                            'original_path': excluded.file_path,
                            'reason': excluded.reason,
                            'rule': excluded.rule,
                            'moved_to': str(target_file)
                        })
                
                # Create exclusion log
                self._create_log_file(excluded_dir, excluded_log_entries, "exclusions", dry_run)
        
        # Process error files (files that failed analysis in Stage 3)
        stage3_result = stage4_result.stage3_result
        error_analyses = [a for a in stage3_result.file_analyses if a.error]
        total_errors = len(error_analyses)
        
        if total_errors > 0:
            logger.info("")
            logger.info("=" * 60)
            logger.info(f"Processing {total_errors} error files")
            logger.info("=" * 60)
            
            # Create errors directory
            if not self._create_target_directory(errors_dir, dry_run):
                logger.error(f"Failed to create errors directory: {errors_dir}")
            else:
                for idx, analysis in enumerate(error_analyses, 1):
                    current_operation += 1
                    
                    # Update progress
                    if self.progress_manager:
                        self.progress_manager.update_file_info(
                            f"[{current_operation}/{total_operations}] Moving error file: {Path(analysis.file_path).name}\n"
                            f"Error: {analysis.error}\n"
                            f"Model: {analysis.assigned_model}"
                        )
                        self.progress_manager.update_stage_progress(current_operation)
                    
                    logger.info("-" * 60)
                    logger.info(f"Error File {idx}/{total_errors}: {Path(analysis.file_path).name}")
                    logger.debug(f"  Error: {analysis.error}")
                    
                    source_path = Path(analysis.file_path)
                    target_file = errors_dir / source_path.name
                    
                    # Handle filename conflicts
                    if target_file.exists() and not overwrite:
                        stem = target_file.stem
                        suffix = target_file.suffix
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        target_file = errors_dir / f"{stem}_{timestamp}{suffix}"
                    
                    operation = MoveOperation(
                        source_path=analysis.file_path,
                        target_path="_errors",
                        target_filename=target_file.name,
                        full_target=str(target_file),
                        category="error"
                    )
                    
                    # Move the file
                    success, error = self._move_file(source_path, target_file, dry_run, overwrite)
                    operation.success = success
                    operation.error = error
                    
                    result.add_operation(operation)
                    
                    # Add to log
                    if success or dry_run:
                        error_log_entries.append({
                            'file_name': source_path.name,
                            'original_path': analysis.file_path,
                            'error': analysis.error,
                            'stage': 'Stage 3 (AI Analysis)',
                            'assigned_model': analysis.assigned_model,
                            'moved_to': str(target_file)
                        })
                
                # Create error log
                self._create_log_file(errors_dir, error_log_entries, "errors", dry_run)
        
        # Save complete Stage 5 result to cache (useful for dry-run mode)
        if use_cache and self.cache_manager.enabled:
            source_dir = stage4_result.stage3_result.stage2_result.stage1_result.source_directory
            self.cache_manager.save_stage5_result_cache(result)
        
        # Complete stage progress
        if self.progress_manager:
            self.progress_manager.complete_stage()
        
        # Final summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("Stage 5 complete!")
        logger.info(f"  Total files: {result.total_files}")
        logger.info(f"  Organized moves: {result.successful_moves}")
        logger.info(f"  Garbage moves: {result.garbage_moves}")
        logger.info(f"  Excluded moves: {result.excluded_moves}")
        logger.info(f"  Error moves: {result.error_moves}")
        logger.info(f"  Failed moves: {result.failed_moves}")
        logger.info(f"  Skipped moves: {result.skipped_moves}")
        
        if dry_run:
            logger.info("")
            logger.info("*** DRY-RUN MODE: No files were actually moved ***")
        else:
            logger.info("")
            logger.info("*** All files have been moved from source directory ***")
        
        logger.info("=" * 60)
        
        return result
