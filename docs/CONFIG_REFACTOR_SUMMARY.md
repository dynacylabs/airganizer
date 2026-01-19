# Configuration System Refactoring - Implementation Summary

## Overview

The configuration system has been refactored to improve usability, reduce duplication, and add automatic model discovery capabilities.

## Key Changes

### 1. Centralized Credentials

**Before**: Credentials were specified for each model individually
```yaml
models:
  available_models:
    - name: "gpt4o"
      api_key_env: "OPENAI_API_KEY"
    - name: "gpt4_turbo"
      api_key_env: "OPENAI_API_KEY"
```

**After**: Credentials specified once per provider
```yaml
models:
  openai:
    api_key_env: "OPENAI_API_KEY"
  anthropic:
    api_key_env: "ANTHROPIC_API_KEY"
```

### 2. Model Mode Selection

New `model_mode` setting to control which types of models to use:

- **`mixed`** (default): Use both online and local models
- **`online_only`**: Use only OpenAI/Anthropic models
- **`local_only`**: Use only Ollama/local models

```yaml
models:
  model_mode: "mixed"  # online_only, local_only, or mixed
```

### 3. Automatic Model Discovery

New `discovery_method: "auto"` automatically enumerates available models:

```yaml
models:
  discovery_method: "auto"  # auto, config, local_enumerate, local_download
  
  openai:
    auto_enumerate: true
  
  anthropic:
    auto_enumerate: true
  
  ollama:
    auto_enumerate: true
```

**How it works**:
- **OpenAI**: Calls `/v1/models` API to list available models
- **Anthropic**: Uses known list of Claude 3 models
- **Ollama**: Queries local Ollama instance for installed models

### 4. Provider-Specific Configuration

Each provider now has its own configuration section:

```yaml
models:
  openai:
    api_key_env: "OPENAI_API_KEY"
    base_url: "https://api.openai.com/v1"
    auto_enumerate: true
    models: []  # Optional: manually specify models
  
  anthropic:
    api_key_env: "ANTHROPIC_API_KEY"
    base_url: "https://api.anthropic.com"
    auto_enumerate: true
    models: []
  
  ollama:
    base_url: "http://localhost:11434"
    auto_enumerate: true
    auto_download_models: []  # Optional: auto-download these
    models: []
```

## Implementation Details

### Files Modified

1. **config.example.yaml**
   - Restructured to use new provider-based format
   - Added `model_mode` and `discovery_method` settings
   - Removed per-model credential duplication

2. **src/config.py**
   - Added validation for `model_mode` (online_only/local_only/mixed)
   - Added validation for `discovery_method` (auto/config/local_enumerate/local_download)
   - Added provider-specific defaults
   - Added convenience properties: `model_mode`, `discovery_method`, `openai_api_key`, `anthropic_api_key`

3. **src/model_discovery.py**
   - Added `_filter_by_mode()` method to filter models based on `model_mode`
   - Added `_auto_discover_models()` method for automatic discovery
   - Added `_enumerate_openai_models()` to fetch models from OpenAI API
   - Added `_enumerate_anthropic_models()` with known Claude 3 models
   - Added helper methods: `_create_openai_model()`, `_create_anthropic_model()`, `_create_ollama_model()`
   - Updated `_discover_from_config()` to support both old and new config formats
   - Updated `discover_models()` to support "auto" method and apply mode filtering

### Files Created

1. **docs/CONFIGURATION.md**
   - Comprehensive configuration guide
   - Detailed explanation of all settings
   - Examples for common use cases
   - Migration guide from old format
   - Troubleshooting section

2. **docs/CONFIG_QUICKREF.md**
   - Quick reference for common patterns
   - Minimal configuration examples
   - Environment variable setup
   - Common issues and solutions

3. **tests/test_config_refactor.py**
   - Unit tests for config loading
   - Tests for model mode filtering
   - Tests for model creation helpers
   - Backward compatibility tests

## Usage Examples

### Example 1: Automatic Discovery (Recommended)

```yaml
models:
  model_mode: "mixed"
  discovery_method: "auto"
  
  openai:
    api_key_env: "OPENAI_API_KEY"
  
  anthropic:
    api_key_env: "ANTHROPIC_API_KEY"
  
  ollama:
    base_url: "http://localhost:11434"
```

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Example 2: Local-Only Mode

```yaml
models:
  model_mode: "local_only"
  discovery_method: "local_download"
  
  ollama:
    auto_download_models:
      - "llama3.2-vision:latest"
      - "llava:latest"
```

### Example 3: Online-Only Mode

```yaml
models:
  model_mode: "online_only"
  discovery_method: "auto"
  
  openai:
    api_key_env: "OPENAI_API_KEY"
  
  anthropic:
    api_key_env: "ANTHROPIC_API_KEY"
```

### Example 4: Manual Control

```yaml
models:
  model_mode: "mixed"
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

## Benefits

1. **No Credential Duplication**: API keys specified once per provider, not per model
2. **Automatic Discovery**: Zero configuration needed - just provide API keys
3. **Flexible Filtering**: Easy to switch between online/local/mixed modes
4. **Simpler Configuration**: Much less YAML to write and maintain
5. **Future-Proof**: New models automatically discovered as providers release them
6. **Backward Compatible**: Old config format still works

## Migration Guide

To migrate from the old configuration format:

1. **Remove per-model credentials**:
   - Delete `api_key_env` from each model definition
   - Move API keys to provider-level config

2. **Add model_mode**:
   ```yaml
   models:
     model_mode: "mixed"  # or online_only, local_only
   ```

3. **Add discovery_method**:
   ```yaml
   models:
     discovery_method: "auto"  # for automatic discovery
   ```

4. **Restructure providers**:
   ```yaml
   models:
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

5. **Optionally remove model lists**:
   - If using `auto` discovery, manual model lists are optional
   - Keep them if you want to restrict to specific models

## Testing

Run the test suite to verify the implementation:

```bash
python tests/test_config_refactor.py
```

Tests cover:
- Config loading with new structure
- Model mode filtering (online_only/local_only/mixed)
- Model creation helpers
- Backward compatibility with old format

## API Details

### ModelDiscovery Class

#### New Methods

- `_filter_by_mode(models: List[AIModel]) -> List[AIModel]`
  - Filters models based on `model_mode` setting
  - Returns only online models for `online_only`
  - Returns only local models for `local_only`
  - Returns all models for `mixed`

- `_auto_discover_models() -> List[AIModel]`
  - Main method for auto-discovery
  - Calls provider-specific enumeration methods
  - Respects `auto_enumerate` setting for each provider
  - Handles auto-download for Ollama if configured

- `_enumerate_openai_models() -> List[AIModel]`
  - Calls OpenAI `/v1/models` API
  - Filters for GPT-4 and GPT-3.5 models
  - Detects vision capabilities

- `_enumerate_anthropic_models() -> List[AIModel]`
  - Returns known Claude 3 models
  - All Claude 3 models support vision

- `_create_openai_model(model_id: str) -> AIModel`
  - Creates AIModel for OpenAI model
  - Detects vision capabilities from model name

- `_create_anthropic_model(model_id: str) -> AIModel`
  - Creates AIModel for Anthropic model
  - All Claude 3 models marked as vision-capable

- `_create_ollama_model(model_name: str) -> AIModel`
  - Creates AIModel for Ollama model
  - Detects vision capabilities from model name

#### Modified Methods

- `discover_models() -> List[AIModel]`
  - Now supports `auto` discovery method
  - Applies model_mode filtering to all results
  - Logs discovery statistics

- `_discover_from_config() -> List[AIModel]`
  - Now supports both old and new config formats
  - Uses provider-specific sections for new format
  - Falls back to `available_models` for old format

### Config Class

#### New Properties

- `model_mode: str`
  - Returns the configured model mode
  - Default: "mixed"

- `discovery_method: str`
  - Returns the configured discovery method
  - Default: "config"

- `openai_api_key: Optional[str]`
  - Returns OpenAI API key from environment
  - Uses configured environment variable name

- `anthropic_api_key: Optional[str]`
  - Returns Anthropic API key from environment
  - Uses configured environment variable name

## Next Steps

1. **Update existing configurations** to use new format
2. **Test with real API keys** to verify auto-enumeration
3. **Monitor for issues** with backward compatibility
4. **Add more providers** as needed (Google, Azure, etc.)
5. **Implement caching** for discovered models to reduce API calls

## Backward Compatibility

The old configuration format is fully supported:

```yaml
models:
  available_models:
    - name: "gpt4o"
      type: "online"
      provider: "openai"
      model_name: "gpt-4o"
      api_key_env: "OPENAI_API_KEY"
      capabilities: ["text", "image"]
```

The system will automatically detect and use the old format if present.

## Performance Considerations

1. **API Calls**: Auto-enumeration makes API calls to OpenAI
   - Consider caching discovered models
   - Use `discovery_method: "config"` to avoid API calls

2. **Ollama Queries**: Local model enumeration is fast
   - Minimal overhead for local discovery

3. **Filtering**: Model mode filtering is in-memory
   - No performance impact

## Security Considerations

1. **API Keys**: Always use environment variables
   - Never commit API keys to git
   - Use `.env` files for development

2. **Base URLs**: Can be customized for proxy/testing
   - Default to official API endpoints

3. **Model Access**: Respects API key availability
   - Models without valid keys are skipped

## Documentation

- **docs/CONFIGURATION.md**: Comprehensive guide
- **docs/CONFIG_QUICKREF.md**: Quick reference
- **config.example.yaml**: Example configuration
- **tests/test_config_refactor.py**: Test suite

## Summary

The configuration system has been successfully refactored to:
- ✅ Centralize credentials per provider
- ✅ Add model_mode filtering (online_only/local_only/mixed)
- ✅ Implement automatic model discovery
- ✅ Maintain backward compatibility
- ✅ Simplify configuration for end users
- ✅ Provide comprehensive documentation

The system is now more flexible, easier to use, and future-proof for new models and providers.
