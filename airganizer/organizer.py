"""Main organizer module for generating directory structures."""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from airganizer.chunker import TreeChunker
from airganizer.ai_providers import AIProvider


class StructureOrganizer:
    """
    Orchestrates the process of generating an organized directory structure.
    
    This class:
    1. Chunks the file tree
    2. Iteratively feeds chunks to AI
    3. Builds up the theoretical structure
    """
    
    def __init__(
        self,
        ai_provider: AIProvider,
        chunk_size: int = 4000,
        debug: bool = False
    ):
        """
        Initialize the organizer.
        
        Args:
            ai_provider: The AI provider to use for structure generation
            chunk_size: Maximum size of each chunk in characters
            debug: Enable debug output
        """
        self.ai_provider = ai_provider
        self.chunker = TreeChunker(max_chunk_size=chunk_size)
        self.theoretical_structure = {'dirs': {}, 'files': []}
        self.debug = debug
    
    def organize(
        self,
        file_tree: Dict[str, Any],
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Generate an organized directory structure from file tree.
        
        Args:
            file_tree: The actual file tree structure
            progress_callback: Optional callback function(current, total, chunk_data)
            
        Returns:
            The theoretical directory structure
        """
        # Split into chunks
        if self.debug:
            print("[DEBUG] Starting chunking process...")
        
        chunks = self.chunker.chunk_tree(file_tree)
        total_chunks = len(chunks)
        
        if self.debug:
            print(f"[DEBUG] Created {total_chunks} chunks")
            for i, chunk in enumerate(chunks, 1):
                chunk_json = json.dumps(chunk)
                print(f"[DEBUG] Chunk {i} size: {len(chunk_json)} chars")
        
        print(f"Processing {total_chunks} chunks...")
        
        # Process each chunk
        for i, chunk in enumerate(chunks, 1):
            if progress_callback:
                progress_callback(i, total_chunks, chunk)
            else:
                print(f"\nProcessing chunk {i}/{total_chunks}...")
            
            if self.debug:
                chunk_json = json.dumps(chunk)
                print(f"[DEBUG] Chunk {i} content preview:")
                print(f"[DEBUG]   Files in chunk: {len(chunk.get('files', []))}")
                print(f"[DEBUG]   Dirs in chunk: {len(chunk.get('dirs', {}))}")
                print(f"[DEBUG] Sending to AI provider...")
            
            # Feed to AI
            try:
                self.theoretical_structure = self.ai_provider.generate_structure(
                    file_chunk=chunk,
                    current_structure=self.theoretical_structure,
                    debug=self.debug
                )
                
                if self.debug:
                    print(f"[DEBUG] Received response from AI")
                    print(f"[DEBUG] Current structure has {len(self.theoretical_structure.get('dirs', {}))} top-level categories")
                
                if not progress_callback:
                    print(f"  ✓ Structure updated")
                    
            except Exception as e:
                print(f"  ✗ Error processing chunk {i}: {e}")
                if self.debug:
                    import traceback
                    print(f"[DEBUG] Full error traceback:")
                    traceback.print_exc()
                continue
        
        return self.theoretical_structure
    
    def save_structure(self, output_path: str):
        """
        Save the theoretical structure to a JSON file.
        
        Args:
            output_path: Path to save the structure
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.theoretical_structure, f, indent=2)
        
        print(f"\nStructure saved to: {output_path}")
    
    def load_structure(self, input_path: str):
        """
        Load a theoretical structure from a JSON file.
        
        Args:
            input_path: Path to load the structure from
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            self.theoretical_structure = json.load(f)
        
        print(f"Structure loaded from: {input_path}")
    
    def get_structure_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the theoretical structure.
        
        Returns:
            Dictionary with summary statistics
        """
        def count_dirs(structure: Dict[str, Any]) -> int:
            """Recursively count directories."""
            count = len(structure.get('dirs', {}))
            for subdir in structure.get('dirs', {}).values():
                count += count_dirs(subdir)
            return count
        
        def get_depth(structure: Dict[str, Any], current_depth: int = 0) -> int:
            """Get maximum depth of directory tree."""
            if not structure.get('dirs'):
                return current_depth
            
            max_depth = current_depth
            for subdir in structure.get('dirs', {}).values():
                depth = get_depth(subdir, current_depth + 1)
                max_depth = max(max_depth, depth)
            
            return max_depth
        
        def list_categories(structure: Dict[str, Any], prefix: str = "") -> list:
            """List all category paths."""
            categories = []
            for dir_name, subdir in structure.get('dirs', {}).items():
                path = f"{prefix}/{dir_name}" if prefix else dir_name
                categories.append(path)
                categories.extend(list_categories(subdir, path))
            return categories
        
        return {
            'total_directories': count_dirs(self.theoretical_structure),
            'max_depth': get_depth(self.theoretical_structure),
            'categories': list_categories(self.theoretical_structure)
        }
    
    def print_structure(self, max_depth: Optional[int] = None):
        """
        Pretty print the theoretical structure.
        
        Args:
            max_depth: Maximum depth to print (None for all)
        """
        def print_tree(structure: Dict[str, Any], indent: int = 0, depth: int = 0):
            """Recursively print tree structure."""
            if max_depth is not None and depth >= max_depth:
                return
            
            dirs = structure.get('dirs', {})
            for dir_name in sorted(dirs.keys()):
                print("  " * indent + f"📁 {dir_name}/")
                print_tree(dirs[dir_name], indent + 1, depth + 1)
        
        print("\nTheoretical Directory Structure:")
        print("=" * 60)
        print_tree(self.theoretical_structure)
        print("=" * 60)
        
        summary = self.get_structure_summary()
        print(f"\nTotal categories: {summary['total_directories']}")
        print(f"Maximum depth: {summary['max_depth']}")
