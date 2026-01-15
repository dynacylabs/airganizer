# Dynamic Model Loading

Airganizer now supports **dynamic model loading and unloading** to optimize resource usage!

## What's New

### 1. Model Manager

A new `ModelManager` class handles loading/unloading models on-demand:

```python
from src.models import get_model_manager

manager = get_model_manager()

# Load a model
manager.load_model("llama3.2")

# Use it...

# Unload when done
manager.unload_model("llama3.2")
```

### 2. Full RAM Usage (100%)

**Changed**: No more 20% headroom! The system now uses **100% of available RAM**.

- **Before**: Only 80% RAM usable (left 20% headroom)
- **Now**: 100% RAM usable with dynamic management

**Why?** The model manager intelligently loads/unloads models as needed, so we don't need to artificially limit ourselves.

### 3. Automatic Model Management

The manager automatically:
- ✅ **Loads models** when needed
- ✅ **Unloads models** to make room for others
- ✅ **Tracks idle time** for each model
- ✅ **Cleans up idle models** after timeout
- ✅ **Respects concurrent limits**

## How It Works

### Sequential Model Usage

```python
# Your system: 16GB RAM

# Load llama3.2 (4.5GB)
manager.load_model("llama3.2")
# RAM: 4.5GB used, 11.5GB free

# Do some text analysis...

# Unload llama3.2
manager.unload_model("llama3.2")
# RAM: 0GB used, 16GB free

# Load llama3.2-vision (12GB)
manager.load_model("llama3.2-vision")
# RAM: 12GB used, 4GB free

# Do image analysis...
```

### Force Loading (Auto-Unload)

```python
# Load first model
manager.load_model("llama3.2")        # 4.5GB

# Load second model
manager.load_model("codellama")       # 7.0GB
# Total: 11.5GB used

# Try to load huge model with force=True
manager.load_model("llama3.2-vision", force=True)  # 12GB
# Manager automatically unloads llama3.2 and codellama
# Then loads llama3.2-vision
```

### Automatic Idle Cleanup

```python
# Load a model
manager.load_model("llama3.2")

# Use it
# ...

# 5 minutes later (default timeout)
# Manager automatically unloads if not used
manager.unload_idle_models()
```

## Configuration

### `models.max_concurrent_loaded`

Max number of local models loaded simultaneously.

**Default**: `2`

**Example**:
```json
{
  "models": {
    "max_concurrent_loaded": 3
  }
}
```

### `models.auto_unload_idle`

Automatically unload models that haven't been used recently.

**Default**: `true`

**Example**:
```json
{
  "models": {
    "auto_unload_idle": false
  }
}
```

### `models.idle_timeout_seconds`

How long a model can be idle before auto-unloading.

**Default**: `300` (5 minutes)

**Example**:
```json
{
  "models": {
    "idle_timeout_seconds": 600  // 10 minutes
  }
}
```

## API Reference

### ModelManager

```python
from src.models import get_model_manager

manager = get_model_manager()

# Check if model can be loaded
can_load, reason = manager.can_load_model("llama3.2")

# Load a model
success = manager.load_model("llama3.2")

# Load with force (auto-unload others)
success = manager.load_model("llama3.2-vision", force=True)

# Unload a model
manager.unload_model("llama3.2")

# Unload all idle models
manager.unload_idle_models()

# Get available RAM
available = manager.get_available_ram()  # GB

# Get loaded models
loaded = manager.get_loaded_models()

# Print status
manager.print_status()
```

### LoadedModel

```python
@dataclass
class LoadedModel:
    name: str              # Model name
    loaded_at: datetime    # When loaded
    ram_used_gb: float     # RAM usage
    provider: str          # Provider (ollama, etc)
    last_used: datetime    # Last access time
```

## Demo

```bash
python demo_model_manager.py
```

Shows:
- System resources
- Loading/unloading models
- Hitting concurrent limits
- Automatic room-making
- Status tracking

## Benefits

### 1. **Run Larger Models**

**Before**: 16GB RAM with 20% headroom = 12.8GB usable
- ❌ Cannot run llama3.2-vision (needs 12GB)

**Now**: 16GB RAM with dynamic loading = 16GB usable
- ✅ Can run llama3.2-vision!

### 2. **Better Resource Utilization**

**Before**: Multiple small models loaded = wasted RAM if not all needed

**Now**: Load models only when needed, unload when done

### 3. **Automatic Memory Management**

**Before**: Manual model management required

**Now**: Automatic loading, unloading, and cleanup

### 4. **Flexible Workflows**

```python
# Analyze different file types sequentially
for file in files:
    if file.is_image():
        manager.load_model("llama3.2-vision")
        # analyze image
        manager.unload_model("llama3.2-vision")
    elif file.is_code():
        manager.load_model("codellama")
        # analyze code
        manager.unload_model("codellama")
    else:
        manager.load_model("llama3.2")
        # analyze text
        manager.unload_model("llama3.2")
```

## Integration

The ModelManager integrates with ModelRecommender:

```python
from src.ai import create_model_recommender

# Recommender automatically uses model manager
recommender = create_model_recommender(provider='ollama')

# When recommending models, it checks:
# 1. Can the model be loaded? (RAM available?)
# 2. Should we unload others to make room?
# 3. Is the model idle and should be cleaned up?
```

## Trade-offs

### ✅ Pros
- Use full system RAM (100%)
- Run larger models on limited systems
- Automatic memory management
- Better resource utilization

### ⚠️ Considerations
- **Loading time**: Each model load takes time
- **Processing overhead**: Load/unload cycles add latency
- **Disk I/O**: Loading from disk repeatedly

### 💡 Optimization Tips

1. **Batch similar files**: Process all images together to avoid reloading vision model
2. **Adjust concurrent limit**: Higher = less unloading, but more RAM usage
3. **Tune idle timeout**: Longer = less reloading, but models stay in RAM
4. **Use online models**: For frequently-needed capabilities to avoid local loading

## Example Configuration

### Aggressive (Max Performance)
```json
{
  "models": {
    "max_concurrent_loaded": 3,
    "auto_unload_idle": false,
    "idle_timeout_seconds": 3600
  }
}
```
Keeps models loaded longer, uses more RAM.

### Conservative (Max Memory Efficiency)
```json
{
  "models": {
    "max_concurrent_loaded": 1,
    "auto_unload_idle": true,
    "idle_timeout_seconds": 60
  }
}
```
Unloads quickly, minimal RAM usage.

### Balanced (Default)
```json
{
  "models": {
    "max_concurrent_loaded": 2,
    "auto_unload_idle": true,
    "idle_timeout_seconds": 300
  }
}
```
Good balance of performance and memory.

## Summary

🎉 **Dynamic model loading enables:**

- ✅ **100% RAM usage** (no artificial limits)
- ✅ **Automatic load/unload** (smart memory management)
- ✅ **Run larger models** on limited systems
- ✅ **Idle cleanup** (free unused memory)
- ✅ **Configurable limits** (concurrent models, timeouts)
- ⚠️ **Trade-off**: Loading time vs. memory optimization

Now you can run any model that fits in your system's total RAM! 🚀
