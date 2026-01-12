# Airganizer

An AI-powered file organizing system that helps you automatically organize and manage your files.

## Features

- **Recursive directory scanning** - Scan any directory and all subdirectories
- **AI-powered organization** - Generate intelligent directory structures using AI
- **Multiple AI providers** - Support for OpenAI, Anthropic Claude, and local Ollama models
- **GPU acceleration** - Local AI support with GPU and Apple Metal
- **Chunked processing** - Efficiently handle large directory trees
- **Configurable** - Customize AI provider, models, and chunk sizes

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

This creates `.airganizer.json` with default settings. Edit it to configure your AI provider:

```json
{
  "ai_provider": "ollama",
  "chunk_size": 4000,
  "openai": {
    "api_key": "your-api-key-here",
    "model": "gpt-4"
  },
  "anthropic": {
    "api_key": "your-api-key-here",
    "model": "claude-3-5-sonnet-20241022"
  },
  "ollama": {
    "model": "llama2",
    "base_url": "http://localhost:11434"
  }
}
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

# Save structure to file
python -m airganizer.main /path/to/directory --organize --output structure.json

# Adjust chunk size
python -m airganizer.main /path/to/directory --organize --chunk-size 2000
```

## How It Works

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

