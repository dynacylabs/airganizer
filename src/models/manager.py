"""Model lifecycle management - load and unload models as needed."""

import time
from typing import Dict, Optional, List, Set
from dataclasses import dataclass
from datetime import datetime

from ..core.system_resources import get_system_resources
from ..models import ModelRegistry, ModelInfo, get_model_registry
from ..config import get_config


@dataclass
class LoadedModel:
    """Information about a currently loaded model."""
    name: str
    loaded_at: datetime
    ram_used_gb: float
    provider: str
    last_used: datetime


class ModelManager:
    """Manages loading and unloading of models to optimize resource usage."""
    
    def __init__(self, registry: Optional[ModelRegistry] = None, config: Optional[any] = None):
        """
        Initialize model manager.
        
        Args:
            registry: Model registry
            config: Configuration
        """
        self.registry = registry or get_model_registry()
        self.config = config or get_config()
        self.system_resources = get_system_resources()
        
        # Track loaded models
        self.loaded_models: Dict[str, LoadedModel] = {}
        
        # Get configuration
        self.max_concurrent = self.config.get('models.max_concurrent_loaded', 2)
        self.auto_unload = self.config.get('models.auto_unload_idle', True)
        self.idle_timeout_seconds = self.config.get('models.idle_timeout_seconds', 300)  # 5 minutes
    
    def can_load_model(self, model_name: str) -> tuple[bool, str]:
        """
        Check if a model can be loaded given current resources.
        
        Args:
            model_name: Name of model to check
            
        Returns:
            (can_load, reason) tuple
        """
        model_info = self.registry.get_model(model_name)
        if not model_info:
            return False, f"Model {model_name} not found in registry"
        
        # Online models don't need loading
        if model_info.provider in ["openai", "anthropic"]:
            return True, "Online model, no loading needed"
        
        # Check if already loaded
        if model_name in self.loaded_models:
            return True, "Model already loaded"
        
        # Calculate available RAM
        current_ram_used = sum(m.ram_used_gb for m in self.loaded_models.values())
        available_ram = self.system_resources.total_ram_gb - current_ram_used
        
        required_ram = model_info.ram_required_gb or 0
        
        if required_ram > available_ram:
            return False, f"Insufficient RAM: need {required_ram:.1f}GB, have {available_ram:.1f}GB available"
        
        # Check concurrent limit
        local_loaded = sum(1 for m in self.loaded_models.values() if m.provider not in ["openai", "anthropic"])
        if local_loaded >= self.max_concurrent:
            return False, f"Max concurrent models ({self.max_concurrent}) reached"
        
        return True, "Model can be loaded"
    
    def load_model(self, model_name: str, force: bool = False) -> bool:
        """
        Load a model into memory.
        
        Args:
            model_name: Name of model to load
            force: If True, unload other models to make room
            
        Returns:
            True if loaded successfully
        """
        model_info = self.registry.get_model(model_name)
        if not model_info:
            print(f"❌ Model {model_name} not found")
            return False
        
        # Online models don't need loading
        if model_info.provider in ["openai", "anthropic"]:
            return True
        
        # Check if already loaded
        if model_name in self.loaded_models:
            self.loaded_models[model_name].last_used = datetime.now()
            return True
        
        # Check if we can load
        can_load, reason = self.can_load_model(model_name)
        
        if not can_load:
            if force:
                print(f"⚠️  {reason}")
                print(f"🔄 Force loading - will unload other models...")
                self._make_room_for_model(model_info)
            else:
                print(f"❌ Cannot load {model_name}: {reason}")
                return False
        
        # Load the model
        print(f"📥 Loading {model_name}...")
        start_time = time.time()
        
        # For Ollama models, we'd actually trigger loading here
        if model_info.provider == "ollama":
            success = self._load_ollama_model(model_name)
            if not success:
                print(f"❌ Failed to load Ollama model {model_name}")
                return False
        
        load_time = time.time() - start_time
        
        # Track as loaded
        self.loaded_models[model_name] = LoadedModel(
            name=model_name,
            loaded_at=datetime.now(),
            ram_used_gb=model_info.ram_required_gb or 0,
            provider=model_info.provider,
            last_used=datetime.now()
        )
        
        print(f"✅ Loaded {model_name} in {load_time:.1f}s ({model_info.ram_required_gb:.1f}GB RAM)")
        return True
    
    def unload_model(self, model_name: str) -> bool:
        """
        Unload a model from memory.
        
        Args:
            model_name: Name of model to unload
            
        Returns:
            True if unloaded successfully
        """
        if model_name not in self.loaded_models:
            return True  # Already unloaded
        
        loaded = self.loaded_models[model_name]
        
        # Online models don't need unloading
        if loaded.provider in ["openai", "anthropic"]:
            return True
        
        print(f"📤 Unloading {model_name}...")
        
        # For Ollama, we'd trigger unload here
        if loaded.provider == "ollama":
            self._unload_ollama_model(model_name)
        
        # Remove from tracking
        del self.loaded_models[model_name]
        
        print(f"✅ Unloaded {model_name} (freed {loaded.ram_used_gb:.1f}GB)")
        return True
    
    def _make_room_for_model(self, model_info: ModelInfo) -> None:
        """Unload models to make room for a new one."""
        required_ram = model_info.ram_required_gb or 0
        
        # Sort by last used (oldest first)
        models_by_usage = sorted(
            self.loaded_models.values(),
            key=lambda m: m.last_used
        )
        
        # Unload oldest models until we have enough space
        for loaded in models_by_usage:
            if loaded.provider in ["openai", "anthropic"]:
                continue
            
            current_ram_used = sum(m.ram_used_gb for m in self.loaded_models.values())
            available_ram = self.system_resources.total_ram_gb - current_ram_used
            
            if available_ram >= required_ram:
                break
            
            print(f"  Unloading {loaded.name} to make room...")
            self.unload_model(loaded.name)
    
    def unload_idle_models(self) -> None:
        """Unload models that haven't been used recently."""
        if not self.auto_unload:
            return
        
        now = datetime.now()
        to_unload = []
        
        for model_name, loaded in self.loaded_models.items():
            if loaded.provider in ["openai", "anthropic"]:
                continue
            
            idle_seconds = (now - loaded.last_used).total_seconds()
            if idle_seconds > self.idle_timeout_seconds:
                to_unload.append(model_name)
        
        for model_name in to_unload:
            print(f"⏱️  {model_name} idle for {self.idle_timeout_seconds}s, unloading...")
            self.unload_model(model_name)
    
    def _load_ollama_model(self, model_name: str) -> bool:
        """Actually load an Ollama model."""
        try:
            import requests
            host = self.config.get('ai.local.ollama_host', 'http://localhost:11434')
            
            # Trigger model loading by making a simple request
            response = requests.post(
                f"{host}/api/generate",
                json={
                    "model": model_name,
                    "prompt": "ping",
                    "stream": False
                },
                timeout=30
            )
            
            return response.status_code == 200
        except Exception as e:
            print(f"⚠️  Failed to load Ollama model: {e}")
            return False
    
    def _unload_ollama_model(self, model_name: str) -> None:
        """Unload an Ollama model."""
        # Ollama automatically manages memory, but we could add explicit unloading if API supports it
        # For now, just remove from tracking
        pass
    
    def get_loaded_models(self) -> List[LoadedModel]:
        """Get list of currently loaded models."""
        return list(self.loaded_models.values())
    
    def get_available_ram(self) -> float:
        """Get currently available RAM in GB."""
        current_ram_used = sum(m.ram_used_gb for m in self.loaded_models.values())
        return self.system_resources.total_ram_gb - current_ram_used
    
    def get_status(self) -> Dict:
        """Get current manager status."""
        local_loaded = [m for m in self.loaded_models.values() if m.provider not in ["openai", "anthropic"]]
        
        return {
            "total_ram_gb": self.system_resources.total_ram_gb,
            "used_ram_gb": sum(m.ram_used_gb for m in self.loaded_models.values()),
            "available_ram_gb": self.get_available_ram(),
            "loaded_models_count": len(self.loaded_models),
            "local_models_count": len(local_loaded),
            "loaded_models": [
                {
                    "name": m.name,
                    "ram_gb": m.ram_used_gb,
                    "provider": m.provider,
                    "idle_seconds": (datetime.now() - m.last_used).total_seconds()
                }
                for m in self.loaded_models.values()
            ]
        }
    
    def print_status(self) -> None:
        """Print current status."""
        status = self.get_status()
        
        print(f"📊 Model Manager Status:")
        print(f"  RAM: {status['used_ram_gb']:.1f}/{status['total_ram_gb']:.1f}GB used")
        print(f"  Available: {status['available_ram_gb']:.1f}GB")
        print(f"  Loaded: {status['loaded_models_count']} models ({status['local_models_count']} local)")
        
        if status['loaded_models']:
            print(f"\n  Currently loaded:")
            for model in status['loaded_models']:
                idle = model['idle_seconds']
                print(f"    • {model['name']:<20} | {model['ram_gb']:>6.1f}GB | idle: {idle:>6.0f}s")


def get_model_manager() -> ModelManager:
    """Get singleton model manager instance."""
    global _model_manager
    if '_model_manager' not in globals():
        _model_manager = ModelManager()
    return _model_manager
