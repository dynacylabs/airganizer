"""Configuration management for Airganizer."""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import json


class Config:
    """Configuration manager for Airganizer."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_file: Path to configuration file (optional)
        """
        self.config_file = config_file or self._get_default_config_path()
        self.config: Dict[str, Any] = self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        home = Path.home()
        config_dir = home / '.config' / 'airganizer'
        config_dir.mkdir(parents=True, exist_ok=True)
        return str(config_dir / 'config.json')
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not Path(self.config_file).exists():
            return self._get_default_config()
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                default = self._get_default_config()
                return self._deep_merge(default, config)
        except Exception:
            return self._get_default_config()
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "ai": {
                "mode": "online",  # "online" or "local"
                "default_provider": "openai",  # online: openai, anthropic; local: ollama
                "chunk_size": 50,
                "temperature": 0.3,
                "max_tokens": 4000,
                "local": {
                    "ollama_host": "http://localhost:11434",
                    "default_model": "llama3.2"
                }
            },
            "models": {
                "auto_download": False,  # Auto-download models if needed
                "model_dir": str(Path.home() / '.cache' / 'airganizer' / 'models'),
                "available_models": {},  # Dict of available models with constraints
                # Format: {"model_name": {"enabled": bool, "max_ram_gb": float|null, "allow_online": bool}}
                "explicit_mapping": {},  # e.g., {"application/pdf": "llama-vision", "image/*": "clip"}
                "recommendations_cache": {},  # Cache AI recommendations per file type
                "max_concurrent_loaded": 2,  # Max local models loaded simultaneously
                "auto_unload_idle": True,  # Automatically unload idle models
                "idle_timeout_seconds": 300  # Unload models idle for 5 minutes
            },
            "system": {
                "max_ram_usage_gb": None,  # None = auto-detect, or set explicit limit
                "require_gpu": False,  # Require GPU for local models
                "respect_resource_limits": True  # Filter models based on system resources
            },
            "scan": {
                "use_binwalk": False,
                "default_output": "data/metadata.json",
                "collect_full_metadata": True  # Collect all metadata upfront
            },
            "propose": {
                "default_output": "data/proposed_structure.json"
            },
            "analyze": {
                "default_output": "data/analysis.json",
                "ask_ai_for_models": True,  # Ask AI which models to use
                "batch_size": 10  # Files to batch when asking for model recommendations
            }
        }
    
    def save(self) -> None:
        """Save configuration to file."""
        config_path = Path(self.config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_ai_api_key(self, provider: str) -> Optional[str]:
        """Get API key for AI provider."""
        env_vars = {
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'claude': 'ANTHROPIC_API_KEY'
        }
        
        env_var = env_vars.get(provider.lower())
        if env_var:
            return os.getenv(env_var)
        
        return None
    
    def should_use_local_ai(self) -> bool:
        """Check if local AI should be used."""
        return self.get('ai.use_local', False)
    
    def get_local_endpoint(self) -> str:
        """Get local AI endpoint."""
        return self.get('ai.local_endpoint', 'http://localhost:11434')
    
    def should_auto_download_models(self) -> bool:
        """Check if models should be auto-downloaded."""
        return self.get('models.auto_download', False)
    
    def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """Get dict of available models with their constraints."""
        return self.get('models.available_models', {})
    
    def add_available_model(self, model_name: str, enabled: bool = True,
                          max_ram_gb: Optional[float] = None,
                          allow_online: bool = True) -> None:
        """Add a model to the available models list with constraints."""
        models_dict = self.get('models.available_models', {})
        models_dict[model_name] = {
            "enabled": enabled,
            "max_ram_gb": max_ram_gb,
            "allow_online": allow_online
        }
        self.set('models.available_models', models_dict)
        self.save()
    
    def is_model_enabled(self, model_name: str) -> bool:
        """Check if a model is enabled by user."""
        models_dict = self.get('models.available_models', {})
        if not models_dict:  # If not configured, all models are allowed
            return True
        if model_name not in models_dict:
            return False  # If configured but not in list, not allowed
        return models_dict[model_name].get("enabled", True)
    
    def get_model_ram_limit(self, model_name: str) -> Optional[float]:
        """Get RAM limit for a specific model."""
        models_dict = self.get('models.available_models', {})
        if model_name in models_dict:
            return models_dict[model_name].get("max_ram_gb")
        return None
    
    def is_online_model_allowed(self, model_name: str) -> bool:
        """Check if online model is allowed."""
        models_dict = self.get('models.available_models', {})
        if not models_dict:  # If not configured, all models are allowed
            return True
        if model_name not in models_dict:
            return True  # If not explicitly configured, allow by default
        return models_dict[model_name].get("allow_online", True)
    
    def get_system_ram_limit(self) -> Optional[float]:
        """Get system-wide RAM limit in GB."""
        return self.get('system.max_ram_usage_gb')
    
    def respect_resource_limits(self) -> bool:
        """Check if resource limits should be enforced."""
        return self.get('system.respect_resource_limits', True)
    
    def get_file_type_model(self, file_type: str) -> Optional[str]:
        """Get explicitly mapped model for a file type."""
        mappings = self.get('models.file_type_mappings', {})
        return mappings.get(file_type)
    
    def set_file_type_model(self, file_type: str, model_name: str) -> None:
        """Set model mapping for a file type."""
        mappings = self.get('models.file_type_mappings', {})
        mappings[file_type] = model_name
        self.set('models.file_type_mappings', mappings)
        self.save()
    
    def get_preferred_models(self, category: str) -> List[str]:
        """Get preferred models for a category."""
        prefs = self.get('models.preferred_models', {})
        return prefs.get(category, [])
    
    def is_online_mode(self) -> bool:
        """Check if using online AI."""
        return self.get('ai.mode', 'online') == 'online'
    
    def is_local_mode(self) -> bool:
        """Check if using local AI."""
        return self.get('ai.mode', 'online') == 'local'
    
    def get_model_for_filetype(self, mime_type: str) -> Optional[str]:
        """Get explicitly configured model for a file type."""
        explicit = self.get('models.explicit_mapping', {})
        
        # Direct match
        if mime_type in explicit:
            return explicit[mime_type]
        
        # Wildcard match (e.g., "image/*")
        main_type = mime_type.split('/')[0] if '/' in mime_type else mime_type
        wildcard = f"{main_type}/*"
        if wildcard in explicit:
            return explicit[wildcard]
        
        return None
    
    def add_available_model(self, model_name: str) -> None:
        """Add a model to the list of available models."""
        available = self.get('models.available_models', [])
        if model_name not in available:
            available.append(model_name)
            self.set('models.available_models', available)
            self.save()
    
    def is_model_available(self, model_name: str) -> bool:
        """Check if a model is available locally."""
        available = self.get('models.available_models', [])
        return model_name in available
    
    def should_auto_download(self) -> bool:
        """Check if models should be auto-downloaded."""
        return self.get('models.auto_download', False)
    
    def get_model_recommendation_cache(self, mime_type: str) -> Optional[Dict[str, Any]]:
        """Get cached model recommendation for a file type."""
        cache = self.get('models.recommendations_cache', {})
        return cache.get(mime_type)
    
    def cache_model_recommendation(self, mime_type: str, recommendation: Dict[str, Any]) -> None:
        """Cache model recommendation for a file type."""
        cache = self.get('models.recommendations_cache', {})
        cache[mime_type] = recommendation
        self.set('models.recommendations_cache', cache)
        self.save()


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
