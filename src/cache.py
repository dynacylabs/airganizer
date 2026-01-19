"""Cache management for resumable operations."""

import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from .models import (
    FileInfo, Stage1Result, Stage2Result, ModelInfo,
    FileAnalysis, Stage3Result, TaxonomyNode, FileAssignment, Stage4Result
)
from .stage5 import Stage5Result


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
        
        # Cache is always valid if it exists
        # Check source file modification time if provided
        if source_file and source_file.exists():
            cache_mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
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
            stage: Optional stage to clear ('stage1', 'stage2', 'stage3', 'stage4', 'stage5', or None for all)
            
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
        elif stage == 'stage3':
            patterns = ['stage3_*.json']
        elif stage == 'stage4':
            patterns = ['stage4_*.json']
        elif stage == 'stage5':
            patterns = ['stage5_*.json']
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
            elif cache_file.name.startswith('stage3_file_'):
                stats['file_caches'] += 1
            elif cache_file.name.startswith('stage3_'):
                stats.setdefault('stage3_results', 0)
                stats['stage3_results'] += 1
            elif cache_file.name.startswith('stage4_'):
                stats.setdefault('stage4_results', 0)
                stats['stage4_results'] += 1
            elif cache_file.name.startswith('stage5_'):
                stats.setdefault('stage5_results', 0)
                stats['stage5_results'] += 1
            elif cache_file.name.startswith('file_'):
                stats['file_caches'] += 1
        
        stats['total_files'] = (
            stats['stage1_results'] + 
            stats['stage2_results'] + 
            stats.get('stage3_results', 0) +
            stats.get('stage4_results', 0) +
            stats.get('stage5_results', 0) +
            stats['file_caches']
        )
        
        # Convert size to human readable
        size_mb = stats['total_size'] / (1024 * 1024)
        stats['total_size_mb'] = round(size_mb, 2)
        
        return stats
    
    # ========== Stage 3 Caching ==========
    
    def get_stage3_file_cache(self, file_path: str) -> Optional[FileAnalysis]:
        """
        Get cached FileAnalysis for a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            FileAnalysis if cached and valid, None otherwise
        """
        if not self.enabled:
            return None
        
        file_hash = self._get_file_hash(file_path)
        cache_path = self.cache_dir / f"stage3_file_{file_hash}.json"
        
        source_path = Path(file_path)
        if not self._is_cache_valid(cache_path, source_path):
            return None
        
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
            
            analysis = FileAnalysis(
                file_path=data['file_path'],
                assigned_model=data['assigned_model'],
                proposed_filename=data['proposed_filename'],
                description=data['description'],
                tags=data['tags'],
                analysis_timestamp=data.get('analysis_timestamp'),
                error=data.get('error')
            )
            
            logger.debug(f"Cache hit for Stage 3 file analysis: {file_path}")
            return analysis
        
        except Exception as e:
            logger.warning(f"Failed to load Stage 3 file cache for {file_path}: {e}")
            return None
    
    def save_stage3_file_cache(self, analysis: FileAnalysis) -> None:
        """
        Save FileAnalysis to cache.
        
        Args:
            analysis: FileAnalysis object to cache
        """
        if not self.enabled:
            return
        
        file_hash = self._get_file_hash(analysis.file_path)
        cache_path = self.cache_dir / f"stage3_file_{file_hash}.json"
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(analysis.to_dict(), f, indent=2)
            
            logger.debug(f"Cached Stage 3 analysis: {analysis.file_path}")
        
        except Exception as e:
            logger.warning(f"Failed to save Stage 3 file cache for {analysis.file_path}: {e}")
    
    def get_stage3_result_cache(self, source_directory: str) -> Optional[Stage3Result]:
        """
        Get cached Stage3Result for a directory.
        
        Args:
            source_directory: Source directory path
            
        Returns:
            Stage3Result if cached and valid, None otherwise
        """
        if not self.enabled:
            return None
        
        dir_hash = self._get_directory_hash(source_directory)
        cache_path = self.cache_dir / f"stage3_{dir_hash}.json"
        
        if not self._is_cache_valid(cache_path):
            return None
        
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
            
            # Load Stage2Result first (will be loaded from cache)
            stage2_result = self.get_stage2_result_cache(source_directory)
            if not stage2_result:
                logger.warning("Stage 2 result not in cache, cannot load Stage 3")
                return None
            
            # Load file analyses
            file_analyses = []
            for a_data in data.get('file_analyses', []):
                analysis = FileAnalysis(
                    file_path=a_data['file_path'],
                    assigned_model=a_data['assigned_model'],
                    proposed_filename=a_data['proposed_filename'],
                    description=a_data['description'],
                    tags=a_data['tags'],
                    analysis_timestamp=a_data.get('analysis_timestamp'),
                    error=a_data.get('error')
                )
                file_analyses.append(analysis)
            
            result = Stage3Result(
                stage2_result=stage2_result,
                file_analyses=file_analyses,
                total_analyzed=data.get('total_analyzed', 0),
                total_errors=data.get('total_errors', 0)
            )
            
            logger.info(f"Loaded Stage 3 result from cache: {len(result.file_analyses)} analyses")
            return result
        
        except Exception as e:
            logger.warning(f"Failed to load Stage 3 cache: {e}")
            return None
    
    def save_stage3_result_cache(self, result: Stage3Result) -> None:
        """
        Save Stage3Result to cache.
        
        Args:
            result: Stage3Result to cache
        """
        if not self.enabled:
            return
        
        dir_hash = self._get_directory_hash(result.stage2_result.stage1_result.source_directory)
        cache_path = self.cache_dir / f"stage3_{dir_hash}.json"
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
            
            logger.info(f"Saved Stage 3 result to cache: {len(result.file_analyses)} analyses")
        
        except Exception as e:
            logger.warning(f"Failed to save Stage 3 cache: {e}")
    
    # ========== Stage 4 Caching ==========
    
    def get_stage4_result_cache(self, source_directory: str) -> Optional[Stage4Result]:
        """
        Get cached Stage4Result for a directory.
        
        Args:
            source_directory: Source directory path
            
        Returns:
            Stage4Result if cached and valid, None otherwise
        """
        if not self.enabled:
            return None
        
        dir_hash = self._get_directory_hash(source_directory)
        cache_path = self.cache_dir / f"stage4_{dir_hash}.json"
        
        if not self._is_cache_valid(cache_path):
            return None
        
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
            
            # Load Stage3Result first
            stage3_result = self.get_stage3_result_cache(source_directory)
            if not stage3_result:
                logger.warning("Stage 3 result not in cache, cannot load Stage 4")
                return None
            
            # Load taxonomy nodes
            taxonomy = []
            for t_data in data.get('taxonomy', []):
                node = TaxonomyNode(
                    name=t_data['name'],
                    path=t_data['path'],
                    description=t_data['description'],
                    parent_path=t_data.get('parent_path'),
                    level=t_data.get('level', 0)
                )
                taxonomy.append(node)
            
            # Load file assignments
            file_assignments = []
            for a_data in data.get('file_assignments', []):
                assignment = FileAssignment(
                    file_path=a_data['file_path'],
                    taxonomy_path=a_data['taxonomy_path'],
                    reason=a_data['reason']
                )
                file_assignments.append(assignment)
            
            result = Stage4Result(
                stage3_result=stage3_result,
                taxonomy=taxonomy,
                file_assignments=file_assignments,
                total_categories=data.get('total_categories', 0),
                total_assigned=data.get('total_assigned', 0)
            )
            
            logger.info(f"Loaded Stage 4 result from cache: {len(result.taxonomy)} categories")
            return result
        
        except Exception as e:
            logger.warning(f"Failed to load Stage 4 cache: {e}")
            return None
    
    def save_stage4_result_cache(self, result: Stage4Result) -> None:
        """
        Save Stage4Result to cache.
        
        Args:
            result: Stage4Result to cache
        """
        if not self.enabled:
            return
        
        dir_hash = self._get_directory_hash(
            result.stage3_result.stage2_result.stage1_result.source_directory
        )
        cache_path = self.cache_dir / f"stage4_{dir_hash}.json"
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
            
            logger.info(f"Saved Stage 4 result to cache: {len(result.taxonomy)} categories")
        
        except Exception as e:
            logger.warning(f"Failed to save Stage 4 cache: {e}")
    
    # ========== Stage 5 Caching ==========
    
    def get_stage5_result_cache(self, source_directory: str) -> Optional[Stage5Result]:
        """
        Get cached Stage5Result for a directory.
        
        Args:
            source_directory: Source directory path
            
        Returns:
            Stage5Result if cached and valid, None otherwise
        """
        if not self.enabled:
            return None
        
        dir_hash = self._get_directory_hash(source_directory)
        cache_path = self.cache_dir / f"stage5_{dir_hash}.json"
        
        if not self._is_cache_valid(cache_path):
            return None
        
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
            
            # Load Stage4Result first
            stage4_result = self.get_stage4_result_cache(source_directory)
            if not stage4_result:
                logger.warning("Stage 4 result not in cache, cannot load Stage 5")
                return None
            
            # Import MoveOperation here to avoid circular dependency
            from .stage5 import MoveOperation
            
            # Load move operations
            operations = []
            for op_data in data.get('operations', []):
                operation = MoveOperation(
                    source_path=op_data['source_path'],
                    destination_path=op_data['destination_path'],
                    category=op_data['category'],
                    reason=op_data.get('reason'),
                    success=op_data.get('success', False),
                    error=op_data.get('error')
                )
                operations.append(operation)
            
            result = Stage5Result(
                stage4_result=stage4_result,
                destination_root=data['destination_root'],
                operations=operations,
                total_files=data.get('total_files', 0),
                successful_moves=data.get('successful_moves', 0),
                failed_moves=data.get('failed_moves', 0),
                skipped_moves=data.get('skipped_moves', 0),
                excluded_moves=data.get('excluded_moves', 0),
                error_moves=data.get('error_moves', 0),
                dry_run=data.get('dry_run', False)
            )
            
            logger.info(f"Loaded Stage 5 result from cache: {len(result.operations)} operations")
            return result
        
        except Exception as e:
            logger.warning(f"Failed to load Stage 5 cache: {e}")
            return None
    
    def save_stage5_result_cache(self, result: Stage5Result) -> None:
        """
        Save Stage5Result to cache.
        
        Args:
            result: Stage5Result to cache
        """
        if not self.enabled:
            return
        
        dir_hash = self._get_directory_hash(
            result.stage4_result.stage3_result.stage2_result.stage1_result.source_directory
        )
        cache_path = self.cache_dir / f"stage5_{dir_hash}.json"
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
            
            logger.info(f"Saved Stage 5 result to cache: {len(result.operations)} operations")
        
        except Exception as e:
            logger.warning(f"Failed to save Stage 5 cache: {e}")

