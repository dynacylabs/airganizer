"""Core file scanner module for recursive directory enumeration."""

import os
from pathlib import Path
from typing import List, Generator


class FileScanner:
    """Scans directories recursively and enumerates all files."""
    
    def __init__(self, root_path: str):
        """
        Initialize the FileScanner.
        
        Args:
            root_path: The root directory to scan
        """
        self.root_path = Path(root_path).resolve()
        
        if not self.root_path.exists():
            raise ValueError(f"Path does not exist: {root_path}")
        
        if not self.root_path.is_dir():
            raise ValueError(f"Path is not a directory: {root_path}")
    
    def scan(self) -> Generator[Path, None, None]:
        """
        Recursively scan the directory and yield all file paths.
        
        Yields:
            Path objects for each file found
        """
        for root, dirs, files in os.walk(self.root_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                # Skip hidden files
                if not file.startswith('.'):
                    file_path = Path(root) / file
                    yield file_path
    
    def get_all_files(self) -> List[Path]:
        """
        Get a list of all files in the directory.
        
        Returns:
            List of Path objects for all files
        """
        return list(self.scan())
    
    def count_files(self) -> int:
        """
        Count total number of files in the directory.
        
        Returns:
            Total file count
        """
        return sum(1 for _ in self.scan())
