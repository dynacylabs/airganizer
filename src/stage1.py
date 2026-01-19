"""Stage 1: File scanning, enumeration, and metadata collection."""

import logging
import magic
from pathlib import Path
from typing import List, Optional

from .config import Config
from .models import FileInfo, Stage1Result
from .metadata_extractor import extract_exif_data, extract_metadata_by_mime, run_binwalk
from .cache import CacheManager


logger = logging.getLogger(__name__)


class Stage1Scanner:
    """Stage 1: Scans directory and collects file information with metadata."""
    
    def __init__(self, config: Config, cache_manager: Optional[CacheManager] = None):
        """
        Initialize the Stage 1 scanner.
        
        Args:
            config: Configuration object
            cache_manager: Optional CacheManager for caching results
        """
        self.config = config
        self.mime = magic.Magic(mime=True)
        self.cache_manager = cache_manager or CacheManager(
            cache_dir=config.cache_directory,
            enabled=config.cache_enabled,
            ttl_hours=config.cache_ttl_hours
        )
        logger.debug(f"Stage1Scanner initialized with cache_enabled={config.cache_enabled}")
        logger.debug(f"  - include_hidden={config.include_hidden}")
        logger.debug(f"  - exclude_extensions={config.exclude_extensions}")
        logger.debug(f"  - max_file_size={config.max_file_size}")
    
    def _should_exclude_file(self, file_path: Path) -> bool:
        """
        Check if a file should be excluded based on configuration.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file should be excluded, False otherwise
        """
        # Check if hidden file should be excluded
        if not self.config.include_hidden and file_path.name.startswith('.'):
            logger.debug(f"Excluding hidden file: {file_path}")
            return True
        
        # Check if file extension should be excluded
        if file_path.suffix.lower() in self.config.exclude_extensions:
            return True
        
        # Check file size limit
        if self.config.max_file_size > 0:
            try:
                if file_path.stat().st_size > self.config.max_file_size:
                    logger.info(f"Excluding file due to size limit: {file_path}")
                    return True
            except OSError as e:
                logger.warning(f"Cannot stat file {file_path}: {e}")
                return True
        
        return False
    
    def _should_exclude_dir(self, dir_path: Path) -> bool:
        """
        Check if a directory should be excluded based on configuration.
        
        Args:
            dir_path: Path to the directory
            
        Returns:
            True if directory should be excluded, False otherwise
        """
        # Check if hidden directory should be excluded
        if not self.config.include_hidden and dir_path.name.startswith('.'):
            return True
        
        # Check if directory is in exclude list
        if dir_path.name in self.config.exclude_dirs:
            return True
        
        return False
    
    def _get_mime_type(self, file_path: Path) -> str:
        """
        Get the MIME type of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            MIME type string
        """
        try:
            return self.mime.from_file(str(file_path))
        except Exception as e:
            logger.warning(f"Could not determine MIME type for {file_path}: {e}")
            return "application/octet-stream"
    
    def _scan_file(self, file_path: Path, result: Stage1Result) -> None:
        """
        Scan a single file and add it to results with metadata.
        Uses cache if available and valid.
        
        Args:
            file_path: Path to the file
            result: Stage1Result object to add the file to
        """
        try:
            if self._should_exclude_file(file_path):
                logger.debug(f"Excluding file: {file_path}")
                return
            
            # Try to get from cache first
            file_info = self.cache_manager.get_stage1_file_cache(str(file_path.absolute()))
            
            if file_info:
                # Cache hit - use cached data
                result.add_file(file_info)
                logger.debug(f"Loaded from cache: {file_path}")
                return
            
            # Cache miss - process file
            logger.debug(f"Processing file: {file_path}")
            
            # Get basic file information
            file_size = file_path.stat().st_size
            mime_type = self._get_mime_type(file_path)
            
            # Extract EXIF data for image files
            exif_data = {}
            if mime_type.startswith('image/'):
                logger.debug(f"Extracting EXIF data from {file_path}")
                exif_data = extract_exif_data(file_path)
            
            # Extract metadata based on MIME type
            logger.debug(f"Extracting metadata from {file_path}")
            metadata = extract_metadata_by_mime(file_path, mime_type)
            
            # Run binwalk analysis
            logger.debug(f"Running binwalk on {file_path}")
            binwalk_output = run_binwalk(file_path)
            
            # Create FileInfo object with all metadata
            file_info = FileInfo(
                file_name=file_path.name,
                file_path=str(file_path.absolute()),
                mime_type=mime_type,
                file_size=file_size,
                exif_data=exif_data,
                binwalk_output=binwalk_output,
                metadata=metadata
            )
            
            # Save to cache
            self.cache_manager.save_stage1_file_cache(file_info)
            
            result.add_file(file_info)
            logger.debug(f"Added file: {file_path} (MIME: {mime_type})")
            
        except Exception as e:
            error_msg = f"Error processing file: {e}"
            logger.error(f"{error_msg} - {file_path}")
            result.add_error(str(file_path), error_msg)
    
    def _scan_directory_recursive(self, directory: Path, result: Stage1Result) -> None:
        """
        Recursively scan a directory and collect file information.
        
        Args:
            directory: Directory path to scan
            result: Stage1Result object to add files to
        """
        try:
            for item in directory.iterdir():
                # Handle symbolic links
                if item.is_symlink() and not self.config.follow_symlinks:
                    logger.debug(f"Skipping symlink: {item}")
                    continue
                
                if item.is_file():
                    self._scan_file(item, result)
                elif item.is_dir():
                    if self._should_exclude_dir(item):
                        logger.debug(f"Excluding directory: {item}")
                        continue
                    
                    if self.config.recursive:
                        self._scan_directory_recursive(item, result)
                        
        except PermissionError as e:
            error_msg = f"Permission denied: {e}"
            logger.warning(f"{error_msg} - {directory}")
            result.add_error(str(directory), error_msg)
        except Exception as e:
            error_msg = f"Error scanning directory: {e}"
            logger.error(f"{error_msg} - {directory}")
            result.add_error(str(directory), error_msg)
    
    def scan(self, source_directory: str, use_cache: bool = True) -> Stage1Result:
        """
        Scan the source directory and collect file information with metadata.
        
        Args:
            source_directory: Path to the source directory
            use_cache: Whether to use cached results if available
            
        Returns:
            Stage1Result object containing all collected file information,
            unique MIME types, and extracted metadata (EXIF, binwalk, etc.)
        """
        source_path = Path(source_directory).resolve()
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source directory not found: {source_directory}")
        
        if not source_path.is_dir():
            raise NotADirectoryError(f"Source path is not a directory: {source_directory}")
        
        # Try to load complete result from cache first
        if use_cache:
            cached_result = self.cache_manager.get_stage1_result_cache(str(source_path))
            if cached_result:
                logger.info(f"Loaded complete Stage 1 result from cache")
                logger.info(f"  Files: {cached_result.total_files}")
                logger.info(f"  MIME types: {len(cached_result.unique_mime_types)}")
                return cached_result
        
        logger.info(f"Starting Stage 1: File enumeration and metadata collection")
        logger.info(f"Scanning directory: {source_path}")
        if use_cache:
            logger.info(f"Cache enabled: Will use cached file data where available")
        
        # Initialize result object
        result = Stage1Result(
            source_directory=str(source_path),
            total_files=0,
            files=[],
            errors=[]
        )
        
        # Scan the directory for files and collect metadata
        self._scan_directory_recursive(source_path, result)
        
        logger.info(f"File scanning complete: Found {result.total_files} files")
        if result.errors:
            logger.warning(f"Encountered {len(result.errors)} errors during scanning")
        
        # Extract unique MIME types
        logger.info("Extracting unique MIME types")
        result.extract_unique_mime_types()
        logger.info(f"Found {len(result.unique_mime_types)} unique MIME types")
        
        # Save complete result to cache
        if use_cache:
            self.cache_manager.save_stage1_result_cache(result)
        
        logger.info("=" * 60)
        logger.info("Stage 1 complete!")
        logger.info(f"  Files: {result.total_files}")
        logger.info(f"  MIME types: {len(result.unique_mime_types)}")
        logger.info(f"  Errors: {len(result.errors)}")
        logger.info("=" * 60)
        
        return result
