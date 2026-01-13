# Airganizer

An AI-powered file organizing system that helps you automatically organize and manage your files.

## Features

- **Recursive directory scanning** - Scan any directory and all subdirectories
- **AI-powered organization** - Generate intelligent directory structures using AI
- **Multiple AI providers** - Support for OpenAI, Anthropic Claude, and local Ollama models
- **Multiple data formats** - JSON, path list, or compact formats for efficient processing
- **GPU acceleration** - Local AI support with GPU and Apple Metal
- **Chunked processing** - Efficiently handle large directory trees
- **Configurable** - Customize AI provider, models, chunk sizes, and data formats

## Installation

```bash
pip install -r requirements.txt
```

### AI Provider Setup

Install the AI provider you want to use:

```bash
# For OpenAI
pip install openai

# For Anthropic Claude
pip install anthropic

# For Ollama (local AI)
pip install ollama
# Also install and run Ollama: https://ollama.ai
```

## Configuration

Create a configuration file:

```bash
python -m airganizer.main /path/to/directory --init-config
```

This creates `.airganizer.yaml` with default settings. Edit it to configure your AI provider:

```yaml
# Airganizer Configuration File
# Edit this file to configure your AI provider and settings

# AI provider to use: 'openai', 'anthropic', or 'ollama'
ai_provider: ollama

# Maximum chunk size in characters
chunk_size: 4000

# Format for file tree data: 'json', 'pathlist', or 'compact'
# - json: Full hierarchical structure (default, most detailed)
# - pathlist: Simple newline-separated paths (60% smaller, recommended)
# - compact: Indented format (similar to 'tree' command)
format: pathlist

# OpenAI configuration
openai:
  api_key: ''  # Or set OPENAI_API_KEY environment variable
  model: gpt-4

# Anthropic configuration
anthropic:
  api_key: ''  # Or set ANTHROPIC_API_KEY environment variable
  model: claude-3-5-sonnet-20241022

# Ollama (local AI) configuration
ollama:
  model: llama2
  base_url: http://localhost:11434
```
```

You can also use environment variables:
- `OPENAI_API_KEY` for OpenAI
- `ANTHROPIC_API_KEY` for Anthropic

## Usage

### Scan and list files

```bash
python -m airganizer.main /path/to/directory
python -m airganizer.main /path/to/directory -v  # verbose mode
```

### Generate file tree structure

```bash
# Output to console
python -m airganizer.main /path/to/directory --tree

# Save to file
python -m airganizer.main /path/to/directory --tree --output tree.json
```

### Generate organized directory structure (AI)

```bash
# Using configured AI provider
python -m airganizer.main /path/to/directory --organize

# Specify provider
python -m airganizer.main /path/to/directory --organize --provider ollama

# Specify data format (pathlist is 60% smaller than JSON)
python -m airganizer.main /path/to/directory --organize --format pathlist

# Save structure to file
python -m airganizer.main /path/to/directory --organize --output structure.json

# Adjust chunk size (recommended: 80K-500K for large datasets)
python -m airganizer.main /path/to/directory --organize --chunk-size 80000

# Full optimization for large datasets
python -m airganizer.main /path/to/directory --organize --format pathlist --chunk-size 80000
```

## How It Works

### Data Format Options

Airganizer supports three formats for sending file trees to AI:

**JSON Format (json)** - Default hierarchical structure
```json
{
  "dirs": {
    "documents": {
      "dirs": {},
      "files": ["report.pdf", "notes.txt"]
    }
  },
  "files": []
}
```

**Path List Format (pathlist)** - Simple newline-separated paths (recommended)
```
documents/report.pdf
documents/notes.txt
photos/vacation.jpg
```
- 60% smaller than JSON
- Faster to parse
- Reduces chunks from 560K to ~222K for large datasets
- Recommended for datasets over 10GB

**Compact Format (compact)** - Indented structure
```
documents/:
  files: report.pdf, notes.txt
photos/:
  files: vacation.jpg
```

**Performance comparison for 650GB dataset:**
- JSON with 4K chunks: 560,000 chunks = 16 days
- Path list with 4K chunks: 222,000 chunks = 6 days (2.5x faster)
- Path list with 80K chunks: 11,000 chunks = 15 hours (25x faster!)

### Phase 1: Structure Generation (Current)

1. **Scan** - Recursively scan the directory to find all files
2. **Build Tree** - Create a hierarchical JSON representation
3. **Chunk** - Split the tree into manageable chunks
4. **AI Analysis** - Iteratively feed chunks to AI with current structure
5. **Structure Evolution** - AI refines the theoretical directory structure with each chunk
6. **Output** - Final organized directory structure (folders only, no file placement yet)

### Future Phases

- **Phase 2**: Router - Determine best AI model for each file type
- **Phase 3**: File Analysis - Deep analysis of individual files
- **Phase 4**: Final Placement - Place files in the organized structure
- **Phase 5**: Execution - Actually move/organize the files

## Development

This project is structured for scalability and modularity as it grows into a comprehensive file organization tool.

### Project Structure

```
airganizer/
├── __init__.py          # Package initialization
├── main.py              # CLI entry point
├── scanner.py           # Directory scanning
├── chunker.py           # Tree chunking logic
├── ai_providers.py      # AI provider abstractions
├── organizer.py         # Structure generation orchestrator
└── config.py            # Configuration management
```

