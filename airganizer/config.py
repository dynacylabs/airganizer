"""Configuration management for Airganizer."""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any


class Config:
    """Manages configuration for Airganizer."""
    
    DEFAULT_CONFIG = {
        'ai_provider': 'ollama',  # 'openai', 'anthropic', or 'ollama'
        'chunk_size': 4000,
        'openai': {
            'api_key': '',
            'model': 'gpt-4'
        },
        'anthropic': {
            'api_key': '',
            'model': 'claude-3-5-sonnet-20241022'
        },
        'ollama': {
            'model': 'llama2',
            'base_url': 'http://localhost:11434'
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to config file. If None, uses default location.
        """
        if config_path is None:
            config_path = self._get_default_config_path()
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default config file path."""
        # Look in current directory first, then home directory
        local_config = Path('.airganizer.json')
        if local_config.exists():
            return str(local_config)
        
        home_config = Path.home() / '.airganizer.json'
        return str(home_config)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                # Merge with defaults to handle missing keys
                config = self.DEFAULT_CONFIG.copy()
                config.update(loaded)
                return config
        
        return self.DEFAULT_CONFIG.copy()
    
    def save(self):
        """Save current configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key (can use dot notation, e.g., 'openai.api_key')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set a configuration value.
        
        Args:
            key: Configuration key (can use dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_ai_provider_config(self) -> Dict[str, Any]:
        """Get configuration for the current AI provider."""
        provider = self.get('ai_provider', 'ollama')
        
        # Check for environment variables first
        if provider == 'openai':
            api_key = os.environ.get('OPENAI_API_KEY') or self.get('openai.api_key', '')
            return {
                'provider': 'openai',
                'api_key': api_key,
                'model': self.get('openai.model', 'gpt-4')
            }
        elif provider == 'anthropic':
            api_key = os.environ.get('ANTHROPIC_API_KEY') or self.get('anthropic.api_key', '')
            return {
                'provider': 'anthropic',
                'api_key': api_key,
                'model': self.get('anthropic.model', 'claude-3-5-sonnet-20241022')
            }
        else:  # ollama
            return {
                'provider': 'ollama',
                'model': self.get('ollama.model', 'llama2'),
                'base_url': self.get('ollama.base_url', 'http://localhost:11434')
            }
    
    def create_default_config(self, path: Optional[str] = None):
        """
        Create a default configuration file.
        
        Args:
            path: Path to create config file. If None, uses default location.
        """
        if path:
            self.config_path = Path(path)
        
        self.config = self.DEFAULT_CONFIG.copy()
        self.save()
        
        print(f"Default configuration created at: {self.config_path}")
        print("\nEdit this file to configure your AI provider and settings.")
