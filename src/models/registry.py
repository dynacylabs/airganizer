"""Model registry and management."""

from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from dataclasses import dataclass, asdict


@dataclass
class ModelInfo:
    """Information about an analysis model."""
    name: str
    type: str  # "vision", "nlp", "ocr", "audio", "code", etc.
    provider: str  # "openai", "anthropic", "local", "huggingface", etc.
    capabilities: List[str]  # e.g., ["image_analysis", "object_detection"]
    file_types: List[str]  # MIME types this model can handle
    is_available: bool = False
    size_mb: Optional[float] = None
    local_path: Optional[str] = None
    ram_required_gb: Optional[float] = None  # Estimated RAM requirement in GB
    requires_gpu: bool = False  # Whether model requires GPU
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelInfo':
        """Create from dictionary."""
        return cls(**data)


class ModelRegistry:
    """Registry of available analysis models."""
    
    def __init__(self, registry_path: Optional[str] = None):
        """
        Initialize model registry.
        
        Args:
            registry_path: Path to registry JSON file
        """
        if registry_path:
            self.registry_path = Path(registry_path)
        else:
            config_dir = Path.home() / '.config' / 'airganizer'
            config_dir.mkdir(parents=True, exist_ok=True)
            self.registry_path = config_dir / 'model_registry.json'
        
        self.models: Dict[str, ModelInfo] = self._load_registry()
    
    def _load_registry(self) -> Dict[str, ModelInfo]:
        """Load registry from file."""
        if not self.registry_path.exists():
            return self._get_default_models()
        
        try:
            with open(self.registry_path, 'r') as f:
                data = json.load(f)
                return {
                    name: ModelInfo.from_dict(info)
                    for name, info in data.items()
                }
        except Exception:
            return self._get_default_models()
    
    def _get_default_models(self) -> Dict[str, ModelInfo]:
        """Get default model registry."""
        return {
            # Vision models (online - minimal RAM)
            "gpt-4o-vision": ModelInfo(
                name="gpt-4o-vision",
                type="vision",
                provider="openai",
                capabilities=["image_analysis", "ocr", "object_detection", "image_description"],
                file_types=["image/jpeg", "image/png", "image/gif", "image/webp"],
                ram_required_gb=0.1  # API only, minimal overhead
            ),
            "claude-3-5-sonnet-vision": ModelInfo(
                name="claude-3-5-sonnet-vision",
                type="vision",
                provider="anthropic",
                capabilities=["image_analysis", "ocr", "document_understanding"],
                file_types=["image/jpeg", "image/png", "image/gif", "image/webp"],
                ram_required_gb=0.1  # API only, minimal overhead
            ),
            
            # Document analysis (online - minimal RAM)
            "gpt-4o": ModelInfo(
                name="gpt-4o",
                type="nlp",
                provider="openai",
                capabilities=["text_analysis", "document_understanding", "code_analysis"],
                file_types=["text/plain", "application/pdf", "text/markdown", "text/x-script.python"],
                ram_required_gb=0.1  # API only, minimal overhead
            ),
            "claude-3-5-sonnet": ModelInfo(
                name="claude-3-5-sonnet",
                type="nlp",
                provider="anthropic",
                capabilities=["text_analysis", "document_understanding", "code_analysis"],
                file_types=["text/plain", "application/pdf", "text/markdown", "text/x-script.python"],
                ram_required_gb=0.1  # API only, minimal overhead
            ),
            
            # Local models (require significant RAM)
            "llama3.2-vision": ModelInfo(
                name="llama3.2-vision",
                type="vision",
                provider="ollama",
                capabilities=["image_analysis", "ocr"],
                file_types=["image/jpeg", "image/png", "image/gif"],
                size_mb=7300,
                ram_required_gb=12.0,  # 7.3GB model + ~4-5GB overhead
                is_available=False
            ),
            "llama3.2": ModelInfo(
                name="llama3.2",
                type="nlp",
                provider="ollama",
                capabilities=["text_analysis", "code_analysis"],
                file_types=["text/plain", "text/markdown", "text/x-script.python"],
                size_mb=2000,
                ram_required_gb=4.5,  # 2GB model + ~2-2.5GB overhead
                is_available=False
            ),
            "codellama": ModelInfo(
                name="codellama",
                type="code",
                provider="ollama",
                capabilities=["code_analysis", "code_generation"],
                file_types=["text/x-script.python", "text/x-script.javascript", "text/x-c"],
                size_mb=3800,
                ram_required_gb=7.0,  # 3.8GB model + ~3GB overhead
                is_available=False
            ),
            "llama3.2:1b": ModelInfo(
                name="llama3.2:1b",
                type="nlp",
                provider="ollama",
                capabilities=["text_analysis"],
                file_types=["text/plain", "text/markdown"],
                size_mb=1300,
                ram_required_gb=3.0,  # Smaller model for limited systems
                is_available=False
            )
        }
    
    def save(self) -> None:
        """Save registry to file."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            name: model.to_dict()
            for name, model in self.models.items()
        }
        
        with open(self.registry_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def filter_by_resources(self, available_ram_gb: float,
                           require_gpu: bool = False) -> List[ModelInfo]:
        """
        Filter models that can run with given resources.
        
        Args:
            available_ram_gb: Available RAM in GB
            require_gpu: Whether to filter for GPU models only
            
        Returns:
            List of models that can run with given resources
        """
        suitable_models = []
        for model in self.models.values():
            # Check RAM requirement
            if model.ram_required_gb and model.ram_required_gb > available_ram_gb:
                continue
            
            # Check GPU requirement
            if require_gpu and not model.requires_gpu:
                continue
            
            suitable_models.append(model)
        
        return suitable_models
    
    def get_models_by_provider(self, provider: str) -> List[ModelInfo]:
        """Get all models from a specific provider."""
        return [m for m in self.models.values() if m.provider == provider]
    
    def get_model(self, name: str) -> Optional[ModelInfo]:
        """Get model info by name."""
        return self.models.get(name)
    
    def add_model(self, model: ModelInfo) -> None:
        """Add or update a model in the registry."""
        self.models[model.name] = model
        self.save()
    
    def get_models_for_filetype(self, mime_type: str) -> List[ModelInfo]:
        """Get all models that can handle a file type."""
        matching = []
        
        for model in self.models.values():
            if mime_type in model.file_types:
                matching.append(model)
            else:
                # Check wildcard match
                main_type = mime_type.split('/')[0] if '/' in mime_type else mime_type
                for file_type in model.file_types:
                    if file_type.endswith('/*') and file_type.startswith(main_type):
                        matching.append(model)
                        break
        
        return matching
    
    def get_available_models(self, capability: Optional[str] = None) -> List[ModelInfo]:
        """Get all available models, optionally filtered by capability."""
        available = [m for m in self.models.values() if m.is_available]
        
        if capability:
            available = [m for m in available if capability in m.capabilities]
        
        return available
    
    def mark_available(self, model_name: str, available: bool = True) -> None:
        """Mark a model as available or unavailable."""
        if model_name in self.models:
            self.models[model_name].is_available = available
            self.save()
    
    def get_recommendations_summary(self) -> Dict[str, Any]:
        """Get summary of available models."""
        by_type = {}
        available_count = 0
        
        for model in self.models.values():
            if model.type not in by_type:
                by_type[model.type] = []
            by_type[model.type].append(model.name)
            
            if model.is_available:
                available_count += 1
        
        return {
            "total_models": len(self.models),
            "available_models": available_count,
            "by_type": by_type
        }


# Global registry instance
_registry: Optional[ModelRegistry] = None


def get_model_registry() -> ModelRegistry:
    """Get global model registry instance."""
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry
