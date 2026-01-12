# Airganizer Quick Start Guide

## Installation

1. Clone the repository
2. Install dependencies (optional AI providers):
   ```bash
   pip install openai      # For OpenAI
   pip install anthropic   # For Anthropic Claude
   pip install ollama      # For local Ollama
   ```

## Quick Commands

### Basic Scanning
```bash
# List all files
python -m airganizer.main /path/to/directory

# Verbose mode
python -m airganizer.main /path/to/directory -v
```

### Generate File Tree
```bash
# View tree
python -m airganizer.main /path/to/directory --tree

# Save tree
python -m airganizer.main /path/to/directory --tree --output tree.json
```

### AI Organization (Phase 1)
```bash
# Initialize config
python -m airganizer.main . --init-config

# Edit .airganizer.json with your AI provider settings

# Generate structure
python -m airganizer.main /path/to/directory --organize

# Save structure
python -m airganizer.main /path/to/directory --organize --output structure.json
```

## Configuration Example

`.airganizer.yaml`:
```yaml
# Airganizer Configuration File

# AI provider to use: 'openai', 'anthropic', or 'ollama'
ai_provider: ollama

# Maximum chunk size in characters
chunk_size: 4000

# Ollama (local AI) configuration
ollama:
  model: llama2
  base_url: http://localhost:11434
```

## AI Providers

### Ollama (Local, Free)
1. Install Ollama: https://ollama.ai
2. Pull a model: `ollama pull llama2`
3. Run Ollama: `ollama serve`
4. Set provider to "ollama" in config

### OpenAI (Cloud, Paid)
1. Get API key from https://platform.openai.com
2. Set `OPENAI_API_KEY` environment variable
3. Set provider to "openai" in config

### Anthropic (Cloud, Paid)
1. Get API key from https://console.anthropic.com
2. Set `ANTHROPIC_API_KEY` environment variable
3. Set provider to "anthropic" in config

## Demo

Run the demo to see chunking in action:
```bash
python demo.py
```

## Current Phase: Structure Generation

- ✅ Scan directories recursively
- ✅ Build hierarchical file tree
- ✅ Chunk tree for AI processing
- ✅ Generate theoretical directory structure
- ⏳ File routing (coming next)
- ⏳ File analysis (future)
- ⏳ File placement (future)
- ⏳ Execution (future)
