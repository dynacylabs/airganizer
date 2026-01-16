"""
Configuration management for Airganizer
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml


class Config:
    """Configuration manager for Airganizer"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration from YAML file
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config_data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def validate(self) -> bool:
        """
        Validate configuration
        
        Returns:
            True if configuration is valid
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Check source directory
        source_dir = self.get_source_directory()
        if not source_dir:
            raise ValueError("Source directory not specified in configuration")
        
        # Check destination directory
        dest_dir = self.get_destination_directory()
        if not dest_dir:
            raise ValueError("Destination directory not specified in configuration")
        
        return True
    
    def get_source_directory(self) -> Optional[str]:
        """Get source directory from configuration"""
        return self.config_data.get('source', {}).get('directory')
    
    def get_destination_directory(self) -> Optional[str]:
        """Get destination directory from configuration"""
        return self.config_data.get('destination', {}).get('directory')
    
    def get_cache_directory(self) -> str:
        """Get cache directory from configuration"""
        return self.config_data.get('cache', {}).get('directory', '.airganizer_cache')
    
    def get_include_patterns(self) -> List[str]:
        """Get file include patterns"""
        return self.config_data.get('source', {}).get('include', ['*'])
    
    def get_exclude_patterns(self) -> List[str]:
        """Get file exclude patterns"""
        return self.config_data.get('source', {}).get('exclude', [])
    
    def should_extract_exif(self) -> bool:
        """Check if EXIF data extraction is enabled"""
        return self.config_data.get('metadata', {}).get('extract_exif', True)
    
    def should_extract_audio_metadata(self) -> bool:
        """Check if audio metadata extraction is enabled"""
        return self.config_data.get('metadata', {}).get('extract_audio_metadata', True)
    
    def should_extract_video_metadata(self) -> bool:
        """Check if video metadata extraction is enabled"""
        return self.config_data.get('metadata', {}).get('extract_video_metadata', True)
    
    def should_extract_document_metadata(self) -> bool:
        """Check if document metadata extraction is enabled"""
        return self.config_data.get('metadata', {}).get('extract_document_metadata', True)
    
    def get_stage1_output_file(self) -> str:
        """Get Stage 1 output file path"""
        return self.config_data.get('stage1', {}).get('output_file', 'file_metadata.json')
    
    def should_calculate_hash(self) -> bool:
        """Check if file hash calculation is enabled"""
        return self.config_data.get('stage1', {}).get('calculate_hash', False)
    
    def get_max_file_size(self) -> int:
        """Get maximum file size to process (in bytes)"""
        max_size_mb = self.config_data.get('stage1', {}).get('max_file_size', 0)
        return max_size_mb * 1024 * 1024 if max_size_mb > 0 else 0
    
    def get_cache_interval(self) -> int:
        """Get cache interval (number of files between cache saves)"""
        return self.config_data.get('stage1', {}).get('cache_interval', 100)
    
    def should_resume_from_cache(self) -> bool:
        """Check if should resume from cache if available"""
        return self.config_data.get('stage1', {}).get('resume_from_cache', True)
