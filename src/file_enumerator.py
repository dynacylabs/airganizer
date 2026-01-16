"""
File enumeration module for Airganizer Stage 1
"""

import os
from pathlib import Path
from typing import List, Iterator
import fnmatch


class FileEnumerator:
    """Enumerate files in a directory recursively"""
    
    def __init__(self, source_directory: str, include_patterns: List[str] = None, 
                 exclude_patterns: List[str] = None):
        """
        Initialize file enumerator
        
        Args:
            source_directory: Root directory to scan
            include_patterns: List of glob patterns to include
            exclude_patterns: List of glob patterns to exclude
        """
        self.source_directory = Path(source_directory)
        self.include_patterns = include_patterns or ['*']
        self.exclude_patterns = exclude_patterns or []
        
        if not self.source_directory.exists():
            raise FileNotFoundError(f"Source directory not found: {source_directory}")
        
        if not self.source_directory.is_dir():
            raise NotADirectoryError(f"Source path is not a directory: {source_directory}")
    
    def _matches_pattern(self, file_path: Path, patterns: List[str]) -> bool:
        """
        Check if file matches any of the patterns
        
        Args:
            file_path: Path to check
            patterns: List of glob patterns
        
        Returns:
            True if file matches any pattern
        """
        file_name = file_path.name
        file_rel_path = str(file_path.relative_to(self.source_directory))
        
        for pattern in patterns:
            if fnmatch.fnmatch(file_name, pattern) or fnmatch.fnmatch(file_rel_path, pattern):
                return True
        
        return False
    
    def _should_include_file(self, file_path: Path) -> bool:
        """
        Determine if a file should be included based on include/exclude patterns
        
        Args:
            file_path: Path to check
        
        Returns:
            True if file should be included
        """
        # Check exclude patterns first
        if self.exclude_patterns and self._matches_pattern(file_path, self.exclude_patterns):
            return False
        
        # Check include patterns
        if self.include_patterns:
            return self._matches_pattern(file_path, self.include_patterns)
        
        return True
    
    def _should_skip_directory(self, dir_path: Path) -> bool:
        """
        Determine if a directory should be skipped based on exclude patterns
        
        Args:
            dir_path: Directory path to check
        
        Returns:
            True if directory should be skipped
        """
        if not self.exclude_patterns:
            return False
        
        dir_name = dir_path.name
        dir_rel_path = str(dir_path.relative_to(self.source_directory))
        
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(dir_name, pattern) or fnmatch.fnmatch(dir_rel_path, pattern):
                return True
        
        return False
    
    def enumerate_files(self) -> Iterator[Path]:
        """
        Enumerate all files in the source directory recursively
        
        Yields:
            Path objects for each file that matches the criteria
        """
        for root, dirs, files in os.walk(self.source_directory):
            root_path = Path(root)
            
            # Filter out excluded directories (modifying dirs in-place affects os.walk)
            dirs[:] = [d for d in dirs if not self._should_skip_directory(root_path / d)]
            
            for file_name in files:
                file_path = root_path / file_name
                
                if self._should_include_file(file_path):
                    yield file_path
    
    def count_files(self) -> int:
        """
        Count the total number of files that will be enumerated
        
        Returns:
            Total file count
        """
        return sum(1 for _ in self.enumerate_files())
    
    def get_files_list(self) -> List[Path]:
        """
        Get a list of all files
        
        Returns:
            List of Path objects
        """
        return list(self.enumerate_files())
