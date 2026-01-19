# Configurable Parameters Reference

This document lists all configurable parameters in the AI File Organizer.

## Overview

Every configurable parameter across all stages is now available in the `config.yaml` file. CLI arguments can override config file values.

---

## General Settings

**Section:** `general`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `log_level` | string | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `max_file_size` | int | `0` | Maximum file size in MB (0 = no limit) |
| `exclude_extensions` | list | `[]` | File extensions to exclude |
| `exclude_dirs` | list | `['.git', '__pycache__', ...]` | Directories to exclude from scanning |

---

## Stage 1 Settings (File Scanning)

**Section:** `stage1`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `recursive` | bool | `true` | Enable recursive directory scanning |
| `follow_symlinks` | bool | `false` | Follow symbolic links |
| `include_hidden` | bool | `false` | Include hidden files (starting with .) |

---

## Cache Settings

**Section:** `cache`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable caching |
| `directory` | string | `.airganizer_cache` | Cache directory location |
| `ttl_hours` | int | `24` | Cache time-to-live in hours |

---

## Model Settings

**Section:** `models`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_mode` | string | `mixed` | Model selection mode (local_only, online_only, mixed) |
| `discovery_method` | string | `auto` | Model discovery method (auto, config, local_download) |

**Provider Settings:**
- `openai.api_key_env`: Environment variable for OpenAI API key
- `anthropic.api_key_env`: Environment variable for Anthropic API key
- `ollama.base_url`: Ollama API base URL
- Each provider has `auto_enumerate` and `models` list settings

---

## Stage 3 Settings (AI File Analysis)

**Section:** `stage3`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_files` | int | `0` | Maximum files to analyze (0 = no limit) |
| `ai.temperature` | float | `0.3` | AI creativity (0.0-2.0, lower = more deterministic) |
| `ai.max_tokens` | int | `1000` | Maximum AI response length |
| `ai.timeout` | int | `60` | API request timeout in seconds |

**CLI Override:**
- `--max-files N`: Override max_files limit

**Usage:**
```yaml
stage3:
  max_files: 100  # Analyze only first 100 files
  ai:
    temperature: 0.3  # More deterministic
    max_tokens: 1000
    timeout: 60
```

---

## Stage 4 Settings (Taxonomic Structure Planning)

**Section:** `stage4`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `batch_size` | int | `100` | Files per batch for taxonomy generation |
| `ai.temperature` | float | `0.3` | AI creativity (0.0-2.0) |
| `ai.max_tokens` | int | `4000` | Maximum AI response length (larger for taxonomy) |
| `ai.timeout` | int | `120` | API request timeout in seconds |

**CLI Override:**
- `--batch-size N`: Override batch size

**Usage:**
```yaml
stage4:
  batch_size: 50  # Smaller batches for faster iteration
  ai:
    temperature: 0.3  # More deterministic categories
    max_tokens: 4000  # Large enough for complex taxonomies
    timeout: 120
```

---

## Stage 5 Settings (Physical File Organization)

**Section:** `stage5`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `overwrite` | bool | `false` | Overwrite existing files at destination |
| `dry_run` | bool | `false` | Simulate moves without actually moving files |

**CLI Override:**
- `--overwrite`: Enable overwrite
- `--dry-run`: Enable dry-run mode

**Usage:**
```yaml
stage5:
  overwrite: false  # Protect existing files
  dry_run: true     # Test run by default
```

---

## Mapping AI Settings (MIME to Model Mapping)

**Section:** `mapping`

Used for Stage 2's intelligent MIME type to AI model mapping.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ai.temperature` | float | `0.3` | AI creativity (0.0-2.0) |
| `ai.max_tokens` | int | `2000` | Maximum AI response length |
| `ai.timeout` | int | `60` | API request timeout in seconds |

**Usage:**
```yaml
mapping:
  ai:
    temperature: 0.3  # Consistent mapping decisions
    max_tokens: 2000
    timeout: 60
```

---

## Complete Example Configuration

```yaml
general:
  log_level: INFO
  max_file_size: 100  # 100 MB limit
  exclude_extensions: ['.tmp', '.swp']
  exclude_dirs: ['.git', '__pycache__', 'node_modules']

stage1:
  recursive: true
  follow_symlinks: false
  include_hidden: false

cache:
  enabled: true
  directory: .airganizer_cache
  ttl_hours: 24

stage3:
  max_files: 0  # No limit
  ai:
    temperature: 0.3
    max_tokens: 1000
    timeout: 60

stage4:
  batch_size: 100
  ai:
    temperature: 0.3
    max_tokens: 4000
    timeout: 120

stage5:
  overwrite: false
  dry_run: false

mapping:
  ai:
    temperature: 0.3
    max_tokens: 2000
    timeout: 60

models:
  model_mode: mixed
  discovery_method: auto
  # ... provider settings ...
```

---

## CLI Arguments Override Priority

CLI arguments always take precedence over config file values:

1. **CLI argument specified** → Use CLI value
2. **CLI argument not specified** → Use config file value
3. **Config file not specified** → Use code default

Example:
```bash
# Uses config file batch_size (e.g., 100)
python main.py --config config.yaml --src /input --dst /output

# Overrides config with CLI value (50)
python main.py --config config.yaml --src /input --dst /output --batch-size 50
```

---

## Parameter Recommendations

### For Production Use:
- `stage3.ai.temperature`: 0.3 (consistent analysis)
- `stage4.ai.temperature`: 0.3 (stable taxonomy)
- `stage5.dry_run`: false (actually move files)
- `stage5.overwrite`: false (protect existing files)
- `cache.enabled`: true (resume capability)

### For Testing:
- `stage3.max_files`: 10-20 (quick tests)
- `stage4.batch_size`: 10-20 (faster iteration)
- `stage5.dry_run`: true (safe testing)
- `general.log_level`: DEBUG (detailed output)

### For Creative Organization:
- `stage3.ai.temperature`: 0.5-0.7 (more creative descriptions)
- `stage4.ai.temperature`: 0.5-0.7 (more diverse categories)

### For Large Datasets:
- `stage4.batch_size`: 50-100 (balance context vs speed)
- `stage3.ai.timeout`: 120 (allow more time)
- `stage4.ai.timeout`: 180 (allow more time)
- `cache.enabled`: true (essential for resumption)

---

## Total Configurable Parameters

| Category | Count |
|----------|-------|
| General Settings | 4 |
| Stage 1 Settings | 3 |
| Cache Settings | 3 |
| Model Settings | 2+ (plus per-provider) |
| Stage 3 Settings | 4 |
| Stage 4 Settings | 4 |
| Stage 5 Settings | 2 |
| Mapping Settings | 3 |
| **Total** | **25+ parameters** |

Every aspect of the pipeline is now configurable!
