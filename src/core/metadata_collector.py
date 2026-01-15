"""Metadata collection module for file analysis."""

import os
import subprocess
import magic
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
import json


@dataclass
class FileMetadata:
    """Data class to store file metadata."""
    file_path: str
    file_name: str
    mime_type: str
    mime_encoding: str
    file_size: int
    binwalk_output: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class MetadataCollector:
    """Collects comprehensive metadata for files."""
    
    def __init__(self, use_binwalk: bool = True):
        """
        Initialize the MetadataCollector.
        
        Args:
            use_binwalk: Whether to run binwalk analysis (can be slow)
        """
        self.use_binwalk = use_binwalk
        self.mime = magic.Magic(mime=True)
        self.mime_encoding = magic.Magic(mime_encoding=True)
        
        # Check if binwalk is available
        if use_binwalk:
            self.binwalk_available = self._check_binwalk()
        else:
            self.binwalk_available = False
    
    def _check_binwalk(self) -> bool:
        """Check if binwalk is installed and available."""
        try:
            result = subprocess.run(
                ['binwalk', '--help'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _get_mime_type(self, file_path: Path) -> tuple[str, str]:
        """
        Get MIME type and encoding for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (mime_type, mime_encoding)
        """
        try:
            mime_type = self.mime.from_file(str(file_path))
            mime_encoding = self.mime_encoding.from_file(str(file_path))
            return mime_type, mime_encoding
        except Exception as e:
            return f"error: {str(e)}", "unknown"
    
    def _run_binwalk(self, file_path: Path) -> Optional[str]:
        """
        Run binwalk analysis on a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Binwalk output as string or None if not available/error
        """
        if not self.binwalk_available:
            return None
        
        try:
            result = subprocess.run(
                ['binwalk', str(file_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"binwalk error (code {result.returncode}): {result.stderr.strip()}"
        except subprocess.TimeoutExpired:
            return "binwalk timeout (>30s)"
        except Exception as e:
            return f"binwalk error: {str(e)}"
    
    def collect_metadata(self, file_path: Path) -> FileMetadata:
        """
        Collect all metadata for a single file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            FileMetadata object with all collected information
        """
        try:
            # Basic file information
            file_name = file_path.name
            file_size = file_path.stat().st_size
            
            # MIME type detection
            mime_type, mime_encoding = self._get_mime_type(file_path)
            
            # Binwalk analysis
            binwalk_output = None
            if self.use_binwalk:
                binwalk_output = self._run_binwalk(file_path)
            
            return FileMetadata(
                file_path=str(file_path),
                file_name=file_name,
                mime_type=mime_type,
                mime_encoding=mime_encoding,
                file_size=file_size,
                binwalk_output=binwalk_output
            )
        except Exception as e:
            return FileMetadata(
                file_path=str(file_path),
                file_name=file_path.name if file_path else "unknown",
                mime_type="error",
                mime_encoding="error",
                file_size=0,
                error=str(e)
            )
