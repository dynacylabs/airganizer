"""Core module initialization."""

from .scanner import FileScanner
from .metadata_collector import MetadataCollector, FileMetadata
from .storage import MetadataStore
from .models import DirectoryNode, ProposedStructure, FileItem

__all__ = [
    'FileScanner', 'MetadataCollector', 'FileMetadata', 'MetadataStore',
    'DirectoryNode', 'ProposedStructure', 'FileItem'
]
