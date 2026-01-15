"""Data models for AI-proposed organizational structures."""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
import json
from datetime import datetime


@dataclass
class DirectoryNode:
    """Represents a directory in the proposed structure."""
    name: str
    description: str
    path: str = ""
    subdirectories: List['DirectoryNode'] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    rationale: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "path": self.path,
            "subdirectories": [sub.to_dict() for sub in self.subdirectories],
            "files": self.files,
            "rationale": self.rationale
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DirectoryNode':
        """Create from dictionary representation."""
        subdirs = [cls.from_dict(sub) for sub in data.get('subdirectories', [])]
        return cls(
            name=data['name'],
            description=data['description'],
            path=data.get('path', ''),
            subdirectories=subdirs,
            files=data.get('files', []),
            rationale=data.get('rationale')
        )
    
    def add_file(self, file_path: str) -> None:
        """Add a file to this directory."""
        if file_path not in self.files:
            self.files.append(file_path)
    
    def add_subdirectory(self, subdir: 'DirectoryNode') -> None:
        """Add a subdirectory to this directory."""
        self.subdirectories.append(subdir)
    
    def find_directory(self, path: str) -> Optional['DirectoryNode']:
        """Find a directory by path."""
        if self.path == path or self.name == path:
            return self
        for subdir in self.subdirectories:
            found = subdir.find_directory(path)
            if found:
                return found
        return None


@dataclass
class ProposedStructure:
    """Represents the complete proposed organizational structure."""
    root: DirectoryNode
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_stats: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "root": self.root.to_dict(),
            "metadata": self.metadata,
            "processing_stats": self.processing_stats,
            "created_at": self.created_at,
            "last_updated": self.last_updated
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProposedStructure':
        """Create from dictionary representation."""
        root = DirectoryNode.from_dict(data['root'])
        return cls(
            root=root,
            metadata=data.get('metadata', {}),
            processing_stats=data.get('processing_stats', {}),
            created_at=data.get('created_at', datetime.now().isoformat()),
            last_updated=data.get('last_updated', datetime.now().isoformat())
        )
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ProposedStructure':
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def update_timestamp(self) -> None:
        """Update the last_updated timestamp."""
        self.last_updated = datetime.now().isoformat()
    
    def get_all_files(self) -> List[str]:
        """Get all files in the proposed structure."""
        files = []
        
        def collect_files(node: DirectoryNode):
            files.extend(node.files)
            for subdir in node.subdirectories:
                collect_files(subdir)
        
        collect_files(self.root)
        return files
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the proposed structure."""
        total_files = len(self.get_all_files())
        
        def count_directories(node: DirectoryNode) -> int:
            count = 1  # Count this directory
            for subdir in node.subdirectories:
                count += count_directories(subdir)
            return count
        
        total_dirs = count_directories(self.root)
        
        return {
            "total_directories": total_dirs,
            "total_files_placed": total_files,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "processing_stats": self.processing_stats
        }


@dataclass
class FileItem:
    """Represents a file to be organized."""
    file_path: str
    file_name: str
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "file_path": self.file_path,
            "file_name": self.file_name,
            "mime_type": self.mime_type,
            "file_size": self.file_size
        }
    
    def to_simple_string(self) -> str:
        """Convert to simple string for AI prompt."""
        parts = [self.file_path]
        if self.mime_type:
            parts.append(f"[{self.mime_type}]")
        return " ".join(parts)
