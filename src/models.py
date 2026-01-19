"""Data models for the AI File Organizer."""

from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class FileInfo:
    """Information about a single file with metadata."""
    
    file_name: str
    file_path: str
    mime_type: str
    file_size: int
    exif_data: Dict[str, Any] = field(default_factory=dict)
    binwalk_output: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert FileInfo to dictionary."""
        return asdict(self)


@dataclass
class ModelInfo:
    """Information about an available AI model."""
    
    name: str
    type: str
    provider: str
    model_name: str
    capabilities: List[str]
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ModelInfo to dictionary."""
        return asdict(self)


@dataclass
class Stage1Result:
    """Results from Stage 1: File enumeration and metadata collection."""
    
    source_directory: str
    total_files: int
    files: List[FileInfo]
    errors: List[Dict[str, str]]
    unique_mime_types: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Stage1Result to dictionary."""
        return {
            'source_directory': self.source_directory,
            'total_files': self.total_files,
            'files': [f.to_dict() for f in self.files],
            'errors': self.errors,
            'unique_mime_types': self.unique_mime_types
        }
    
    def add_file(self, file_info: FileInfo) -> None:
        """Add a file to the results."""
        self.files.append(file_info)
        self.total_files = len(self.files)
    
    def add_error(self, file_path: str, error_message: str) -> None:
        """Add an error to the results."""
        self.errors.append({
            'file_path': file_path,
            'error': error_message
        })
    
    def extract_unique_mime_types(self) -> None:
        """Extract unique MIME types from all files."""
        mime_types = set()
        for file_info in self.files:
            mime_types.add(file_info.mime_type)
        self.unique_mime_types = sorted(list(mime_types))


@dataclass
class Stage2Result:
    """Results from Stage 2: AI model discovery and mapping."""
    
    stage1_result: Stage1Result
    available_models: List[ModelInfo] = field(default_factory=list)
    mime_to_model_mapping: Dict[str, str] = field(default_factory=dict)
    model_connectivity: Dict[str, bool] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Stage2Result to dictionary."""
        return {
            'stage1_result': self.stage1_result.to_dict(),
            'available_models': [m.to_dict() for m in self.available_models],
            'mime_to_model_mapping': self.mime_to_model_mapping,
            'model_connectivity': self.model_connectivity
        }
    
    def set_models(self, models: List[Any]) -> None:
        """
        Set available models.
        
        Args:
            models: List of AIModel objects
        """
        self.available_models = [
            ModelInfo(
                name=m.name,
                type=m.type,
                provider=m.provider,
                model_name=m.model_name,
                capabilities=m.capabilities,
                description=m.description
            )
            for m in models
        ]
    
    def set_mime_mapping(self, mapping: Dict[str, str]) -> None:
        """
        Set the MIME type to model mapping.
        
        Args:
            mapping: Dictionary mapping MIME type to model name
        """
        self.mime_to_model_mapping = mapping
    
    def set_model_connectivity(self, connectivity: Dict[str, bool]) -> None:
        """
        Set the model connectivity status.
        
        Args:
            connectivity: Dictionary mapping model name to connectivity status
        """
        self.model_connectivity = connectivity
    
    def get_model_for_file(self, file_info: FileInfo) -> Optional[str]:
        """
        Get the recommended model for a file based on its MIME type.
        
        Args:
            file_info: FileInfo object
            
        Returns:
            Model name or None if no mapping exists
        """
        return self.mime_to_model_mapping.get(file_info.mime_type)
