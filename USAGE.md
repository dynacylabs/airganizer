# Usage Guide

Complete guide for using AIrganizer to organize your files with AI.

## Table of Contents

- [Quick Start](#quick-start)
- [Command-Line Reference](#command-line-reference)
- [Usage Examples](#usage-examples)
- [Pipeline Stages](#pipeline-stages)
- [Cache Management](#cache-management)
- [Progress Tracking](#progress-tracking)
- [Output Files](#output-files)
- [Common Workflows](#common-workflows)

## Quick Start

### Minimal Example

```bash
# Set API key (if using online models)
export OPENAI_API_KEY="your-key-here"

# Run the pipeline
python main.py \
  --config config.yaml \
  --src /path/to/source \
  --dst /path/to/destination
```

### Test Run (10 files)

```bash
python main.py \
  --config config.yaml \
  --src /path/to/test/folder \
  --dst /path/to/output \
  --max-files 10 \
  --verbose
```

## Command-Line Reference

### Required Arguments

| Argument | Description |
|----------|-------------|
| `--config PATH` | Path to YAML configuration file |
| `--src PATH` | Source directory containing files to organize |
| `--dst PATH` | Destination directory for organized files |

### Output Options

| Argument | Description |
|----------|-------------|
| `--output PATH` | Save complete pipeline results to JSON file |
| `--stage1-output PATH` | Save Stage 1 results only (scan + metadata) |
| `--stage3-output PATH` | Save unified results (all stages combined) |
| `--stage4-output PATH` | Save Stage 4 results (taxonomy structure) |
| `--stage5-output PATH` | Save Stage 5 results (move operations) |

### Stage Control

| Argument | Description |
|----------|-------------|
| `--skip-stage3` | Skip AI analysis stage |
| `--skip-stage4` | Skip taxonomy generation stage |
| `--skip-stage5` | Skip file moving stage |
| `--max-files N` | Process only first N files (for testing) |
| `--dry-run` | Preview operations without moving files |

### Cache Options

| Argument | Description |
|----------|-------------|
| `--no-cache` | Disable cache completely (start fresh) |
| `--clear-cache [STAGE]` | Clear cache before running. Options: `all`, `stage1`, `stage2`, `stage3`, `stage4`, `stage5` |
| `--cache-dir PATH` | Override cache directory location |
| `--cache-stats` | Display cache statistics and exit |

### Other Options

| Argument | Description |
|----------|-------------|
| `--verbose` | Enable verbose output (DEBUG level) |
| `--quiet` | Minimal output (errors only) |
| `--help` | Show help message |

## Usage Examples

### 1. Full Pipeline with Online Models

```bash
# Set API keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Run complete pipeline
python main.py \
  --config config.yaml \
  --src ~/Downloads \
  --dst ~/Organized \
  --output results.json \
  --verbose
```

**What happens:**
1. Scans all files in ~/Downloads
2. Discovers available AI models (GPT-4, Claude, etc.)
3. Analyzes each file with the appropriate AI model
4. Generates hierarchical taxonomy structure
5. Moves files to organized locations in ~/Organized

### 2. Privacy Mode (Local Models Only)

```bash
# Make sure Ollama is running
ollama serve

# Download required models
ollama pull llama3.2-vision
ollama pull llava

# Run with local models
python main.py \
  --config config_local.yaml \
  --src ~/Documents \
  --dst ~/Organized \
  --verbose
```

**config_local.yaml:**
```yaml
models:
  model_mode: "local_only"
  discovery_method: "auto"
  ollama:
    auto_enumerate: true
```

### 3. Test Run (Limited Files)

```bash
# Process only 10 files to test configuration
python main.py \
  --config config.yaml \
  --src ~/test_folder \
  --dst ~/test_output \
  --max-files 10 \
  --verbose
```

**Use case:** Testing configuration before processing thousands of files.

### 4. Dry Run (Preview Mode)

```bash
# See what would happen without moving files
python main.py \
  --config config.yaml \
  --src ~/Downloads \
  --dst ~/Organized \
  --dry-run \
  --output preview.json
```

**Result:** Shows planned taxonomy and file moves, but doesn't actually move files.

### 5. Resume from Interruption

```bash
# First run (interrupted)
python main.py --config config.yaml --src ~/files --dst ~/organized
# ... process interrupted ...

# Second run (resumes automatically)
python main.py --config config.yaml --src ~/files --dst ~/organized
# Picks up where it left off!
```

**Cache benefits:**
- Stages 1-2: Already scanned files and discovered models
- Stage 3: Already analyzed files are skipped
- Stage 4: Taxonomy already generated
- Stage 5: Only remaining moves are executed

### 6. Start Fresh (Clear Cache)

```bash
# Clear all cache and start over
python main.py \
  --config config.yaml \
  --src ~/files \
  --dst ~/organized \
  --clear-cache all
```

### 7. Clear Specific Stage Cache

```bash
# Re-run only Stage 3 (AI analysis)
python main.py \
  --config config.yaml \
  --src ~/files \
  --dst ~/organized \
  --clear-cache stage3
```

### 8. Mixed Mode (Online + Local)

```bash
# Use GPT-4 for text, local models for images
export OPENAI_API_KEY="sk-..."

python main.py \
  --config config_mixed.yaml \
  --src ~/files \
  --dst ~/organized
```

**config_mixed.yaml:**
```yaml
models:
  model_mode: "mixed"
  discovery_method: "auto"
  openai:
    api_key_env: "OPENAI_API_KEY"
    auto_enumerate: true
  ollama:
    auto_enumerate: true
```

### 9. Check Cache Status

```bash
# View what's in cache without running pipeline
python main.py \
  --config config.yaml \
  --src ~/files \
  --dst ~/organized \
  --cache-stats
```

**Output:**
```
Cache Statistics:
  Directory: .cache_airganizer
  Stage 1: 1,234 files scanned
  Stage 2: 15 models mapped
  Stage 3: 856 files analyzed
  Stage 4: Taxonomy generated
  Stage 5: 234 files moved
```

### 10. Skip Stages (Partial Pipeline)

```bash
# Only scan and analyze (skip organization)
python main.py \
  --config config.yaml \
  --src ~/files \
  --dst ~/organized \
  --skip-stage4 \
  --skip-stage5 \
  --stage3-output analysis_only.json
```

## Pipeline Stages

### Stage 1: File Scanning

**What it does:**
- Recursively scans source directory
- Extracts metadata (EXIF, dimensions, etc.)
- Identifies MIME types
- Respects exclusion rules

**Output:**
- List of all discovered files
- Metadata for each file
- Unique MIME types found

**Cache:** Scan results, metadata

### Stage 2: AI Model Discovery

**What it does:**
- Discovers available AI models
- Maps MIME types to best models
- Tests model connectivity
- Downloads local models (if needed)

**Output:**
- List of available models
- MIME-to-model mapping
- Connectivity status

**Cache:** Model list, mapping

### Stage 3: AI-Powered Analysis

**What it does:**
- Analyzes each file with assigned AI model
- Generates proposed filename
- Creates description and tags

**Output:**
- Proposed filename for each file
- Content description
- Categorization tags

**Cache:** Analysis results per file

### Stage 4: Taxonomy Generation

**What it does:**
- Creates hierarchical directory structure
- Assigns files to categories
- Provides reasoning for assignments

**Output:**
- Multi-level taxonomy tree
- File-to-category mappings
- Assignment reasoning

**Cache:** Taxonomy structure, assignments

### Stage 5: File Organization

**What it does:**
- Moves files to organized locations
- Handles filename conflicts
- Logs excluded files and errors
- Supports dry-run mode

**Output:**
- Organized files in destination
- Excluded files log
- Error files log
- Move operation summary

**Cache:** Move operations, resolutions

## Cache Management

### Cache Behavior

- **Permanent:** No expiration - cache is valid until cleared
- **Automatic:** No configuration needed
- **Resumable:** Pipeline resumes from where it left off
- **Stage-specific:** Each stage caches independently

### Cache Operations

**View cache stats:**
```bash
python main.py --config config.yaml --src ~/files --dst ~/organized --cache-stats
```

**Clear all cache:**
```bash
python main.py --config config.yaml --src ~/files --dst ~/organized --clear-cache all
```

**Clear specific stage:**
```bash
python main.py --config config.yaml --src ~/files --dst ~/organized --clear-cache stage3
```

**Disable cache:**
```bash
python main.py --config config.yaml --src ~/files --dst ~/organized --no-cache
```

**Custom cache directory:**
```bash
python main.py --config config.yaml --src ~/files --dst ~/organized --cache-dir /tmp/my_cache
```

### When to Clear Cache

- **Source directory changed:** Clear Stage 1
- **AI models changed:** Clear Stage 2
- **Want different analysis:** Clear Stage 3
- **Want different taxonomy:** Clear Stage 4
- **Start completely fresh:** Clear all

## Progress Tracking

### Dual Progress Bars

```
Stage 3: AI Analysis ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 45/100 files (45%)
📄 Analyzing: vacation_photo_2023.jpg

Overall Progress    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 58% complete
```

**Top bar:** Current stage progress with file count  
**Bottom bar:** Overall pipeline completion  
**File info:** Currently processing file

### Behavior

- **Automatic:** Enabled by default
- **Debug mode:** Disabled when `--verbose` is used (for clean logs)
- **Refresh rate:** 4 updates per second
- **Stage-specific:** Each stage shows relevant progress

### Stage-Specific Progress

- **Stage 1:** Files scanned
- **Stage 2:** Models discovered
- **Stage 3:** Files analyzed
- **Stage 4:** Categories processed
- **Stage 5:** Files moved

## Output Files

### Complete Results (--output)

```json
{
  "stage1": { /* scan results */ },
  "stage2": { /* model mapping */ },
  "stage3": { /* AI analysis */ },
  "stage4": { /* taxonomy */ },
  "stage5": { /* move operations */ }
}
```

### Stage 3 Output (--stage3-output)

```json
{
  "source_directory": "/path/to/source",
  "total_files": 100,
  "files": [
    {
      "file_name": "IMG_1234.jpg",
      "file_path": "/path/to/source/IMG_1234.jpg",
      "mime_type": "image/jpeg",
      "proposed_filename": "family_vacation_beach_sunset.jpg",
      "description": "Beach sunset photo with family...",
      "tags": ["vacation", "beach", "sunset", "family"]
    }
  ]
}
```

### Stage 4 Output (--stage4-output)

```json
{
  "taxonomy": {
    "Photos": {
      "Vacation": {
        "Beach 2023": []
      },
      "Family": []
    },
    "Documents": {
      "Work": [],
      "Personal": []
    }
  },
  "assignments": {
    "IMG_1234.jpg": "Photos/Vacation/Beach 2023"
  }
}
```

## Common Workflows

### Workflow 1: Photo Library Organization

```bash
# 1. Test with 20 photos first
python main.py --config config.yaml --src ~/Photos --dst ~/Organized_Photos --max-files 20 --verbose

# 2. Review results, adjust config if needed

# 3. Run full organization
python main.py --config config.yaml --src ~/Photos --dst ~/Organized_Photos
```

### Workflow 2: Document Cleanup

```bash
# 1. Scan and analyze (no moving yet)
python main.py --config config.yaml --src ~/Documents --dst ~/Organized_Docs --skip-stage5 --output analysis.json

# 2. Review taxonomy in analysis.json

# 3. Complete organization
python main.py --config config.yaml --src ~/Documents --dst ~/Organized_Docs
```

### Workflow 3: Privacy-Focused Organization

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Download models
ollama pull llama3.2-vision
ollama pull llava

# 3. Run with local models only
python main.py --config config_local.yaml --src ~/sensitive_files --dst ~/organized
```

### Workflow 4: Incremental Processing

```bash
# Day 1: Process first batch
python main.py --config config.yaml --src ~/Downloads --dst ~/Organized

# Day 2: Add more files to ~/Downloads, run again
python main.py --config config.yaml --src ~/Downloads --dst ~/Organized
# Only new files are processed!
```

### Workflow 5: Mixed Provider Strategy

```bash
# Use GPT-4 for important documents, local models for images
python main.py --config config_mixed.yaml --src ~/files --dst ~/organized
```

**config_mixed.yaml:**
```yaml
models:
  model_mode: "mixed"
  discovery_method: "auto"
  openai:
    api_key_env: "OPENAI_API_KEY"
    models: ["gpt-4o"]  # For text/documents
  ollama:
    auto_enumerate: true  # For images
```

## Troubleshooting

### Issue: Files not being analyzed

**Solution:** Check `--max-files` limit or exclusion rules in config

### Issue: Progress bars not showing

**Solution:** Progress bars auto-disable in verbose/debug mode. Remove `--verbose` flag.

### Issue: Cache not resuming

**Solution:** Ensure same `--src`, `--dst`, and `--cache-dir` paths

### Issue: Model not found

**Solution:** 
```bash
# For local models
ollama list  # Check installed models
ollama pull <model-name>  # Install missing model

# For online models
export OPENAI_API_KEY="..."  # Check API key is set
```

### Issue: Out of memory

**Solution:** Use `--max-files` to process in batches:
```bash
# Process 100 files at a time
python main.py --config config.yaml --src ~/files --dst ~/organized --max-files 100
```

## Best Practices

1. **Start small:** Use `--max-files 10` to test configuration
2. **Review output:** Check JSON output before full run
3. **Use dry-run:** Preview with `--dry-run` first
4. **Clear cache wisely:** Only clear when necessary
5. **Monitor progress:** Let progress bars guide you
6. **Save outputs:** Use `--output` to save results for review
7. **Test locally first:** Use Ollama for free testing before using paid APIs
8. **Backup important files:** Always keep backups before organizing
