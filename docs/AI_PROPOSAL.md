# AI-Powered Structure Proposal

## Overview

Airganizer now includes AI-powered capabilities to automatically propose organizational structures for your files. The AI analyzes file paths, names, and MIME types to suggest a logical directory hierarchy.

## How It Works

1. **File Analysis**: The system collects information about all files (paths, names, MIME types)
2. **Chunking**: Files are processed in chunks to stay within AI token limits
3. **Iterative Proposal**: The AI builds and refines the structure across multiple chunks
4. **Structure Evolution**: Each chunk allows the AI to:
   - Add new categories as needed
   - Refine existing categories
   - Reorganize based on emerging patterns
   - Update rationales

## Usage

### Step 1: Scan Your Files

First, collect metadata about your files:

```bash
python -m src scan /path/to/directory -o data/my_files.json
```

### Step 2: Generate AI Proposal

Use the metadata to generate an organizational structure:

```bash
# Using OpenAI (requires OPENAI_API_KEY)
export OPENAI_API_KEY='your-key-here'
python -m src propose --metadata data/my_files.json

# Using Anthropic Claude (requires ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY='your-key-here'
python -m src propose --metadata data/my_files.json --provider anthropic
```

### Alternative: Direct Directory Scan

You can also propose directly from a directory without pre-scanning:

```bash
python -m src propose --directory /path/to/directory
```

### Advanced Options

```bash
# Customize chunk size (files per AI call)
python -m src propose --metadata data/files.json --chunk-size 100

# Adjust AI creativity (0.0 = deterministic, 1.0 = creative)
python -m src propose --metadata data/files.json --temperature 0.5

# Custom output location
python -m src propose --metadata data/files.json -o data/custom_structure.json
```

## Configuration

### API Keys

Set your AI provider API key as an environment variable:

```bash
# OpenAI
export OPENAI_API_KEY='sk-...'

# Anthropic Claude
export ANTHROPIC_API_KEY='sk-ant-...'
```

### Installation

Install required AI libraries:

```bash
# For OpenAI
pip install openai

# For Anthropic Claude
pip install anthropic

# Or install both
pip install openai anthropic
```

## Output Format

The AI generates a JSON structure like this:

```json
{
  "root": {
    "name": "organized",
    "description": "Root directory for organized files",
    "path": "/organized",
    "subdirectories": [
      {
        "name": "documents",
        "description": "Text documents, PDFs, and office files",
        "path": "/organized/documents",
        "subdirectories": [
          {
            "name": "reports",
            "description": "Business reports and analytics",
            "path": "/organized/documents/reports",
            "subdirectories": [],
            "files": [],
            "rationale": "Group related business documents together"
          }
        ],
        "files": [],
        "rationale": "Separate documents from other file types"
      },
      {
        "name": "media",
        "description": "Images, videos, and audio files",
        "path": "/organized/media",
        "subdirectories": [],
        "files": [],
        "rationale": "Centralize all media content"
      }
    ],
    "files": [],
    "rationale": "Organize files by type and purpose for easy navigation"
  },
  "metadata": {
    "total_files_analyzed": 150
  },
  "processing_stats": {
    "chunk_size": 50,
    "total_chunks": 3,
    "temperature": 0.3
  },
  "created_at": "2026-01-15T18:30:00.000000",
  "last_updated": "2026-01-15T18:32:15.000000"
}
```

## Key Features

### Iterative Refinement

The AI processes files in chunks and updates its proposal with each chunk:

```
Chunk 1/3: Analyzes first 50 files → Creates initial structure
Chunk 2/3: Analyzes next 50 files → Refines and adds categories
Chunk 3/3: Analyzes last 50 files → Finalizes structure
```

### Context Preservation

Each chunk includes:
- Current proposed structure
- New files to analyze
- Ability to modify any part of the structure

### Rationale Tracking

Each directory includes a rationale explaining the organizational logic.

## Python API

Use the AI proposal system programmatically:

```python
from src.core import FileItem
from src.ai import create_structure_proposer

# Create file items
files = [
    FileItem("doc1.pdf", "doc1.pdf", "application/pdf", 1024),
    FileItem("photo.jpg", "photo.jpg", "image/jpeg", 512000),
    # ... more files
]

# Create proposer
proposer = create_structure_proposer(
    provider='openai',  # or 'anthropic'
    chunk_size=50,
    temperature=0.3
)

# Generate proposal with progress tracking
def progress(chunk_num, total_chunks, message):
    print(f"[{chunk_num}/{total_chunks}] {message}")

structure = proposer.propose_structure(files, progress_callback=progress)

# Save result
proposer.save_structure('data/structure.json')

# Get summary
summary = structure.get_summary()
print(f"Created {summary['total_directories']} directories")
```

## Best Practices

1. **Start with metadata**: Pre-scan files to include MIME types for better AI decisions
2. **Adjust chunk size**: Larger chunks = fewer AI calls but higher cost per call
3. **Lower temperature**: Use 0.1-0.3 for consistent, logical structures
4. **Review output**: Always review the AI's proposal before implementing
5. **Iterate**: Run multiple times with different settings if needed

## Limitations

- Initial proposal only creates structure (files not assigned yet)
- AI may not understand domain-specific file relationships
- Costs scale with number of files and chunk size
- Rate limits may apply based on your AI provider plan

## Next Steps

After generating a proposal:

1. Review the structure in the output JSON file
2. Later phases will:
   - Assign files to directories based on content
   - Refine the structure with more context
   - Actually organize files on disk

## Cost Considerations

- **OpenAI GPT-4**: ~$0.01-0.03 per 1000 files (varies by model)
- **Anthropic Claude**: ~$0.015-0.075 per 1000 files (varies by model)
- Chunk size affects number of API calls:
  - 100 files, chunk size 50 = 2 calls
  - 1000 files, chunk size 100 = 10 calls

## Troubleshooting

### "API key not found"
Set the appropriate environment variable:
```bash
export OPENAI_API_KEY='your-key'
# or
export ANTHROPIC_API_KEY='your-key'
```

### "Module not found: openai/anthropic"
Install the required library:
```bash
pip install openai anthropic
```

### "Failed to parse AI response"
The system will use a fallback structure. Try:
- Reducing chunk size
- Adjusting temperature
- Checking API rate limits

### High API costs
- Increase chunk size (fewer calls)
- Use lower-cost models
- Pre-filter files before proposal
