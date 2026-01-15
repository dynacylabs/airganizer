"""System resource detection and management."""

import platform
import psutil
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class SystemResources:
    """System resource information."""
    total_ram_gb: float
    available_ram_gb: float
    cpu_count: int
    platform: str
    has_gpu: bool = False
    gpu_memory_gb: Optional[float] = None
    
    def can_run_model(self, required_ram_gb: float, required_gpu: bool = False) -> bool:
        """
        Check if system can run a model with given requirements.
        
        Args:
            required_ram_gb: RAM required by the model in GB
            required_gpu: Whether model requires GPU
            
        Returns:
            True if system can run the model
        """
        # Use full available RAM - no artificial headroom
        # Model manager will handle dynamic loading/unloading
        if required_ram_gb > self.total_ram_gb:
            return False
        
        if required_gpu and not self.has_gpu:
            return False
        
        return True


def get_system_resources() -> SystemResources:
    """
    Detect current system resources.
    
    Returns:
        SystemResources with current system information
    """
    # Get memory info
    memory = psutil.virtual_memory()
    total_ram_gb = memory.total / (1024 ** 3)
    available_ram_gb = memory.available / (1024 ** 3)
    
    # Get CPU info
    cpu_count = psutil.cpu_count(logical=True)
    
    # Get platform
    system_platform = platform.system()
    
    # Try to detect GPU (basic check)
    has_gpu = False
    gpu_memory_gb = None
    
    try:
        # Try to import torch for GPU detection
        import torch
        if torch.cuda.is_available():
            has_gpu = True
            # Get first GPU memory
            gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
    except ImportError:
        pass
    
    return SystemResources(
        total_ram_gb=total_ram_gb,
        available_ram_gb=available_ram_gb,
        cpu_count=cpu_count,
        platform=system_platform,
        has_gpu=has_gpu,
        gpu_memory_gb=gpu_memory_gb
    )


def format_resources(resources: SystemResources) -> Dict[str, str]:
    """Format system resources for display."""
    return {
        "total_ram": f"{resources.total_ram_gb:.1f} GB",
        "available_ram": f"{resources.available_ram_gb:.1f} GB",
        "cpu_cores": str(resources.cpu_count),
        "platform": resources.platform,
        "gpu": "Yes" if resources.has_gpu else "No",
        "gpu_memory": f"{resources.gpu_memory_gb:.1f} GB" if resources.gpu_memory_gb else "N/A"
    }


def estimate_model_ram_usage(model_size_mb: float, provider: str) -> float:
    """
    Estimate RAM usage for a model.
    
    Args:
        model_size_mb: Model size in MB
        provider: Model provider (openai, anthropic, ollama, etc.)
        
    Returns:
        Estimated RAM usage in GB
    """
    if provider in ["openai", "anthropic"]:
        # Online models don't use local RAM (just API calls)
        return 0.1  # Minimal overhead for API requests
    
    # Local models need ~1.2x their size in RAM (for loading + inference overhead)
    base_gb = model_size_mb / 1024 * 1.2
    
    # Add overhead for inference (context window, activations, etc.)
    # Typically need 2-4GB additional for small models, 8-16GB for large models
    if model_size_mb < 3000:  # < 3GB model
        overhead = 2.0
    elif model_size_mb < 7000:  # 3-7GB model
        overhead = 4.0
    elif model_size_mb < 13000:  # 7-13GB model
        overhead = 8.0
    else:  # 13GB+ model
        overhead = 16.0
    
    return base_gb + overhead
