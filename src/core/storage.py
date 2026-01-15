"""Data storage module for persisting file metadata."""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from .metadata_collector import FileMetadata


class MetadataStore:
    """Handles storage and retrieval of file metadata."""
    
    def __init__(self, storage_path: str = "data/metadata.json"):
        """
        Initialize the MetadataStore.
        
        Args:
            storage_path: Path to store the metadata JSON file
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata: List[Dict[str, Any]] = []
    
    def add_metadata(self, metadata: FileMetadata) -> None:
        """
        Add a file metadata entry to the store.
        
        Args:
            metadata: FileMetadata object to add
        """
        self.metadata.append(metadata.to_dict())
    
    def add_batch(self, metadata_list: List[FileMetadata]) -> None:
        """
        Add multiple metadata entries at once.
        
        Args:
            metadata_list: List of FileMetadata objects
        """
        for metadata in metadata_list:
            self.add_metadata(metadata)
    
    def save(self) -> None:
        """Save the metadata to a JSON file."""
        output = {
            "scan_date": datetime.now().isoformat(),
            "total_files": len(self.metadata),
            "files": self.metadata
        }
        
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
    
    def load(self) -> Dict[str, Any]:
        """
        Load metadata from the JSON file.
        
        Returns:
            Dictionary containing the loaded metadata
        """
        if not self.storage_path.exists():
            return {"files": []}
        
        with open(self.storage_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def clear(self) -> None:
        """Clear all metadata from memory."""
        self.metadata = []
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the collected metadata.
        
        Returns:
            Dictionary with summary statistics
        """
        if not self.metadata:
            return {
                "total_files": 0,
                "total_size": 0,
                "mime_types": {}
            }
        
        total_size = sum(item.get('file_size', 0) for item in self.metadata)
        mime_types: Dict[str, int] = {}
        
        for item in self.metadata:
            mime = item.get('mime_type', 'unknown')
            mime_types[mime] = mime_types.get(mime, 0) + 1
        
        return {
            "total_files": len(self.metadata),
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "mime_types": mime_types
        }
