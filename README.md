# Airganizer

An AI-powered file system organizing tool that analyzes and organizes files based on their metadata and content.

## Features

### Phase 1: File Analysis ✅
- **Recursive directory enumeration** - Scans all files in a directory tree
- **Detailed file metadata extraction** - Captures file path, name, exact MIME type, encoding, and size
- **Binwalk analysis** - Deep binary analysis of files (optional)
- **JSON export** - Saves all metadata in structured JSON format
- **Summary statistics** - Provides overview of file types and sizes

### Phase 2: AI Structure Proposal ✅
- **AI-powered structure generation** - Uses GPT-4/Claude to propose organizational structures
- **Iterative refinement** - Processes files in chunks and evolves structure
- **Intelligent categorization** - Analyzes file types and purposes
- **Rationale tracking** - Explains organizational decisions
- **Flexible providers** - Supports OpenAI and Anthropic Claude

### Phase 3: AI Model Recommendation ✅ NEW!
- **Intelligent model selection** - AI recommends which analysis models to use for each file
- **Local & online AI support** - Choose between cloud APIs (OpenAI/Anthropic) or local models (Ollama)
- **Smart caching** - Reduces API costs by caching recommendations by MIME type
- **Explicit mappings** - Manually configure which models to use for specific file types
- **Model registry** - Tracks available models and their capabilities
- **Auto-download** - Optionally download required local models automatically
- **Resource-aware** - Automatically detects system RAM/CPU/GPU and filters suitable models
- **Dynamic loading** - Load and unload models on-demand to optimize memory usage (NEW!)

## Project Structure

```
airganizer/
├── src/
│   ├── core/              # Core functionality
│   │   ├── scanner.py     # File enumeration
│   │   ├── metadata_collector.py  # Metadata extraction
│   │   ├── storage.py     # Data persistence
│   │   └── models.py      # Data models for structures
│   ├── ai/                # AI integration
│   │   ├── client.py      # AI provider clients
│   │   ├── proposer.py    # Structure proposal logic
│   │   └── prompts.py     # AI prompt templates
│   ├── commands/          # CLI commands
│   ├── main.py            # CLI entry point
│   └── config.py          # Configuration management
├── examples/              # Usage examples
├── docs/                  # Documentation
├── test_data/            # Sample test files
├── data/                 # Output storage
└── requirements.txt      # Python dependencies
```
## Installation

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `python-magic` - MIME type detection
- `openai` - OpenAI API client (optional)
- `anthropic` - Anthropic Claude API client (optional)

### 2. (Optional) Install binwalk for deep binary analysis

```bash
# On Ubuntu/Debian
sudo apt-get install binwalk

# Or use the provided script
bash install_binwalk.sh
```

### 3. Set up AI API keys (for structure proposal)

```bash
# For OpenAI
export OPENAI_API_KEY='your-api-key-here'

# For Anthropic Claude
export ANTHROPIC_API_KEY='your-api-key-here'
```

## Usage

### Command 1: Scan Files

Scan a directory and collect comprehensive file metadata:

```bash
python -m src scan /path/to/directory
```

**Options:**
```bash
# Specify output file
python -m src scan /path/to/directory -o data/my_files.json

# Skip binwalk analysis (faster)
python -m src scan /path/to/directory --no-binwalk

# Verbose output
python -m src scan /path/to/directory -v
```

### Command 2: Propose Structure (NEW!)

Use AI to analyze files and propose an organizational structure:

```bash
# From previously scanned metadata
python -m src propose --metadata data/my_files.json

# Or scan directory directly
python -m src propose --directory /path/to/directory

# Use Anthropic Claude instead of OpenAI
python -m src propose --metadata data/my_files.json --provider anthropic

# Customize AI parameters
python -m src propose \
  --metadata data/my_files.json \
  --chunk-size 100 \
  --temperature 0.3 \
  -o data/structure.json
```

**Options:**
- `--metadata`: Use pre-scanned metadata JSON
- `--directory`: Scan directory on-the-fly
- `--provider`: AI provider (openai, anthropic, claude)
- `--chunk-size`: Files per AI call (default: 50)
- `--temperature`: AI creativity 0.0-1.0 (default: 0.3)
- `-o`: Output file (default: data/proposed_structure.json)

See [docs/AI_PROPOSAL.md](docs/AI_PROPOSAL.md) for detailed documentation.

### Command 3: Analyze & Recommend Models (NEW!)

Get AI-powered recommendations for which analysis models to use for each file:

```bash
# Analyze a directory and get model recommendations
python -m src analyze --directory /path/to/directory

# Or use pre-scanned metadata
python -m src analyze --metadata data/my_files.json

# Use specific AI provider
python -m src analyze --directory /path/to/directory --provider ollama
python -m src analyze --directory /path/to/directory --provider anthropic

# Specify output location
python -m src analyze \
  --metadata data/my_files.json \
  -o data/analysis_results.json
```

**Options:**
- `--metadata`: Use pre-scanned metadata JSON
- `--directory`: Scan and analyze directory directly
- `--provider`: AI provider (openai, anthropic, ollama)
- `-o`: Output file (default: data/analysis_results.json)

**Output includes:**
- Recommended models for each file
- Analysis types to perform (OCR, image analysis, etc.)
- Priority levels (high/medium/low)
- Rationale for each recommendation

See [PHASE3_COMPLETE.md](PHASE3_COMPLETE.md) for detailed documentation.

### Python API Usage

#### File Scanning
```python
from src.core import FileScanner, MetadataCollector, MetadataStore

# Scan a directory
scanner = FileScanner('/path/to/directory')

# Collect metadata
collector = MetadataCollector(use_binwalk=False)
store = MetadataStore(storage_path='data/output.json')

for file_path in scanner.scan():
    metadata = collector.collect_metadata(file_path)
    store.add_metadata(metadata)

# Save results
store.save()

# Get summary
summary = store.get_summary()
print(f"Scanned {summary['total_files']} files")
```

#### AI Structure Proposal
```python
from src.core import FileItem
from src.ai import create_structure_proposer

# Create file items (or load from metadata)
files = [
    FileItem("path/to/file.txt", "file.txt", "text/plain", 1024),
    # ... more files
]

# Create AI proposer
proposer = create_structure_proposer(provider='openai', chunk_size=50)

# Generate structure with progress tracking
def show_progress(chunk, total, msg):
    print(f"[{chunk}/{total}] {msg}")

structure = proposer.propose_structure(files, progress_callback=show_progress)

# Save and review
proposer.save_structure('data/structure.json')
summary = structure.get_summary()
```

#### AI Model Recommendations (NEW!)
```python
from src.core import FileScanner, MetadataCollector
from src.ai import create_model_recommender

# Scan and collect metadata
scanner = FileScanner('/path/to/directory')
collector = MetadataCollector(use_binwalk=False)

files = []
for file_path in scanner.scan():
    metadata = collector.collect_metadata(file_path)
    file_item = FileItem(
        file_path=str(file_path),
        file_name=file_path.name,
        mime_type=metadata.mime_type,
        file_size=metadata.file_size
    )
    files.append(file_item)

# Get AI recommendations
recommender = create_model_recommender(provider='openai')

def show_progress(batch_num, total, msg):
    print(f"[{batch_num}/{total}] {msg}")

recommendations = recommender.recommend_models(
    files,
    progress_callback=show_progress
)

# Review recommendations
for file in files:
    rec = recommendations[file.file_path]
    print(f"{file.file_name}:")
    print(f"  Model: {rec['primary_model']}")
    print(f"  Analysis: {', '.join(rec['analysis_types'])}")
    print(f"  Priority: {rec['priority']}")
```

## Complete Workflow

Here's the recommended end-to-end workflow:

```bash
# Step 1: Scan your files and collect metadata
python -m src scan /path/to/messy/directory -o data/files.json -v

# Step 2: Review the scan results
cat data/files.json | jq '.total_files, .files[] | .mime_type' | sort | uniq -c

# Step 3: Use AI to propose an organizational structure
export OPENAI_API_KEY='your-key'
python -m src propose --metadata data/files.json -o data/structure.json

# Step 4: Get AI recommendations for which models to use for analysis (NEW!)
python -m src analyze --metadata data/files.json -o data/analysis.json

# Step 5: Review the analysis recommendations
cat data/analysis.json | jq '.summary'
```
python -m src propose --metadata data/files.json -o data/structure.json

# Step 4: Review the proposed structure
cat data/structure.json | jq '.root.subdirectories[].name'

# Next phases (coming soon):
# Step 5: Refine structure with AI analyzing file contents
# Step 6: Assign files to directories
# Step 7: Actually organize the files
```

## Output Formats

### Metadata Output (from scan command)

The scan command generates a JSON file with file metadata:

```json
{
  "scan_date": "2026-01-15T17:40:15.319755",
  "total_files": 3,
  "files": [
    {
      "file_path": "/path/to/file.py",
      "file_name": "file.py",
      "mime_type": "text/x-script.python",
      "mime_encoding": "us-ascii",
      "file_size": 156,
      "binwalk_output": null,
      "error": null
    }
  ]
}
```

### Proposed Structure Output (from propose command)

The propose command generates a hierarchical structure:

```json
{
  "root": {
    "name": "organized",
    "description": "Root directory for organized files",
    "path": "/organized",
    "subdirectories": [
      {
        "name": "documents",
        "description": "Text documents and PDFs",
        "path": "/organized/documents",
        "subdirectories": [],
        "files": [],
        "rationale": "Group text-based content"
      }
    ],
    "files": [],
    "rationale": "Organize by file type and purpose"
  },
  "metadata": {
    "total_files_analyzed": 150
  },
  "processing_stats": {
    "chunk_size": 50,
    "total_chunks": 3
  }
}
```

## Examples

### Example 1: Basic Scan

```bash
# Scan the test data
python -m src scan test_data -v

# Output:
# 🔍 Scanning directory: test_data
# ------------------------------------------------------------
# Found 3 files to analyze
#
# Processing: sample_doc.md
# Processing: sample_script.py
# Processing: sample_config.json
#
# ✅ Processed 3 files
#
# 💾 Metadata saved to: data/metadata.json
#
# 📊 Summary:
# ------------------------------------------------------------
# Total files:     3
# Total size:      0.0 MB
#
# MIME types found:
#   text/plain                               1 files
#   text/x-script.python                     1 files
#   application/json                         1 files
```

### Example 2: AI Structure Proposal

```bash
# First scan
python -m src scan test_data -o data/test_files.json

# Then propose structure
export OPENAI_API_KEY='your-key'
python -m src propose --metadata data/test_files.json

# Output:
# 🤖 AI-Powered Structure Proposal
# ============================================================
# 
# 📂 Loading files...
# ✓ Loaded 3 files from metadata: data/test_files.json
# 
# 🔧 Initializing AI (openai)...
# ✓ AI client initialized
# 
# 🎯 Generating organizational structure...
#    Files to process: 3
#    Chunk size: 50
# 
# ⏳ [100.0%] Processing chunk 1/1...
# 
# 💾 Saving proposed structure...
# ✓ Structure saved to: data/proposed_structure.json
# 
# 📊 Proposal Summary:
# ============================================================
# Total directories proposed: 4
# 
# 📁 Proposed Structure Overview:
# ============================================================
# └── organized/
#     ↳ Root directory for organized files
#     ├── documents/
#     │   ↳ Text files and documentation
#     ├── code/
#     │   ↳ Source code and scripts
#     └── data/
#         ↳ Configuration and data files
```

## Configuration

Airganizer uses a configuration file located at `~/.config/airganizer/config.json`.

### AI Configuration

Configure which AI provider to use:

```bash
# Use online AI (OpenAI or Anthropic)
export OPENAI_API_KEY='your-key'
# or
export ANTHROPIC_API_KEY='your-key'

# Use local AI (Ollama)
# 1. Install Ollama: https://ollama.ai
# 2. Pull a model: ollama pull llama3.2
# 3. Configure Airganizer (coming soon):
#    python -m src config set ai.mode local
#    python -m src config set ai.local.ollama_model llama3.2
```

### Model Selection

Configure which analysis models to use:

```json
{
  "models": {
    "auto_download": false,
    "explicit_mapping": {
      "image/jpeg": "gpt-4o-vision",
      "image/png": "gpt-4o-vision",
      "text/x-script.python": "claude-3-5-sonnet",
      "text/plain": "claude-3-5-sonnet"
    }
  }
}
```

### Available Configuration Options

- `ai.mode` - "online" or "local"
- `ai.default_provider` - "openai", "anthropic", or "ollama"
- `ai.local.ollama_host` - Ollama server URL (default: http://localhost:11434)
- `ai.local.ollama_model` - Default Ollama model
- `models.auto_download` - Auto-download required models (for local mode)
- `models.explicit_mapping` - Map MIME types to specific models
- `analyze.ask_ai_for_models` - Use AI to recommend models (default: true)

## Documentation

- [DYNAMIC_LOADING.md](DYNAMIC_LOADING.md) - **NEW!** Dynamic model loading and memory management
- [RESOURCE_AWARE.md](RESOURCE_AWARE.md) - Resource-aware model selection guide
- [PHASE3_COMPLETE.md](PHASE3_COMPLETE.md) - AI model recommendation system guide
- [AI_PROPOSAL.md](docs/AI_PROPOSAL.md) - Detailed guide for AI structure proposal
- [OVERVIEW.md](OVERVIEW.md) - Technical architecture and design
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - File organization reference

## Roadmap

### ✅ Phase 1: File Analysis (Complete)
- Recursive directory scanning
- MIME type detection
- Metadata collection
- Binwalk integration

### ✅ Phase 2: AI Structure Proposal (Complete)
- AI-powered structure generation
- Iterative refinement
- Multiple AI provider support

### ✅ Phase 3: AI Model Recommendation (Complete)
- AI recommends which models to use for each file
- Support for online and local AI
- Smart caching and explicit mappings
- Model registry and availability tracking

### 📋 Phase 4: File Analysis Execution (Next)
- Execute recommended models on files
- Extract structured data
- Generate analysis reports
- Multi-model analysis support

### 📋 Phase 5: Content Analysis & Refinement (Planned)
- AI analysis of file contents
- Semantic similarity detection
- Relationship discovery
- Structure refinement

### 📋 Phase 6: File Assignment (Planned)
- Assign files to proposed directories
- Handle conflicts and duplicates
- Generate organization preview

### 📋 Phase 5: Execution (Planned)
- Actually move/copy files
- Preserve metadata
- Undo capability
- Dry-run mode

## Next Steps

This is the foundation for the AI file organizing tool. Future features will include:

- AI-powered file categorization
- Automatic organization based on content
- Duplicate file detection
- Smart tagging and search
- Content-based file clustering
