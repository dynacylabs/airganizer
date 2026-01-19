# Configuration Guide

This document explains how to configure the AI File Organizer.

## Table of Contents
- [Configuration File Structure](#configuration-file-structure)
- [Model Configuration](#model-configuration)
- [Provider Configuration](#provider-configuration)
- [Model Modes](#model-modes)
- [Discovery Methods](#discovery-methods)
- [Migration Guide](#migration-guide)

## Configuration File Structure

The configuration file (`config.yaml`) is structured with the following main sections:

```yaml
directories:
  input_directory: "/path/to/organize"
  output_directory: "/path/to/organized"

stage1:
  recursive: true
  follow_symlinks: false
  include_hidden: false

models:
  model_mode: "mixed"           # online_only, local_only, or mixed
  discovery_method: "auto"      # auto, config, local_enumerate, or local_download
  local_provider: "ollama"
  
  openai:
    api_key_env: "OPENAI_API_KEY"
    base_url: "https://api.openai.com/v1"
    auto_enumerate: true
    models: []  # Optional: manually specify models
  
  anthropic:
    api_key_env: "ANTHROPIC_API_KEY"
    base_url: "https://api.anthropic.com"
    auto_enumerate: true
    models: []  # Optional: manually specify models
  
  ollama:
    base_url: "http://localhost:11434"
    auto_enumerate: true
    auto_download_models: []  # Optional: models to auto-download
    models: []  # Optional: manually specify models

cache:
  enabled: true
  directory: ".airganizer_cache"
  ttl_hours: 24
```

## Model Configuration

### Centralized Credentials

Credentials are now defined **once per provider** instead of per model:

```yaml
models:
  openai:
    api_key_env: "OPENAI_API_KEY"  # Environment variable name
    base_url: "https://api.openai.com/v1"
  
  anthropic:
    api_key_env: "ANTHROPIC_API_KEY"
    base_url: "https://api.anthropic.com"
```

Set the corresponding environment variables:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Mapping Model

The mapping model (used for initial file categorization) pulls credentials from the provider config:

```yaml
stage2:
  mapping_model:
    provider: "openai"           # Uses models.openai credentials
    model_name: "gpt-4o"
```

## Provider Configuration

### OpenAI

```yaml
models:
  openai:
    api_key_env: "OPENAI_API_KEY"
    base_url: "https://api.openai.com/v1"
    auto_enumerate: true          # Automatically fetch available models
    models:                       # Optional: manually specify models
      - "gpt-4o"
      - "gpt-4-turbo"
      - "gpt-3.5-turbo"
```

**Auto-enumeration**: When `auto_enumerate: true`, the system will:
- Call OpenAI's `/v1/models` API endpoint
- Discover all available GPT-4 and GPT-3.5 models
- Automatically detect vision capabilities

**Manual specification**: Set `auto_enumerate: false` and list models explicitly if you want to:
- Control exactly which models are used
- Avoid API calls for model discovery
- Use custom or fine-tuned models

### Anthropic

```yaml
models:
  anthropic:
    api_key_env: "ANTHROPIC_API_KEY"
    base_url: "https://api.anthropic.com"
    auto_enumerate: true
    models:                       # Optional: manually specify models
      - "claude-3-5-sonnet-20241022"
      - "claude-3-opus-20240229"
```

**Note**: Anthropic doesn't provide a models list API endpoint, so auto-enumeration uses a known list of Claude 3 models. All Claude 3 models support vision capabilities.

### Ollama (Local)

```yaml
models:
  ollama:
    base_url: "http://localhost:11434"
    auto_enumerate: true
    auto_download_models:         # Optional: auto-download these models
      - "llama3.2-vision:latest"
      - "llava:latest"
    models:                       # Optional: manually specify models
      - "llama3.2-vision:latest"
```

**Auto-enumeration**: Queries the Ollama API for locally installed models.

**Auto-download**: Models listed in `auto_download_models` will be automatically pulled from Ollama's registry if not already present.

## Model Modes

The `model_mode` setting controls which types of models to use:

### `mixed` (default)
Uses both online and local models:

```yaml
models:
  model_mode: "mixed"
```

**Use when**: You want to leverage both cloud APIs and local models for optimal flexibility.

### `online_only`
Uses only online models (OpenAI, Anthropic):

```yaml
models:
  model_mode: "online_only"
```

**Use when**:
- You have reliable internet and API access
- You want the latest/most powerful models
- You don't have local GPU resources
- You need consistent performance

### `local_only`
Uses only local models (Ollama):

```yaml
models:
  model_mode: "local_only"
```

**Use when**:
- You have privacy concerns
- You have limited/expensive internet
- You have local GPU resources
- You want offline operation

## Discovery Methods

The `discovery_method` setting controls how models are discovered:

### `auto` (recommended)
Automatically discovers models from all configured providers:

```yaml
models:
  discovery_method: "auto"
  model_mode: "mixed"
  
  openai:
    auto_enumerate: true
  anthropic:
    auto_enumerate: true
  ollama:
    auto_enumerate: true
```

**How it works**:
1. Checks each provider's configuration
2. If API key exists and `auto_enumerate: true`, fetches available models
3. For Ollama, queries locally installed models
4. Optionally auto-downloads specified Ollama models
5. Filters results based on `model_mode`

**Advantages**:
- Zero manual configuration
- Always up-to-date with available models
- Respects API key availability

### `config`
Uses manually specified models from configuration:

```yaml
models:
  discovery_method: "config"
  
  openai:
    auto_enumerate: false
    models:
      - "gpt-4o"
      - "gpt-4-turbo"
  
  anthropic:
    auto_enumerate: false
    models:
      - "claude-3-5-sonnet-20241022"
```

**Use when**:
- You want explicit control over models
- You're using custom/fine-tuned models
- You want to avoid discovery API calls

### `local_enumerate`
Only discovers locally available Ollama models:

```yaml
models:
  discovery_method: "local_enumerate"
  local_provider: "ollama"
```

**Use when**:
- You only want to use what's already installed
- You're working offline
- You don't want automatic downloads

### `local_download`
Discovers local models and downloads missing ones:

```yaml
models:
  discovery_method: "local_download"
  
  ollama:
    auto_download_models:
      - "llama3.2-vision:latest"
      - "llava:latest"
```

**Use when**:
- You want specific local models guaranteed available
- You're okay with one-time downloads
- You want to bootstrap a new installation

## Migration Guide

### From Old Configuration

**Old format** (per-model credentials):
```yaml
models:
  available_models:
    - name: "gpt4o"
      type: "online"
      provider: "openai"
      model_name: "gpt-4o"
      api_key_env: "OPENAI_API_KEY"
      capabilities: ["text", "image"]
    
    - name: "claude_opus"
      type: "online"
      provider: "anthropic"
      model_name: "claude-3-opus-20240229"
      api_key_env: "ANTHROPIC_API_KEY"
      capabilities: ["text", "image"]
```

**New format** (centralized credentials):
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
```

### Benefits of New Format

1. **No credential duplication**: API keys specified once per provider
2. **Automatic discovery**: No need to manually list every model
3. **Flexible filtering**: Use `model_mode` to control online/local/mixed
4. **Simpler configuration**: Much less YAML to write and maintain
5. **Future-proof**: New models automatically discovered

### Backward Compatibility

The old `available_models` format is still supported for backward compatibility. The system will automatically detect and use it if present.

## Examples

### Example 1: Online-only with Auto-discovery

```yaml
models:
  model_mode: "online_only"
  discovery_method: "auto"
  
  openai:
    api_key_env: "OPENAI_API_KEY"
    auto_enumerate: true
  
  anthropic:
    api_key_env: "ANTHROPIC_API_KEY"
    auto_enumerate: true

stage2:
  mapping_model:
    provider: "openai"
    model_name: "gpt-4o"
```

Result: Automatically discovers and uses all available GPT-4 and Claude 3 models.

### Example 2: Local-only with Specific Models

```yaml
models:
  model_mode: "local_only"
  discovery_method: "local_download"
  
  ollama:
    base_url: "http://localhost:11434"
    auto_enumerate: true
    auto_download_models:
      - "llama3.2-vision:latest"
      - "llava:latest"

stage2:
  mapping_model:
    provider: "ollama"
    model_name: "llama3.2-vision:latest"
```

Result: Downloads and uses specified Ollama models, works offline.

### Example 3: Mixed with Manual Control

```yaml
models:
  model_mode: "mixed"
  discovery_method: "config"
  
  openai:
    auto_enumerate: false
    models:
      - "gpt-4o"
  
  anthropic:
    auto_enumerate: false
    models:
      - "claude-3-5-sonnet-20241022"
  
  ollama:
    auto_enumerate: false
    models:
      - "llama3.2-vision:latest"

stage2:
  mapping_model:
    provider: "anthropic"
    model_name: "claude-3-5-sonnet-20241022"
```

Result: Uses exactly the specified models, no auto-discovery.

### Example 4: Selective Auto-enumeration

```yaml
models:
  model_mode: "mixed"
  discovery_method: "auto"
  
  openai:
    auto_enumerate: true
  
  anthropic:
    auto_enumerate: false
    models:
      - "claude-3-opus-20240229"  # Only use Opus, not Sonnet
  
  ollama:
    auto_enumerate: true
```

Result: Auto-discovers OpenAI and Ollama models, uses specific Claude model.

## Troubleshooting

### Models not being discovered

1. **Check API keys**: Ensure environment variables are set correctly
2. **Check connectivity**: For online models, ensure internet access
3. **Check Ollama**: For local models, ensure Ollama is running
4. **Check logs**: Run with `-v` flag for detailed logging

### Wrong models being used

1. **Check model_mode**: Ensure it's set correctly (online_only/local_only/mixed)
2. **Check auto_enumerate**: Set to `false` to use manual lists
3. **Check manual lists**: Ensure models are spelled correctly

### API key errors

1. **Check environment variable names**: Must match `api_key_env` setting
2. **Check variable is exported**: Use `echo $OPENAI_API_KEY` to verify
3. **Check key validity**: Test with provider's API directly

## Best Practices

1. **Use auto-discovery**: Unless you have specific requirements, use `discovery_method: "auto"`
2. **Set model_mode appropriately**: Use `online_only` for production, `local_only` for privacy
3. **Keep credentials in environment**: Never commit API keys to git
4. **Use .env files**: Consider using a `.env` file for development
5. **Monitor costs**: Online models cost money; local models use GPU resources
6. **Cache results**: Keep caching enabled to avoid redundant API calls
