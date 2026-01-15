# Quick Start: Resource-Aware Airganizer

## Installation

```bash
cd /workspaces/airganizer

# Install dependencies (includes psutil for resource detection)
pip install -r requirements.txt
```

## 1. Check Your System Resources

```bash
python demo_resources.py
```

This shows:
- Your RAM, CPU, GPU capabilities
- All available models
- Which models will run on your system
- Smart recommendations

## 2. Configure Model Availability

Edit `~/.config/airganizer/config.json`:

### Example 1: Limited RAM (< 8GB) - Use Online Models

```json
{
  "system": {
    "max_ram_usage_gb": 8.0,
    "respect_resource_limits": true
  },
  "models": {
    "available_models": {
      "gpt-4o": {"enabled": true, "allow_online": true},
      "gpt-4o-vision": {"enabled": true, "allow_online": true},
      "llama3.2-vision": {"enabled": false}
    }
  }
}
```

### Example 2: Moderate RAM (8-16GB) - Mixed Approach

```json
{
  "models": {
    "available_models": {
      "gpt-4o-vision": {"enabled": true, "allow_online": true},
      "llama3.2": {"enabled": true, "max_ram_gb": 6.0},
      "llama3.2:1b": {"enabled": true, "max_ram_gb": 4.0}
    }
  }
}
```

### Example 3: High RAM (16GB+) - All Models

```json
{
  "models": {
    "available_models": {
      // Leave empty or don't specify to allow all models
    }
  }
}
```

### Example 4: No Internet - Local Only

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

## 3. Test It

```bash
# Set API key (if using online models)
export OPENAI_API_KEY='your-key'

# Run test
python test_analyze.py
```

## 4. Analyze Files

```bash
# The system will automatically:
# - Check your RAM
# - Filter models that fit
# - Respect your enabled/disabled settings
# - Recommend appropriate models

python -m src analyze -d test_data
```

## Key Configuration Options

| Setting | Default | Purpose |
|---------|---------|---------|
| `system.max_ram_usage_gb` | `null` (auto) | Limit total RAM usage |
| `system.respect_resource_limits` | `true` | Enforce RAM filtering |
| `models.available_models` | `{}` (all allowed) | Control which models to use |
| `models.auto_download` | `false` | Auto-download local models |

## Model RAM Requirements

| Model | RAM Required | Type |
|-------|-------------|------|
| gpt-4o | 0.1GB | Online (API) |
| gpt-4o-vision | 0.1GB | Online (API) |
| claude-3-5-sonnet | 0.1GB | Online (API) |
| llama3.2:1b | 3.0GB | Local (tiny) |
| llama3.2 | 4.5GB | Local (standard) |
| codellama | 7.0GB | Local (code) |
| llama3.2-vision | 12.0GB | Local (vision) |

## What's New?

✅ **Auto-detects system RAM, CPU, GPU**  
✅ **Filters models that won't fit**  
✅ **User controls which models are allowed**  
✅ **Per-model RAM limits**  
✅ **Online vs local model preferences**  
✅ **Prevents out-of-memory errors**  
✅ **Smart recommendations based on hardware**  

## Troubleshooting

**"No suitable models found"**  
→ Your system doesn't have enough RAM for any enabled local models  
→ Solution: Enable online models or use smaller local models

**"Model X disabled by user"**  
→ Check `models.available_models` in config  
→ Set `{"model_name": {"enabled": true}}`

**Want to ignore RAM limits (testing)?**  
→ Set `system.respect_resource_limits: false`

## Examples

```python
from src.core import get_system_resources
from src.models import get_model_registry
from src.config import get_config

# Check resources
resources = get_system_resources()
print(f"RAM: {resources.total_ram_gb:.1f}GB")

# Get suitable models
registry = get_model_registry()
suitable = registry.filter_by_resources(resources.total_ram_gb * 0.8)
print(f"Can run {len(suitable)} models")

# Configure
config = get_config()
config.add_available_model('llama3.2', enabled=True, max_ram_gb=6.0)
```

Ready to run resource-aware file analysis! 🚀
