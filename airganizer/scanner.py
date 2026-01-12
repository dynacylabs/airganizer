"""File scanner module for recursively scanning directories."""

import os
from pathlib import Path
from typing import List


class FileScanner:
    """Scans directories recursively to find all files."""
    
    def __init__(self, root_path: str):
        """
        Initialize the file scanner.
        
        Args:
            root_path: Root directory to scan
        """
        self.root_path = Path(root_path).resolve()
        
        if not self.root_path.exists():
            raise ValueError(f"Path does not exist: {root_path}")
        
        if not self.root_path.is_dir():
            raise ValueError(f"Path is not a directory: {root_path}")
    
    def scan(self) -> List[Path]:
        """
        Recursively scan the directory for all files.
        
        Returns:
            List of Path objects for all files found
        """
        files = []
        
        for root, dirs, filenames in os.walk(self.root_path):
            root_path = Path(root)
            
            for filename in filenames:
                file_path = root_path / filename
                files.append(file_path)
        
        return files
    
    def get_file_info(self, file_path: Path) -> dict:
        """
        Get information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        stat = file_path.stat()
        
        return {
            'path': file_path,
            'name': file_path.name,
            'extension': file_path.suffix,
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'relative_path': file_path.relative_to(self.root_path)
        }
    
    def build_tree(self) -> dict:
        """
        Build a hierarchical tree structure of the directory.
        
        Returns:
            Dictionary representing the directory tree with 'dirs' and 'files' keys
        """
        def build_subtree(path: Path) -> dict:
            tree = {
                'dirs': {},
                'files': []
            }
            
            try:
                for item in sorted(path.iterdir()):
                    if item.is_file():
                        tree['files'].append(item.name)
                    elif item.is_dir():
                        tree['dirs'][item.name] = build_subtree(item)
            except PermissionError:
                # Skip directories we can't access
                pass
            
            return tree
        
        return build_subtree(self.root_path)


