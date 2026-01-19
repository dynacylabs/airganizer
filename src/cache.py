"""Cache management for resumable operations."""

import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from .models import FileInfo, Stage1Result, Stage2Result, ModelInfo


logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching for Stage 1 and Stage 2 results."""
    
    def __init__(self, cache_dir: str, enabled: bool = True, ttl_hours: int = 24):
        """
        Initialize the cache manager.
        
        Args:
            cache_dir: Directory to store cache files
            enabled: Whether caching is enabled
            ttl_hours: Time-to-live for cache entries in hours
        """
        self.cache_dir = Path(cache_dir)
        self.enabled = enabled
        self.ttl = timedelta(hours=ttl_hours)
        
        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Cache enabled at: {self.cache_dir}")
        else:
            logger.info("Cache disabled")
    
    def _get_file_hash(self, file_path: str) -> str:
        """
        Generate a hash for a file path.
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA256 hash of the file path
        """
        return hashlib.sha256(file_path.encode()).hexdigest()[:16]
    
    def _get_directory_hash(self, directory: str) -> str:
        """
        Generate a hash for a directory path.
        
        Args:
            directory: Path to the directory
            
        Returns:
            SHA256 hash of the directory path
        """
        return hashlib.sha256(directory.encode()).hexdigest()[:16]
    
    def _is_cache_valid(self, cache_path: Path, source_file: Optional[Path] = None) -> bool:
        """
        Check if a cache file is valid.
        
        Args:
            cache_path: Path to the cache file
            source_file: Optional source file to check modification time
            
        Returns:
            True if cache is valid, False otherwise
        """
        if not cache_path.exists():
            return False
        
        # Check TTL
        cache_mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - cache_mtime > self.ttl:
            logger.debug(f"Cache expired: {cache_path}")
            return False
        
        # Check source file modification time if provided
        if source_file and source_file.exists():
            source_mtime = datetime.fromtimestamp(source_file.stat().st_mtime)
            if source_mtime > cache_mtime:
                logger.debug(f"Source file newer than cache: {source_file}")
                return False
        
        return True
    
    def get_stage1_file_cache(self, file_path: str) -> Optional[FileInfo]:
        """
        Get cached FileInfo for a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            FileInfo object if cached and valid, None otherwise
        """
        if not self.enabled:
            return None
        
        file_hash = self._get_file_hash(file_path)
        cache_path = self.cache_dir / f"file_{file_hash}.json"
        
        source_path = Path(file_path)
        if not self._is_cache_valid(cache_path, source_path):
            return None
        
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
            
            file_info = FileInfo(
                file_name=data['file_name'],
                file_path=data['file_path'],
                mime_type=data['mime_type'],
                file_size=data['file_size'],
                exif_data=data.get('exif_data', {}),
                binwalk_output=data.get('binwalk_output', ''),
                metadata=data.get('metadata', {})
            )
            
            logger.debug(f"Cache hit for file: {file_path}")
            return file_info
        
        except Exception as e:
            logger.warning(f"Failed to load cache for {file_path}: {e}")
            return None
    
    def save_stage1_file_cache(self, file_info: FileInfo) -> None:
        """
        Save FileInfo to cache.
        
        Args:
            file_info: FileInfo object to cache
        """
        if not self.enabled:
            return
        
        file_hash = self._get_file_hash(file_info.file_path)
        cache_path = self.cache_dir / f"file_{file_hash}.json"
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(file_info.to_dict(), f, indent=2)
            
            logger.debug(f"Cached file: {file_info.file_path}")
        
        except Exception as e:
            logger.warning(f"Failed to save cache for {file_info.file_path}: {e}")
    
    def get_stage1_result_cache(self, source_directory: str) -> Optional[Stage1Result]:
        """
        Get cached Stage1Result for a directory.
        
        Args:
            source_directory: Source directory path
            
        Returns:
            Stage1Result if cached and valid, None otherwise
        """
        if not self.enabled:
            return None
        
        dir_hash = self._get_directory_hash(source_directory)
        cache_path = self.cache_dir / f"stage1_{dir_hash}.json"
        
        if not self._is_cache_valid(cache_path):
            return None
        
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
            
            files = [
                FileInfo(
                    file_name=f['file_name'],
                    file_path=f['file_path'],
                    mime_type=f['mime_type'],
                    file_size=f['file_size'],
                    exif_data=f.get('exif_data', {}),
                    binwalk_output=f.get('binwalk_output', ''),
                    metadata=f.get('metadata', {})
                )
                for f in data.get('files', [])
            ]
            
            result = Stage1Result(
                source_directory=data['source_directory'],
                total_files=data['total_files'],
                files=files,
                errors=data.get('errors', []),
                unique_mime_types=data.get('unique_mime_types', [])
            )
            
            logger.info(f"Loaded Stage 1 result from cache: {len(result.files)} files")
            return result
        
        except Exception as e:
            logger.warning(f"Failed to load Stage 1 cache: {e}")
            return None
    
    def save_stage1_result_cache(self, result: Stage1Result) -> None:
        """
        Save Stage1Result to cache.
        
        Args:
            result: Stage1Result to cache
        """
        if not self.enabled:
            return
        
        dir_hash = self._get_directory_hash(result.source_directory)
        cache_path = self.cache_dir / f"stage1_{dir_hash}.json"
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
            
            logger.info(f"Saved Stage 1 result to cache: {len(result.files)} files")
        
        except Exception as e:
            logger.warning(f"Failed to save Stage 1 cache: {e}")
    
    def get_stage2_result_cache(self, source_directory: str) -> Optional[Stage2Result]:
        """
        Get cached Stage2Result for a directory.
        
        Args:
            source_directory: Source directory path
            
        Returns:
            Stage2Result if cached and valid, None otherwise
        """
        if not self.enabled:
            return None
        
        dir_hash = self._get_directory_hash(source_directory)
        cache_path = self.cache_dir / f"stage2_{dir_hash}.json"
        
        if not self._is_cache_valid(cache_path):
            return None
        
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
            
            # Load Stage1Result
            stage1_data = data.get('stage1_result', {})
            files = [
                FileInfo(
                    file_name=f['file_name'],
                    file_path=f['file_path'],
                    mime_type=f['mime_type'],
                    file_size=f['file_size'],
                    exif_data=f.get('exif_data', {}),
                    binwalk_output=f.get('binwalk_output', ''),
                    metadata=f.get('metadata', {})
                )
                for f in stage1_data.get('files', [])
            ]
            
            stage1_result = Stage1Result(
                source_directory=stage1_data['source_directory'],
                total_files=stage1_data['total_files'],
                files=files,
                errors=stage1_data.get('errors', []),
                unique_mime_types=stage1_data.get('unique_mime_types', [])
            )
            
            # Load Stage2Result
            models = [
                ModelInfo(
                    name=m['name'],
                    type=m['type'],
                    provider=m['provider'],
                    model_name=m['model_name'],
                    capabilities=m['capabilities'],
                    description=m['description']
                )
                for m in data.get('available_models', [])
            ]
            
            result = Stage2Result(
                stage1_result=stage1_result,
                available_models=models,
                mime_to_model_mapping=data.get('mime_to_model_mapping', {}),
                model_connectivity=data.get('model_connectivity', {})
            )
            
            logger.info(f"Loaded Stage 2 result from cache")
            return result
        
        except Exception as e:
            logger.warning(f"Failed to load Stage 2 cache: {e}")
            return None
    
    def save_stage2_result_cache(self, result: Stage2Result) -> None:
        """
        Save Stage2Result to cache.
        
        Args:
            result: Stage2Result to cache
        """
        if not self.enabled:
            return
        
        dir_hash = self._get_directory_hash(result.stage1_result.source_directory)
        cache_path = self.cache_dir / f"stage2_{dir_hash}.json"
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
            
            logger.info(f"Saved Stage 2 result to cache")
        
        except Exception as e:
            logger.warning(f"Failed to save Stage 2 cache: {e}")
    
    def clear_cache(self, stage: Optional[str] = None) -> int:
        """
        Clear cache files.
        
        Args:
            stage: Optional stage to clear ('stage1', 'stage2', or None for all)
            
        Returns:
            Number of cache files removed
        """
        if not self.enabled or not self.cache_dir.exists():
            return 0
        
        count = 0
        
        patterns = []
        if stage is None:
            patterns = ['*.json']
        elif stage == 'stage1':
            patterns = ['stage1_*.json', 'file_*.json']
        elif stage == 'stage2':
            patterns = ['stage2_*.json']
        else:
            logger.warning(f"Unknown stage for cache clear: {stage}")
            return 0
        
        for pattern in patterns:
            for cache_file in self.cache_dir.glob(pattern):
                try:
                    cache_file.unlink()
                    count += 1
                    logger.debug(f"Removed cache file: {cache_file}")
                except Exception as e:
                    logger.warning(f"Failed to remove cache file {cache_file}: {e}")
        
        if count > 0:
            logger.info(f"Cleared {count} cache file(s)")
        
        return count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.enabled or not self.cache_dir.exists():
            return {
                'enabled': False,
                'total_files': 0,
                'total_size': 0
            }
        
        stats = {
            'enabled': True,
            'cache_dir': str(self.cache_dir),
            'ttl_hours': self.ttl.total_seconds() / 3600,
            'stage1_results': 0,
            'stage2_results': 0,
            'file_caches': 0,
            'total_size': 0
        }
        
        for cache_file in self.cache_dir.glob('*.json'):
            stats['total_size'] += cache_file.stat().st_size
            
            if cache_file.name.startswith('stage1_'):
                stats['stage1_results'] += 1
            elif cache_file.name.startswith('stage2_'):
                stats['stage2_results'] += 1
            elif cache_file.name.startswith('file_'):
                stats['file_caches'] += 1
        
        stats['total_files'] = (
            stats['stage1_results'] + 
            stats['stage2_results'] + 
            stats['file_caches']
        )
        
        # Convert size to human readable
        size_mb = stats['total_size'] / (1024 * 1024)
        stats['total_size_mb'] = round(size_mb, 2)
        
        return stats
