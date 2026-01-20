# Configuration Reference

Complete reference for configuring AIrganizer. All configuration is done via YAML files.

## Table of Contents

- [Configuration File Structure](#configuration-file-structure)
- [General Settings](#general-settings)
- [Stage 1 Settings](#stage-1-settings)
- [AI Model Configuration](#ai-model-configuration)
- [Model Discovery Methods](#model-discovery-methods)
- [Provider Configuration](#provider-configuration)
- [Cache Settings](#cache-settings)
- [Advanced Options](#advanced-options)
- [Example Configurations](#example-configurations)

## Configuration File Structure

```yaml
# General settings
log_level: "INFO"
max_file_size: 0
exclude_extensions: [".tmp", ".cache"]
exclude_dirs: ["node_modules", ".git"]

# Stage 1: File scanning
stage1:
  recursive: true
  follow_symlinks: false
  include_hidden: false

# AI Model configuration
models:
  model_mode: "mixed"
  discovery_method: "auto"
  local_provider: "ollama"
  mapping_model: "gpt-4o"
  
  openai:
    api_key_env: "OPENAI_API_KEY"
    auto_enumerate: true
  
  anthropic:
    api_key_env: "ANTHROPIC_API_KEY"
    auto_enumerate: true
  
  ollama:
    base_url: "http://localhost:11434"
    auto_enumerate: true

# Stage 3: AI analysis
stage3:
  max_retries: 3
  retry_delay: 5
  batch_size: 10

# Stage 4: Taxonomy generation
stage4:
  max_depth: 5
  min_files_per_category: 3

# Stage 5: File organization
stage5:
  handle_conflicts: "rename"
  preserve_timestamps: true
  create_logs: true

# Cache settings
cache:
  enabled: true
  directory: ".cache_airganizer"
```

## General Settings

### `log_level`

**Type:** String  
**Default:** `"INFO"`  
**Options:** `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"`

Controls logging verbosity.

```yaml
log_level: "DEBUG"  # Most verbose
log_level: "INFO"   # Recommended
log_level: "ERROR"  # Errors only
```

### `max_file_size`

**Type:** Integer (MB)  
**Default:** `0` (unlimited)

Maximum file size to process in megabytes. Files larger than this are excluded.

```yaml
max_file_size: 100  # Limit to 100 MB
max_file_size: 0    # No limit
```

### `exclude_extensions`

**Type:** List of strings  
**Default:** `[]`

File extensions to exclude from processing.

```yaml
exclude_extensions:
  - ".tmp"
  - ".cache"
  - ".log"
  - ".bak"
```

### `exclude_dirs`

**Type:** List of strings  
**Default:** `[]`

Directory names to exclude from scanning.

```yaml
exclude_dirs:
  - "node_modules"
  - ".git"
  - "__pycache__"
  - ".venv"
  - "venv"
```

## Stage 1 Settings

Configuration for file scanning and metadata collection.

### `stage1.recursive`

**Type:** Boolean  
**Default:** `true`

Enable recursive directory scanning.

```yaml
stage1:
  recursive: true   # Scan subdirectories
  recursive: false  # Only top-level directory
```

### `stage1.follow_symlinks`

**Type:** Boolean  
**Default:** `false`

Follow symbolic links during scanning.

```yaml
stage1:
  follow_symlinks: true   # Follow symlinks
  follow_symlinks: false  # Skip symlinks
```

**Warning:** Following symlinks can cause infinite loops if there are circular references.

### `stage1.include_hidden`

**Type:** Boolean  
**Default:** `false`

Include hidden files (starting with `.`).

```yaml
stage1:
  include_hidden: true   # Include hidden files
  include_hidden: false  # Skip hidden files
```

## AI Model Configuration

Configuration for AI model discovery and usage.

### `models.model_mode`

**Type:** String  
**Default:** `"mixed"`  
**Options:** `"online_only"`, `"local_only"`, `"mixed"`

Controls which types of AI models to use.

```yaml
models:
  model_mode: "online_only"  # Only OpenAI/Anthropic
  model_mode: "local_only"   # Only Ollama/local
  model_mode: "mixed"        # Both online and local
```

**Use cases:**
- `online_only`: Best quality, requires API keys and internet
- `local_only`: Privacy-focused, offline, free
- `mixed`: Balanced approach, uses best model for each file type

### `models.discovery_method`

**Type:** String  
**Default:** `"auto"`  
**Options:** `"auto"`, `"config"`, `"local_enumerate"`, `"local_download"`

How to discover available AI models.

```yaml
models:
  discovery_method: "auto"             # Recommended: auto-discover all
  discovery_method: "config"           # Use predefined models only
  discovery_method: "local_enumerate"  # Discover local models only
  discovery_method: "local_download"   # Auto-download local models
```

**Method comparison:**

| Method | Description | Use Case |
|--------|-------------|----------|
| `auto` | Auto-discover from all providers | Best for most users |
| `config` | Use only models listed in config | Precise control needed |
| `local_enumerate` | Discover installed local models | Offline/privacy mode |
| `local_download` | Auto-download required models | First-time setup |

### `models.local_provider`

**Type:** String  
**Default:** `"ollama"`  
**Options:** `"ollama"`, `"llamacpp"`, `"transformers"`

Local AI provider to use.

```yaml
models:
  local_provider: "ollama"       # Recommended
  local_provider: "llamacpp"     # Advanced users
  local_provider: "transformers" # Direct HuggingFace
```

### `models.mapping_model`

**Type:** String  
**Default:** `"gpt-4o"`

AI model used to create MIME-to-model mappings (orchestrator model).

```yaml
models:
  mapping_model: "gpt-4o"                      # GPT-4 Turbo (recommended)
  mapping_model: "claude-3-5-sonnet-20241022"  # Claude 3.5 Sonnet
  mapping_model: "gpt-4"                       # GPT-4
```

**Note:** This model should be capable and reliable as it determines which AI models analyze each file type.

## Model Discovery Methods

### Auto-Discovery (Recommended)

Zero configuration - discovers all available models automatically.

```yaml
models:
  model_mode: "mixed"
  discovery_method: "auto"
  
  openai:
    api_key_env: "OPENAI_API_KEY"
    auto_enumerate: true
  
  anthropic:
    api_key_env: "ANTHROPIC_API_KEY"
    auto_enumerate: true
  
  ollama:
    base_url: "http://localhost:11434"
    auto_enumerate: true
```

**What it does:**
1. Connects to each configured provider
2. Enumerates available models
3. Tests connectivity
4. Uses AI to map MIME types to best models

### Config-Based Discovery

Manual control - use only specified models.

```yaml
models:
  discovery_method: "config"
  
  openai:
    api_key_env: "OPENAI_API_KEY"
    auto_enumerate: false
    models:
      - "gpt-4o"
      - "gpt-4-turbo"
      - "gpt-4-vision-preview"
  
  anthropic:
    api_key_env: "ANTHROPIC_API_KEY"
    auto_enumerate: false
    models:
      - "claude-3-5-sonnet-20241022"
      - "claude-3-opus-20240229"
  
  ollama:
    auto_enumerate: false
    models:
      - "llama3.2-vision:latest"
      - "llava:latest"
```

**When to use:** Need precise control over which models are available.

### Local Enumerate

Discover only local models - offline mode.

```yaml
models:
  model_mode: "local_only"
  discovery_method: "local_enumerate"
  
  ollama:
    base_url: "http://localhost:11434"
    auto_enumerate: true
```

**What it does:**
1. Connects to local Ollama instance
2. Lists installed models
3. Uses only these models

**Prerequisite:** Models must already be installed (`ollama pull <model>`).

### Local Download

Auto-download required models.

```yaml
models:
  model_mode: "local_only"
  discovery_method: "local_download"
  
  ollama:
    base_url: "http://localhost:11434"
    auto_download_models:
      - "llama3.2-vision:latest"
      - "llava:latest"
      - "llama3.2:latest"
```

**What it does:**
1. Downloads specified models if not installed
2. Downloads additional models needed by MIME mapping
3. Automatically sets up complete local environment

**When to use:** First-time setup, automated deployment.

## Provider Configuration

### OpenAI Configuration

```yaml
models:
  openai:
    api_key_env: "OPENAI_API_KEY"      # Environment variable name
    base_url: "https://api.openai.com/v1"  # Optional: custom endpoint
    auto_enumerate: true                # Auto-discover models
    models:                             # Manual model list (if auto_enumerate: false)
      - "gpt-4o"
      - "gpt-4-turbo"
      - "gpt-4-vision-preview"
    timeout: 60                         # Request timeout in seconds
    max_retries: 3                      # Retry failed requests
```

**API Key Setup:**
```bash
export OPENAI_API_KEY="sk-..."
```

**Available Models:**
- `gpt-4o` - GPT-4 Turbo with vision (recommended)
- `gpt-4-turbo` - GPT-4 Turbo (text only)
- `gpt-4-vision-preview` - GPT-4 Vision (older)
- `gpt-4` - GPT-4 (text only)
- `gpt-3.5-turbo` - GPT-3.5 (budget option)

### Anthropic Configuration

```yaml
models:
  anthropic:
    api_key_env: "ANTHROPIC_API_KEY"
    base_url: "https://api.anthropic.com"
    auto_enumerate: true
    models:
      - "claude-3-5-sonnet-20241022"
      - "claude-3-opus-20240229"
      - "claude-3-sonnet-20240229"
    timeout: 60
    max_retries: 3
```

**API Key Setup:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Available Models:**
- `claude-3-5-sonnet-20241022` - Claude 3.5 Sonnet (recommended)
- `claude-3-opus-20240229` - Claude 3 Opus (most capable)
- `claude-3-sonnet-20240229` - Claude 3 Sonnet (balanced)
- `claude-3-haiku-20240307` - Claude 3 Haiku (fast, budget)

### Ollama Configuration

```yaml
models:
  ollama:
    base_url: "http://localhost:11434"
    auto_enumerate: true
    models:
      - "llama3.2-vision:latest"
      - "llava:latest"
      - "llama3.2:latest"
    auto_download_models:  # For local_download method
      - "llama3.2-vision:latest"
      - "llava:latest"
    timeout: 120  # Longer timeout for local models
```

**Setup:**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama
ollama serve

# Download models
ollama pull llama3.2-vision
ollama pull llava
```

**Popular Models:**
- `llama3.2-vision:latest` - Llama 3.2 with vision (recommended)
- `llava:latest` - LLaVA vision model
- `llama3.2:latest` - Llama 3.2 (text only)
- `llama3.1:latest` - Llama 3.1 (text only)

## Cache Settings

### `cache.enabled`

**Type:** Boolean  
**Default:** `true`

Enable/disable caching system.

```yaml
cache:
  enabled: true   # Use cache (recommended)
  enabled: false  # Disable cache
```

**Note:** Can also disable via `--no-cache` CLI flag.

### `cache.directory`

**Type:** String  
**Default:** `".cache_airganizer"`

Directory for cache storage.

```yaml
cache:
  directory: ".cache_airganizer"       # Default
  directory: "/tmp/airganizer_cache"   # Custom location
```

## Advanced Options

### Stage 3: AI Analysis Settings

```yaml
stage3:
  max_retries: 3      # Retry failed AI requests
  retry_delay: 5      # Seconds between retries
  batch_size: 10      # Files per batch (for rate limiting)
  timeout: 60         # Request timeout in seconds
```

### Stage 4: Taxonomy Generation Settings

```yaml
stage4:
  max_depth: 5                    # Maximum taxonomy depth
  min_files_per_category: 3       # Minimum files to create category
  taxonomy_model: "gpt-4o"        # Model for taxonomy generation
  allow_multiple_categories: false # Allow files in multiple categories
```

### Stage 5: File Organization Settings

```yaml
stage5:
  handle_conflicts: "rename"  # How to handle filename conflicts
  preserve_timestamps: true   # Keep original file timestamps
  create_logs: true           # Create excluded/error logs
  organize_mode: "move"       # "move" or "copy"
```

**Conflict handling options:**
- `rename`: Append number to filename (file.txt → file_1.txt)
- `skip`: Skip file if conflict exists
- `overwrite`: Overwrite existing file

## Example Configurations

### Example 1: Quick Start (Recommended)

```yaml
log_level: "INFO"
max_file_size: 0
exclude_extensions: [".tmp", ".cache", ".log"]
exclude_dirs: ["node_modules", ".git", "__pycache__"]

stage1:
  recursive: true
  follow_symlinks: false
  include_hidden: false

models:
  model_mode: "mixed"
  discovery_method: "auto"
  mapping_model: "gpt-4o"
  
  openai:
    api_key_env: "OPENAI_API_KEY"
    auto_enumerate: true
  
  anthropic:
    api_key_env: "ANTHROPIC_API_KEY"
    auto_enumerate: true
  
  ollama:
    base_url: "http://localhost:11434"
    auto_enumerate: true

cache:
  enabled: true
  directory: ".cache_airganizer"
```

### Example 2: Privacy Mode (Local Only)

```yaml
log_level: "INFO"
max_file_size: 0

stage1:
  recursive: true
  follow_symlinks: false
  include_hidden: false

models:
  model_mode: "local_only"
  discovery_method: "local_download"
  local_provider: "ollama"
  mapping_model: "llama3.2-vision:latest"
  
  ollama:
    base_url: "http://localhost:11434"
    auto_download_models:
      - "llama3.2-vision:latest"
      - "llava:latest"
      - "llama3.2:latest"

cache:
  enabled: true
  directory: ".cache_airganizer"
```

### Example 3: Online Only (Best Quality)

```yaml
log_level: "INFO"
max_file_size: 100  # Limit to 100 MB

stage1:
  recursive: true
  follow_symlinks: false
  include_hidden: false

models:
  model_mode: "online_only"
  discovery_method: "config"
  mapping_model: "gpt-4o"
  
  openai:
    api_key_env: "OPENAI_API_KEY"
    auto_enumerate: false
    models:
      - "gpt-4o"
      - "gpt-4-turbo"
  
  anthropic:
    api_key_env: "ANTHROPIC_API_KEY"
    auto_enumerate: false
    models:
      - "claude-3-5-sonnet-20241022"

cache:
  enabled: true
  directory: ".cache_airganizer"
```

### Example 4: Minimal (Testing)

```yaml
log_level: "DEBUG"
max_file_size: 10  # Small files only

stage1:
  recursive: false  # Top-level only
  follow_symlinks: false
  include_hidden: false

models:
  model_mode: "online_only"
  discovery_method: "config"
  mapping_model: "gpt-4o"
  
  openai:
    api_key_env: "OPENAI_API_KEY"
    auto_enumerate: false
    models: ["gpt-4o"]

cache:
  enabled: false  # No cache during testing
```

### Example 5: Production (Robust)

```yaml
log_level: "WARNING"  # Minimal logging
max_file_size: 0
exclude_extensions: [".tmp", ".cache", ".log", ".bak", ".swp"]
exclude_dirs: ["node_modules", ".git", "__pycache__", ".venv", "venv"]

stage1:
  recursive: true
  follow_symlinks: false
  include_hidden: false

models:
  model_mode: "mixed"
  discovery_method: "auto"
  mapping_model: "gpt-4o"
  
  openai:
    api_key_env: "OPENAI_API_KEY"
    auto_enumerate: true
    timeout: 120
    max_retries: 5
  
  anthropic:
    api_key_env: "ANTHROPIC_API_KEY"
    auto_enumerate: true
    timeout: 120
    max_retries: 5
  
  ollama:
    base_url: "http://localhost:11434"
    auto_enumerate: true
    timeout: 180

stage3:
  max_retries: 5
  retry_delay: 10
  batch_size: 50

stage5:
  handle_conflicts: "rename"
  preserve_timestamps: true
  create_logs: true

cache:
  enabled: true
  directory: ".cache_airganizer"
```

## Configuration Best Practices

1. **Start with auto-discovery:** Use `discovery_method: "auto"` for simplest setup
2. **Use mixed mode:** Balance quality and cost with `model_mode: "mixed"`
3. **Enable caching:** Always keep `cache.enabled: true` for resumability
4. **Set exclusions:** Exclude unnecessary files to speed up processing
5. **Test first:** Use small `max_file_size` for initial testing
6. **Monitor logs:** Use `log_level: "DEBUG"` during development
7. **Secure API keys:** Use environment variables, never hardcode keys
8. **Backup configs:** Keep multiple config files for different scenarios

## Troubleshooting

### Issue: Models not discovered

**Solution:** Check API keys and network connectivity:
```bash
export OPENAI_API_KEY="your-key"
curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Issue: Ollama connection failed

**Solution:** Ensure Ollama is running:
```bash
ollama serve
ollama list  # Verify models installed
```

### Issue: Cache not working

**Solution:** Check cache directory permissions and ensure same paths:
```bash
ls -la .cache_airganizer/
```

### Issue: Too many API errors

**Solution:** Increase timeouts and retries:
```yaml
models:
  openai:
    timeout: 120
    max_retries: 5
```

## See Also

- [USAGE.md](USAGE.md) - Complete usage guide
- [DEVELOPMENT.md](DEVELOPMENT.md) - Architecture and development guide
- [config.example.yaml](config.example.yaml) - Full example configuration
