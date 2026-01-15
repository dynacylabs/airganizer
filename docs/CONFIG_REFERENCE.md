# Configuration Reference

Complete reference for Airganizer configuration options.

## Configuration File Location

`data/config.json` (created automatically on first run if it doesn't exist)

## Complete Configuration Example

```json
{
  "ai": {
    "mode": "online",
    "default_provider": "openai",
    "openai_api_key": "sk-...",
    "anthropic_api_key": "sk-ant-...",
    "ollama_base_url": "http://localhost:11434"
  },
  "models": {
    "auto_download": false,
    "explicit_mapping": {
      "image/jpeg": "gpt-4o-vision",
      "image/png": "gpt-4o-vision",
      "image/gif": "gpt-4o-vision",
      "image/webp": "gpt-4o-vision",
      "application/pdf": "claude-3-5-sonnet-vision",
      "text/plain": "llama3.2",
      "text/x-python": "gpt-4o",
      "text/x-shellscript": "gpt-4o",
      "application/json": "llama3.2",
      "application/xml": "llama3.2",
      "text/html": "gpt-4o",
      "text/css": "gpt-4o",
      "text/javascript": "gpt-4o",
      "application/zip": "gpt-4o",
      "application/x-tar": "gpt-4o"
    },
    "available_models": [
      "gpt-4o",
      "gpt-4o-vision",
      "claude-3-5-sonnet",
      "claude-3-5-sonnet-vision",
      "llama3.2",
      "llama3.2-vision"
    ]
  },
  "analyze": {
    "ask_ai_for_models": true,
    "batch_size": 20,
    "mime_type_cache": {}
  },
  "scanning": {
    "include_hidden": false,
    "skip_binwalk": false,
    "output_path": "data/metadata.json"
  },
  "proposing": {
    "chunk_size": 50,
    "temperature": 0.3,
    "output_path": "data/proposals.json"
  }
}
```

## Configuration Sections

### `ai` - AI Provider Settings

Controls which AI service to use and how to connect.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `mode` | string | `"online"` | AI mode: `"online"` (cloud APIs) or `"local"` (Ollama) |
| `default_provider` | string | `"openai"` | Default AI provider: `"openai"`, `"anthropic"`, or `"ollama"` |
| `openai_api_key` | string | from env | OpenAI API key (or set `OPENAI_API_KEY` env var) |
| `anthropic_api_key` | string | from env | Anthropic API key (or set `ANTHROPIC_API_KEY` env var) |
| `ollama_base_url` | string | `"http://localhost:11434"` | Ollama server URL for local AI |

**Examples:**

Online mode with OpenAI:
```json
{
  "ai": {
    "mode": "online",
    "default_provider": "openai",
    "openai_api_key": "sk-..."
  }
}
```

Online mode with Anthropic:
```json
{
  "ai": {
    "mode": "online",
    "default_provider": "anthropic",
    "anthropic_api_key": "sk-ant-..."
  }
}
```

Local mode with Ollama:
```json
{
  "ai": {
    "mode": "local",
    "default_provider": "ollama",
    "ollama_base_url": "http://localhost:11434"
  }
}
```

### `models` - Model Management

Controls which models are available and how they're mapped to file types.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `auto_download` | boolean | `false` | Auto-download models when needed (local mode only) |
| `explicit_mapping` | object | `{}` | Map MIME types to specific models |
| `available_models` | array | default list | Models available for use |

**Examples:**

Explicit model mappings (bypasses AI recommendations):
```json
{
  "models": {
    "explicit_mapping": {
      "image/jpeg": "gpt-4o-vision",
      "application/pdf": "claude-3-5-sonnet-vision",
      "text/plain": "llama3.2"
    }
  }
}
```

Available models list:
```json
{
  "models": {
    "available_models": [
      "gpt-4o",
      "gpt-4o-vision",
      "claude-3-5-sonnet-vision",
      "llama3.2",
      "llama3.2-vision"
    ]
  }
}
```

Auto-download enabled (local mode):
```json
{
  "ai": {
    "mode": "local"
  },
  "models": {
    "auto_download": true
  }
}
```

### `analyze` - Analysis Settings

Controls how the analyze command behaves.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `ask_ai_for_models` | boolean | `true` | Let AI recommend models (vs using explicit mappings) |
| `batch_size` | integer | `20` | Number of files to send to AI in one request |
| `mime_type_cache` | object | `{}` | Cached AI recommendations by MIME type (auto-managed) |

**Examples:**

Use AI recommendations:
```json
{
  "analyze": {
    "ask_ai_for_models": true,
    "batch_size": 20
  }
}
```

Use only explicit mappings (no AI calls):
```json
{
  "analyze": {
    "ask_ai_for_models": false
  },
  "models": {
    "explicit_mapping": {
      "image/jpeg": "gpt-4o-vision",
      "application/pdf": "claude-3-5-sonnet-vision"
    }
  }
}
```

Large batch size for speed (more files per API call):
```json
{
  "analyze": {
    "batch_size": 50
  }
}
```

Small batch size for detail (fewer files per API call):
```json
{
  "analyze": {
    "batch_size": 10
  }
}
```

### `scanning` - File Scanning Settings

Controls how files are scanned.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `include_hidden` | boolean | `false` | Include hidden files (starting with `.`) |
| `skip_binwalk` | boolean | `false` | Skip binwalk analysis (faster scanning) |
| `output_path` | string | `"data/metadata.json"` | Default output file for scan results |

**Examples:**

Include hidden files:
```json
{
  "scanning": {
    "include_hidden": true
  }
}
```

Skip binwalk for faster scanning:
```json
{
  "scanning": {
    "skip_binwalk": true
  }
}
```

Custom output path:
```json
{
  "scanning": {
    "output_path": "results/scan_2024.json"
  }
}
```

### `proposing` - Structure Proposal Settings

Controls how AI proposes organizational structures.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `chunk_size` | integer | `50` | Files per AI request when proposing structure |
| `temperature` | float | `0.3` | AI creativity level (0.0-1.0, higher = more creative) |
| `output_path` | string | `"data/proposals.json"` | Default output file for proposals |

**Examples:**

Conservative AI (low creativity):
```json
{
  "proposing": {
    "temperature": 0.1
  }
}
```

Creative AI (high creativity):
```json
{
  "proposing": {
    "temperature": 0.7
  }
}
```

Large chunks for speed:
```json
{
  "proposing": {
    "chunk_size": 100
  }
}
```

Small chunks for detail:
```json
{
  "proposing": {
    "chunk_size": 25
  }
}
```

## Common Configuration Scenarios

### Scenario 1: OpenAI Only, Online

```json
{
  "ai": {
    "mode": "online",
    "default_provider": "openai",
    "openai_api_key": "sk-..."
  },
  "models": {
    "available_models": ["gpt-4o", "gpt-4o-vision"]
  },
  "analyze": {
    "ask_ai_for_models": true
  }
}
```

### Scenario 2: Anthropic Only, Online

```json
{
  "ai": {
    "mode": "online",
    "default_provider": "anthropic",
    "anthropic_api_key": "sk-ant-..."
  },
  "models": {
    "available_models": [
      "claude-3-5-sonnet",
      "claude-3-5-sonnet-vision"
    ]
  },
  "analyze": {
    "ask_ai_for_models": true
  }
}
```

### Scenario 3: Local Only (Ollama)

```json
{
  "ai": {
    "mode": "local",
    "default_provider": "ollama",
    "ollama_base_url": "http://localhost:11434"
  },
  "models": {
    "available_models": ["llama3.2", "llama3.2-vision"],
    "auto_download": true
  },
  "analyze": {
    "ask_ai_for_models": true
  }
}
```

### Scenario 4: Hybrid (Local + Cloud)

Use local models for common files, cloud for special cases:

```json
{
  "ai": {
    "mode": "online",
    "default_provider": "openai"
  },
  "models": {
    "explicit_mapping": {
      "text/plain": "llama3.2",
      "application/json": "llama3.2",
      "image/jpeg": "gpt-4o-vision",
      "application/pdf": "claude-3-5-sonnet-vision"
    },
    "available_models": [
      "llama3.2",
      "gpt-4o-vision",
      "claude-3-5-sonnet-vision"
    ]
  },
  "analyze": {
    "ask_ai_for_models": false
  }
}
```

### Scenario 5: Cost-Optimized

Minimize API calls with caching and explicit mappings:

```json
{
  "ai": {
    "mode": "online",
    "default_provider": "openai"
  },
  "models": {
    "explicit_mapping": {
      "text/plain": "llama3.2",
      "text/x-python": "gpt-4o",
      "image/jpeg": "gpt-4o-vision"
    }
  },
  "analyze": {
    "ask_ai_for_models": true,
    "batch_size": 50
  }
}
```

Common types use explicit mappings (no API calls), uncommon types ask AI once and cache.

### Scenario 6: Quality-Focused

Premium models for best results:

```json
{
  "ai": {
    "mode": "online",
    "default_provider": "openai"
  },
  "models": {
    "available_models": [
      "gpt-4o",
      "gpt-4o-vision",
      "claude-3-5-sonnet-vision"
    ]
  },
  "analyze": {
    "ask_ai_for_models": true,
    "batch_size": 10
  },
  "proposing": {
    "temperature": 0.5
  }
}
```

Small batches for detailed analysis, mix of best models.

## Environment Variables

You can use environment variables instead of storing API keys in config:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

Environment variables take precedence over config file settings.

## Cache Management

The `analyze.mime_type_cache` stores AI recommendations to avoid repeat API calls:

```json
{
  "analyze": {
    "mime_type_cache": {
      "image/jpeg": {
        "primary_model": "gpt-4o-vision",
        "cached_at": "2024-01-15T10:30:00Z",
        "analysis_tasks": ["Object detection", "Scene understanding"]
      },
      "application/pdf": {
        "primary_model": "claude-3-5-sonnet-vision",
        "cached_at": "2024-01-15T10:32:00Z",
        "analysis_tasks": ["Text extraction", "Layout analysis"]
      }
    }
  }
}
```

**To clear cache:** Delete the `mime_type_cache` section or individual MIME types.

**To disable cache:** Delete cached entries before each run.

## Configuration Tips

1. **Start Simple**: Begin with defaults, add customization as needed
2. **Use Environment Variables**: Keep API keys out of version control
3. **Test Locally First**: Use Ollama to test without API costs
4. **Cache Wisely**: Let cache build up for common file types
5. **Explicit for Known**: Use explicit_mapping for file types you always want specific models for
6. **AI for Unknown**: Use ask_ai_for_models for flexibility with new file types
7. **Monitor Costs**: Watch batch_size and explicit_mapping to control API usage

## Troubleshooting

### Configuration not loading

Check file location: `data/config.json`
Check JSON syntax: Use a JSON validator

### API keys not working

Check environment variables:
```bash
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY
```

Check config file permissions:
```bash
ls -la data/config.json
```

### Models not available

For local models:
```bash
ollama list
ollama pull llama3.2
```

For online models, check your API subscription includes the model.

### Cache not working

Check cache structure in `analyze.mime_type_cache`.
Verify timestamps are recent.
Clear cache and let it rebuild if corrupted.

## See Also

- [Main README](../README.md) - Project overview
- [Analyze Command Guide](ANALYZE_COMMAND.md) - Detailed analyze command documentation
- [AI Proposal Guide](AI_PROPOSAL.md) - Structure proposal feature
