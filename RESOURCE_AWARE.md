# Resource-Aware Model Selection

Airganizer now intelligently selects models based on your system resources!

## Key Features

### 1. Automatic Resource Detection
- Detects total and available RAM
- Identifies CPU cores
- Checks for GPU availability
- Platform detection

### 2. Model RAM Requirements
All models now have RAM requirements:
- **Online models** (OpenAI/Anthropic): ~0.1GB (API only)
- **llama3.2:1b**: 3.0GB (small, for limited systems)
- **llama3.2**: 4.5GB (standard local model)
- **codellama**: 7.0GB (code analysis)
- **llama3.2-vision**: 12.0GB (vision tasks)

### 3. User-Controlled Model Availability

Configure which models can be used in `~/.config/airganizer/config.json`:

```json
{
  "models": {
    "available_models": {
      "gpt-4o-vision": {
        "enabled": true,
        "allow_online": true
      },
      "llama3.2": {
        "enabled": true,
        "max_ram_gb": 6.0
      },
      "llama3.2-vision": {
        "enabled": false
      }
    }
  },
  "system": {
    "max_ram_usage_gb": 8.0,
    "respect_resource_limits": true
  }
}
```

### 4. Smart Model Filtering

The recommender automatically:
- ✅ Filters out models that exceed available RAM
- ✅ Respects user-defined model availability
- ✅ Honors per-model RAM limits
- ✅ Distinguishes online vs local models
- ✅ Leaves headroom for system operations

## Usage Examples

### View System Resources

```bash
python demo_resources.py
```

Output shows:
- Your system's RAM, CPU, GPU
- All available models and their requirements
- Which models can run on your system
- Smart recommendations

### Configure Resource Limits

```python
from src.config import get_config

config = get_config()

# Set system-wide RAM limit
config.set('system.max_ram_usage_gb', 8.0)

# Enable specific models with constraints
config.add_available_model('llama3.2', enabled=True, max_ram_gb=6.0)
config.add_available_model('llama3.2-vision', enabled=False)  # Disable large model

# Online models only
config.add_available_model('gpt-4o', enabled=True, allow_online=True)
config.add_available_model('llama3.2', enabled=False)  # Disable local
```

### Analyze with Resource Constraints

```bash
# System automatically filters models
python -m src analyze -d /path/to/files

# Recommendations will only include models that:
# 1. Are enabled in config
# 2. Don't exceed RAM limits
# 3. Match online/local preferences
```

## Configuration Reference

### `models.available_models`

Dictionary of enabled models with constraints:

```json
{
  "model_name": {
    "enabled": bool,           // Whether to use this model
    "max_ram_gb": float|null,  // Max RAM this model can use
    "allow_online": bool       // Whether online API calls are allowed
  }
}
```

**Default**: Empty dict = all models allowed

**Examples**:

```json
// Only allow small local models
{
  "llama3.2:1b": {"enabled": true, "max_ram_gb": 4.0},
  "llama3.2": {"enabled": true, "max_ram_gb": 6.0}
}

// Only online models
{
  "gpt-4o": {"enabled": true, "allow_online": true},
  "claude-3-5-sonnet": {"enabled": true, "allow_online": true}
}

// Mixed: online for vision, local for text
{
  "gpt-4o-vision": {"enabled": true, "allow_online": true},
  "llama3.2": {"enabled": true, "max_ram_gb": 6.0}
}
```

### `system.max_ram_usage_gb`

System-wide RAM limit in GB.

- **Default**: `null` (auto-detect total RAM)
- **Purpose**: Override system RAM for testing or limits

**Example**:
```json
{
  "system": {
    "max_ram_usage_gb": 8.0  // Pretend system only has 8GB
  }
}
```

### `system.respect_resource_limits`

Whether to enforce resource limits.

- **Default**: `true`
- **Purpose**: Disable for testing or when limits don't matter

**Example**:
```json
{
  "system": {
    "respect_resource_limits": false  // Allow any model regardless of RAM
  }
}
```

## How It Works

### 1. Resource Detection

```python
from src.core import get_system_resources

resources = get_system_resources()
print(f"Total RAM: {resources.total_ram_gb:.1f}GB")
print(f"Available: {resources.available_ram_gb:.1f}GB")
```

### 2. Model Filtering

```python
from src.models import get_model_registry

registry = get_model_registry()

# Get models that fit in 8GB
suitable = registry.filter_by_resources(available_ram_gb=8.0)

for model in suitable:
    print(f"{model.name}: {model.ram_required_gb}GB required")
```

### 3. Intelligent Recommendations

The ModelRecommender now:

1. Detects system resources
2. Gets user configuration
3. Filters models by:
   - User enabled/disabled
   - RAM requirements
   - Online/local preferences
4. Recommends from filtered list
5. Falls back gracefully if no models fit

## System Requirements Guide

### Minimal (< 8GB RAM)
- **Recommended**: Online models only
- **Local option**: `llama3.2:1b` (3GB)
- **Note**: Very limited local model options

### Standard (8-16GB RAM)
- **Recommended**: Mix of online and local
- **Can run**: `llama3.2`, `codellama`
- **Cannot run**: Large vision models

### High-End (16GB+ RAM)
- **Recommended**: Any model
- **Can run**: All models including `llama3.2-vision`
- **Best option**: Full local model suite

## Testing

```bash
# Install dependencies (includes psutil for resource detection)
pip install -r requirements.txt

# View your system capabilities
python demo_resources.py

# Test with resource constraints
export OPENAI_API_KEY='your-key'
python test_analyze.py
```

## API Reference

### SystemResources

```python
@dataclass
class SystemResources:
    total_ram_gb: float        # Total system RAM
    available_ram_gb: float    # Currently available RAM
    cpu_count: int             # Number of CPU cores
    platform: str              # OS platform
    has_gpu: bool              # Whether GPU is available
    gpu_memory_gb: float|None  # GPU VRAM if available
    
    def can_run_model(self, required_ram_gb: float, 
                     required_gpu: bool = False) -> bool:
        """Check if system can run a model."""
```

### Config Methods

```python
config = get_config()

# Resource limits
config.get_system_ram_limit() -> float|None
config.respect_resource_limits() -> bool

# Model control
config.is_model_enabled(model_name: str) -> bool
config.get_model_ram_limit(model_name: str) -> float|None
config.is_online_model_allowed(model_name: str) -> bool
config.add_available_model(model_name, enabled, max_ram_gb, allow_online)
```

### ModelRegistry Methods

```python
registry = get_model_registry()

# Filter by resources
suitable = registry.filter_by_resources(
    available_ram_gb=8.0,
    require_gpu=False
)

# Get by provider
online = registry.get_models_by_provider('openai')
local = registry.get_models_by_provider('ollama')
```

## Benefits

1. **Prevents OOM Errors**: Won't try to load models that don't fit
2. **User Control**: Explicit model enabling/disabling
3. **Cost Control**: Limit online API usage
4. **Performance**: Choose appropriate models for hardware
5. **Flexibility**: Mix online and local based on needs

## Example Scenarios

### Scenario 1: Limited System (8GB RAM)

```json
{
  "system": {"max_ram_usage_gb": 8.0},
  "models": {
    "available_models": {
      "gpt-4o": {"enabled": true, "allow_online": true},
      "llama3.2:1b": {"enabled": true, "max_ram_gb": 4.0}
    }
  }
}
```

Result: Uses online for complex tasks, tiny local model for simple text.

### Scenario 2: No Internet (Local Only)

```json
{
  "models": {
    "available_models": {
      "gpt-4o": {"enabled": false},
      "claude-3-5-sonnet": {"enabled": false},
      "llama3.2": {"enabled": true},
      "codellama": {"enabled": true}
    }
  }
}
```

Result: Only uses local models, no API calls.

### Scenario 3: Cost-Conscious (Minimize API)

```json
{
  "models": {
    "available_models": {
      "gpt-4o-vision": {"enabled": true, "allow_online": true},  // Only for images
      "llama3.2": {"enabled": true},                              // Text locally
      "codellama": {"enabled": true}                              // Code locally
    }
  }
}
```

Result: API only for vision, everything else local.

## Summary

Airganizer is now **resource-aware** and **user-controlled**:

✅ Automatically detects system capabilities  
✅ Filters models by RAM requirements  
✅ Respects user-defined availability  
✅ Prevents resource exhaustion  
✅ Balances online vs local intelligently  
✅ Provides smart recommendations  

Your system, your rules! 🚀
