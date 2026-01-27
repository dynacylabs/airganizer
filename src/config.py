"""Configuration file handler for AI File Organizer."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional


class Config:
    """Configuration handler for the AI File Organizer."""
    
    def __init__(self, config_path: str):
        """
        Initialize the configuration handler.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._load_config()
        self._validate_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f) or {}
    
    def _validate_config(self) -> None:
        """Validate configuration structure and set defaults."""
        # Set defaults for general settings
        if 'general' not in self.config:
            self.config['general'] = {}
        
        general = self.config['general']
        general.setdefault('log_level', 'INFO')
        general.setdefault('max_file_size', 0)
        general.setdefault('exclude_extensions', [])
        general.setdefault('exclude_dirs', ['.git', '__pycache__', 'node_modules', '.venv'])
        
        # Set defaults for stage1 settings
        if 'stage1' not in self.config:
            self.config['stage1'] = {}
        
        stage1 = self.config['stage1']
        stage1.setdefault('recursive', True)
        stage1.setdefault('follow_symlinks', False)
        stage1.setdefault('include_hidden', False)
        
        # Set defaults for cache settings
        if 'cache' not in self.config:
            self.config['cache'] = {}
        
        cache = self.config['cache']
        cache.setdefault('enabled', True)
        cache.setdefault('directory', '.airganizer_cache')
        cache.setdefault('ttl_hours', 24)
        
        # Set defaults for models settings
        if 'models' not in self.config:
            self.config['models'] = {}
        
        models = self.config['models']
        models.setdefault('model_mode', 'mixed')
        models.setdefault('discovery_method', 'auto')
        
        # Set defaults for provider configs
        for provider in ['openai', 'anthropic', 'ollama']:
            if provider not in models:
                models[provider] = {}
            
            provider_config = models[provider]
            provider_config.setdefault('auto_enumerate', True)
            provider_config.setdefault('models', [])
            
            if provider == 'openai':
                provider_config.setdefault('api_key_env', 'OPENAI_API_KEY')
                provider_config.setdefault('api_key', '')
            elif provider == 'anthropic':
                provider_config.setdefault('api_key_env', 'ANTHROPIC_API_KEY')
                provider_config.setdefault('api_key', '')
            elif provider == 'ollama':
                provider_config.setdefault('base_url', 'http://localhost:11434')
                provider_config.setdefault('auto_download_models', [])
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'general.log_level')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    @property
    def log_level(self) -> str:
        """Get the configured log level."""
        return self.get('general.log_level', 'INFO')
    
    @property
    def max_file_size(self) -> int:
        """Get the maximum file size in bytes."""
        size_mb = self.get('general.max_file_size', 0)
        return size_mb * 1024 * 1024 if size_mb > 0 else 0
    
    @property
    def exclude_extensions(self) -> List[str]:
        """Get list of file extensions to exclude."""
        return self.get('general.exclude_extensions', [])
    
    @property
    def exclude_dirs(self) -> List[str]:
        """Get list of directories to exclude."""
        return self.get('general.exclude_dirs', [])
    
    @property
    def recursive(self) -> bool:
        """Check if recursive scanning is enabled."""
        return self.get('stage1.recursive', True)
    
    @property
    def follow_symlinks(self) -> bool:
        """Check if symbolic links should be followed."""
        return self.get('stage1.follow_symlinks', False)
    
    @property
    def include_hidden(self) -> bool:
        """Check if hidden files should be included."""
        return self.get('stage1.include_hidden', False)
    
    @property
    def cache_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self.get('cache.enabled', True)
    
    @property
    def cache_directory(self) -> str:
        """Get the cache directory path."""
        return self.get('cache.directory', '.airganizer_cache')
    
    @property
    def cache_ttl_hours(self) -> int:
        """Get the cache TTL in hours."""
        return self.get('cache.ttl_hours', 24)
    
    @property
    def model_mode(self) -> str:
        """Get the model mode (online_only, local_only, or mixed)."""
        return self.get('models.model_mode', 'mixed')
    
    @property
    def discovery_method(self) -> str:
        """Get the model discovery method."""
        return self.get('models.discovery_method', 'config')
    
    @property
    def openai_api_key(self) -> Optional[str]:
        """Get the OpenAI API key from environment."""
        api_key_env = self.get('models.openai.api_key_env', 'OPENAI_API_KEY')
        return os.getenv(api_key_env)
    
    @property
    def anthropic_api_key(self) -> Optional[str]:
        """Get the Anthropic API key from environment."""
        api_key_env = self.get('models.anthropic.api_key_env', 'ANTHROPIC_API_KEY')
        return os.getenv(api_key_env)
    
    # Stage 3 settings
    @property
    def stage3_max_files(self) -> int:
        """Get maximum files to analyze in Stage 3."""
        return self.get('stage3.max_files', 0)
    
    @property
    def stage3_temperature(self) -> float:
        """Get AI temperature for Stage 3 analysis."""
        return self.get('stage3.ai.temperature', 0.3)
    
    @property
    def stage3_max_tokens(self) -> int:
        """Get max tokens for Stage 3 AI responses."""
        return self.get('stage3.ai.max_tokens', 1000)
    
    @property
    def stage3_timeout(self) -> int:
        """Get API timeout for Stage 3 in seconds."""
        return self.get('stage3.ai.timeout', 300)
    
    # Stage 4 settings
    @property
    def stage4_batch_size(self) -> int:
        """Get batch size for Stage 4 processing."""
        return self.get('stage4.batch_size', 25)
    
    @property
    def stage4_temperature(self) -> float:
        """Get AI temperature for Stage 4 taxonomy."""
        return self.get('stage4.ai.temperature', 0.3)
    
    @property
    def stage4_max_tokens(self) -> int:
        """Get max tokens for Stage 4 AI responses."""
        return self.get('stage4.ai.max_tokens', 4000)
    
    @property
    def stage4_timeout(self) -> int:
        """Get API timeout for Stage 4 in seconds."""
        return self.get('stage4.ai.timeout', 300)
    
    # Stage 5 settings
    @property
    def stage5_overwrite(self) -> bool:
        """Get whether to overwrite existing files in Stage 5."""
        return self.get('stage5.overwrite', False)
    
    @property
    def stage5_dry_run(self) -> bool:
        """Get whether to perform dry-run in Stage 5."""
        return self.get('stage5.dry_run', False)
    
    # Mapping AI settings
    @property
    def mapping_temperature(self) -> float:
        """Get AI temperature for MIME mapping."""
        return self.get('mapping.ai.temperature', 0.3)
    
    @property
    def mapping_max_tokens(self) -> int:
        """Get max tokens for mapping AI responses."""
        return self.get('mapping.ai.max_tokens', 2000)
    
    @property
    def mapping_timeout(self) -> int:
        """Get API timeout for mapping in seconds."""
        return self.get('mapping.ai.timeout', 60)
