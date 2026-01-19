# Configuration Quick Reference

## Model Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `mixed` | Both online and local models | Maximum flexibility |
| `online_only` | Only OpenAI/Anthropic | Best performance, requires API keys |
| `local_only` | Only Ollama | Privacy, offline operation |

## Discovery Methods

| Method | Description | When to Use |
|--------|-------------|-------------|
| `auto` | Auto-discover from all providers | Recommended for most users |
| `config` | Use manually specified models | Fine-tuned control |
| `local_enumerate` | Only local models already installed | Offline, no downloads |
| `local_download` | Local models + auto-download | Bootstrap new installation |

## Minimal Configuration

### Auto-discovery (recommended)

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

stage2:
  mapping_model:
    provider: "openai"
    model_name: "gpt-4o"
```

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Local-only

```yaml
models:
  model_mode: "local_only"
  discovery_method: "local_download"
  
  ollama:
    auto_download_models:
      - "llama3.2-vision:latest"

stage2:
  mapping_model:
    provider: "ollama"
    model_name: "llama3.2-vision:latest"
```

### Online-only

```yaml
models:
  model_mode: "online_only"
  discovery_method: "auto"
  
  openai:
    api_key_env: "OPENAI_API_KEY"
  
  anthropic:
    api_key_env: "ANTHROPIC_API_KEY"

stage2:
  mapping_model:
    provider: "anthropic"
    model_name: "claude-3-5-sonnet-20241022"
```

## Provider Settings

### OpenAI
```yaml
openai:
  api_key_env: "OPENAI_API_KEY"
  base_url: "https://api.openai.com/v1"
  auto_enumerate: true
  models: []  # Optional manual list
```

### Anthropic
```yaml
anthropic:
  api_key_env: "ANTHROPIC_API_KEY"
  base_url: "https://api.anthropic.com"
  auto_enumerate: true
  models: []  # Optional manual list
```

### Ollama
```yaml
ollama:
  base_url: "http://localhost:11434"
  auto_enumerate: true
  auto_download_models: []  # Optional auto-download
  models: []  # Optional manual list
```

## Common Patterns

### Pattern: Maximum Automation
- `discovery_method: "auto"`
- `auto_enumerate: true` for all providers
- No manual model lists

### Pattern: Explicit Control
- `discovery_method: "config"`
- `auto_enumerate: false`
- Manual model lists specified

### Pattern: Offline Operation
- `model_mode: "local_only"`
- `discovery_method: "local_enumerate"`
- Ollama running locally

### Pattern: Cost Control
- `model_mode: "online_only"`
- Manually specify cheaper models
- `auto_enumerate: false`

## Environment Variables

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional: Custom base URLs
export OPENAI_BASE_URL="https://custom-endpoint.com/v1"
export ANTHROPIC_BASE_URL="https://custom-endpoint.com"
```

## Common Issues

| Issue | Solution |
|-------|----------|
| "No models discovered" | Check API keys are set |
| "Model not available" | Ensure provider is running (Ollama) |
| "Permission denied" | Check API key validity |
| "Connection refused" | Check Ollama is running on correct port |
| "Wrong models used" | Check `model_mode` setting |

## Tips

- Use `auto` discovery method unless you need specific control
- Set `model_mode` based on your requirements (privacy vs performance)
- Keep API keys in environment, not config file
- Enable caching to reduce API calls
- Use `-v` flag for verbose logging during setup
