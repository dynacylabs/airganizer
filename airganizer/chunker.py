"""Module for chunking file tree data into manageable pieces for AI processing."""

import json
from typing import List, Dict, Any


class TreeChunker:
    """Splits a file tree into size-based chunks for processing."""
    
    def __init__(self, max_chunk_size: int = 4000):
        """
        Initialize the chunker.
        
        Args:
            max_chunk_size: Maximum size of each chunk in characters
        """
        self.max_chunk_size = max_chunk_size
    
    def chunk_tree(self, tree: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split a file tree into chunks based on size.
        
        Args:
            tree: The file tree structure with 'dirs' and 'files' keys
            
        Returns:
            List of tree chunks, each a valid tree structure
        """
        chunks = []
        
        # If the entire tree fits in one chunk, return it
        tree_json = json.dumps(tree)
        if len(tree_json) <= self.max_chunk_size:
            return [tree]
        
        # Otherwise, split by top-level directories
        root_files = tree.get('files', [])
        root_dirs = tree.get('dirs', {})
        
        # Start with root files as first chunk if they exist
        if root_files:
            root_chunk = {'dirs': {}, 'files': root_files}
            root_json = json.dumps(root_chunk)
            
            if len(root_json) <= self.max_chunk_size:
                chunks.append(root_chunk)
            else:
                # If root files alone exceed chunk size, split them
                file_chunks = self._chunk_files(root_files)
                for file_chunk in file_chunks:
                    chunks.append({'dirs': {}, 'files': file_chunk})
        
        # Process each top-level directory
        for dir_name, dir_tree in root_dirs.items():
            dir_chunk = {'dirs': {dir_name: dir_tree}, 'files': []}
            dir_json = json.dumps(dir_chunk)
            
            if len(dir_json) <= self.max_chunk_size:
                chunks.append(dir_chunk)
            else:
                # Recursively chunk this directory
                sub_chunks = self._chunk_directory(dir_name, dir_tree)
                chunks.extend(sub_chunks)
        
        return chunks
    
    def _chunk_files(self, files: List[str]) -> List[List[str]]:
        """
        Split a list of files into chunks.
        
        Args:
            files: List of file names
            
        Returns:
            List of file name chunks
        """
        chunks = []
        current_chunk = []
        current_size = 2  # Start with '{}'
        
        for file in files:
            # Estimate size: file name + quotes + comma
            file_size = len(json.dumps(file)) + 1
            
            if current_size + file_size > self.max_chunk_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_size = 2
            
            current_chunk.append(file)
            current_size += file_size
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _chunk_directory(self, dir_name: str, dir_tree: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Recursively chunk a directory tree.
        
        Args:
            dir_name: Name of the directory
            dir_tree: The directory tree structure
            
        Returns:
            List of chunks containing parts of this directory
        """
        chunks = []
        
        files = dir_tree.get('files', [])
        subdirs = dir_tree.get('dirs', {})
        
        # Try to fit files in chunks
        if files:
            file_chunks = self._chunk_files(files)
            for file_chunk in file_chunks:
                chunk = {
                    'dirs': {dir_name: {'dirs': {}, 'files': file_chunk}},
                    'files': []
                }
                chunks.append(chunk)
        
        # Process subdirectories
        for subdir_name, subdir_tree in subdirs.items():
            full_path = f"{dir_name}/{subdir_name}"
            subdir_chunk = {
                'dirs': {dir_name: {'dirs': {subdir_name: subdir_tree}, 'files': []}},
                'files': []
            }
            subdir_json = json.dumps(subdir_chunk)
            
            if len(subdir_json) <= self.max_chunk_size:
                chunks.append(subdir_chunk)
            else:
                # Further chunk this subdirectory
                # For deeply nested dirs, we flatten the representation
                nested_chunks = self._chunk_directory(subdir_name, subdir_tree)
                for nested_chunk in nested_chunks:
                    # Wrap in parent directory context
                    wrapped = {
                        'dirs': {dir_name: nested_chunk},
                        'files': []
                    }
                    chunks.append(wrapped)
        
        return chunks
    
    def estimate_chunk_count(self, tree: Dict[str, Any]) -> int:
        """
        Estimate how many chunks the tree will be split into.
        
        Args:
            tree: The file tree structure
            
        Returns:
            Estimated number of chunks
        """
        chunks = self.chunk_tree(tree)
        return len(chunks)
