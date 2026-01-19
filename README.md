# AI File Organizer

An AI-powered file organizer that automatically scans, analyzes, and organizes files in your directories using intelligent AI model selection.

## Features

### Stage 1: File Scanning and Metadata Collection
- Recursively scan source directories
- Collect comprehensive file information:
  - File name, path, MIME type, size
  - EXIF data from images (camera, GPS, date, etc.)
  - File-specific metadata (dimensions, duration, page count, etc.)
  - Binwalk analysis for embedded data detection
- Extract unique MIME types from all scanned files
- Configurable exclusion rules for files and directories
- Hidden file handling
- Symbolic link support
- Error tracking and reporting

### Stage 2: AI Model Discovery and Mapping
- **AI Model Discovery** with multiple methods:
  - **Auto**: Automatically discover models from all providers (recommended)
  - **Config**: Use predefined models from configuration file
  - **Local Enumerate**: Automatically discover local AI models only
  - **Local Download**: Discover and download local models as needed
- **Centralized Credentials**: Specify API keys once per provider
- **Model Mode Selection**: Choose online-only, local-only, or mixed operation
- **Intelligent MIME-to-Model Mapping**: AI-powered recommendations for which model should analyze each file type
- **Automatic Model Download**: Downloads required models based on mapping (local_download mode)
- **Connectivity Verification**: Tests all models (local and online) to ensure readiness
- Support for both online (OpenAI, Anthropic) and local (Ollama) AI models

### Stage 3: AI-Powered File Analysis ✨ NEW
- Analyzes each file with its assigned AI model
- Generates for every file:
  - **Proposed filename**: Descriptive, meaningful name
  - **Description**: What's in the file (summary, contents, etc.)
  - **Tags**: Keywords for categorization
- Supports multiple AI providers:
  - **OpenAI**: GPT-4, GPT-4o with vision
  - **Anthropic**: Claude 3 family with vision
  - **Ollama**: Local models (LLaVA, Llama 3.2 Vision, etc.)
- Unified output combining all stages (metadata + mapping + analysis)
- Graceful error handling and retry logic
- Progress tracking and detailed logging

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd airganizer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install system dependencies:
```bash
# Ubuntu/Debian
sudo apt-get install libmagic1

# For local AI models (optional but recommended)
# Install Ollama from https://ollama.ai
curl -fsSL https://ollama.com/install.sh | sh
```

## Configuration

The configuration file (YAML format) allows you to customize all aspects of the file organizer. See [config.example.yaml](config.example.yaml) for a complete example.

**📚 For detailed configuration documentation, see [docs/CONFIGURATION.md](docs/CONFIGURATION.md)**

**⚡ Quick reference: [docs/CONFIG_QUICKREF.md](docs/CONFIG_QUICKREF.md)**

### New Configuration Features

#### Centralized Credentials
Specify API keys **once per provider** instead of per model:
```yaml
models:
  openai:
    api_key_env: "OPENAI_API_KEY"
  anthropic:
    api_key_env: "ANTHROPIC_API_KEY"
```

#### Model Mode Selection
Control which types of models to use:
- `online_only`: Use only OpenAI/Anthropic models
- `local_only`: Use only Ollama/local models
- `mixed`: Use both online and local models (default)

```yaml
models:
  model_mode: "mixed"  # online_only, local_only, or mixed
```

#### Automatic Model Discovery
Automatically enumerate available models from providers:
```yaml
models:
  discovery_method: "auto"
  
  openai:
    auto_enumerate: true
  
  anthropic:
    auto_enumerate: true
  
  ollama:
    auto_enumerate: true
```

### Key Configuration Sections

#### General Settings
- `log_level`: Logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `max_file_size`: Maximum file size to process in MB (0 = no limit)
- `exclude_extensions`: List of file extensions to exclude
- `exclude_dirs`: List of directory names to exclude

#### Stage 1 Settings
- `recursive`: Enable recursive directory scanning
- `follow_symlinks`: Follow symbolic links
- `include_hidden`: Include hidden files (files starting with .)

#### AI Model Configuration
- `model_mode`: Control which model types to use (`online_only`, `local_only`, `mixed`)
- `discovery_method`: How to discover models (`auto`, `config`, `local_enumerate`, `local_download`)
- `local_provider`: Local AI provider (`ollama`, `llamacpp`, `transformers`)
- Provider-specific configurations for `openai`, `anthropic`, and `ollama`
- `mapping_model`: AI model used to create MIME-to-model mappings

### Model Discovery Methods

**Auto-Discovery (Recommended - Zero Configuration)**
```yaml
models:
  model_mode: "mixed"
  discovery_method: "auto"
  
  openai:
    api_key_env: "OPENAI_API_KEY"
    auto_enumerate: true
  
  anthropic:
    api_key_env: "ANTHROPIC_API_KEY"
    auto_enumerate: true
  
  ollama:
    auto_enumerate: true
```

**Config-based (Manual Control)**
```yaml
models:
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

**Local Enumerate (Offline Use)**
```yaml
models:
  model_mode: "local_only"
  discovery_method: "local_enumerate"
  
  ollama:
    base_url: "http://localhost:11434"
```

**Local Download (Auto-Setup)**
```yaml
models:
  model_mode: "local_only"
  discovery_method: "local_download"
  
  ollama:
    auto_download_models:
      - "llama3.2-vision:latest"
      - "llava:latest"
```

Note: This method will also download any additional models required by the MIME-to-model mapping that aren't already installed.

## Usage

### Basic Usage

```bash
# Run all three stages (scan, map, analyze)
python main.py \
  --config config.example.yaml \
  --src /path/to/source \
  --dst /path/to/destination \
  --stage3-output results.json
```

### Command Line Arguments

**Required:**
- `--config`: Path to the configuration file (YAML format)
- `--src`: Source directory to scan for files
- `--dst`: Destination directory for organized files

**Output Options:**
- `--output`: Path to save complete results as JSON
- `--stage1-output`: Path to save Stage 1 results only
- `--stage3-output`: Path to save unified results (all stages combined)

**Stage Control:**
- `--skip-stage3`: Skip AI analysis (only run Stages 1 & 2)
- `--max-files N`: Analyze only first N files (testing)

**Cache Options:**
- `--no-cache`: Disable cache (process everything from scratch)
- `--clear-cache [all|stage1|stage2]`: Clear cache before running
- `--cache-dir PATH`: Override cache directory location
- `--cache-stats`: Display cache statistics and exit

**Other:**
- `--verbose`: Enable verbose output (DEBUG level logging)

### Examples

**Full workflow with online AI models:**
```bash
# Set API keys
export OPENAI_API_KEY="your-api-key"
export ANTHROPIC_API_KEY="your-api-key"

# Run complete analysis
python main.py \
  --config config.example.yaml \
  --src /home/user/Documents \
  --dst /home/user/Organized \
  --stage3-output unified_results.json \
  --verbose
```

**Test with limited files first:**
```bash
# Analyze only 10 files to test configuration
python main.py \
  --config config.example.yaml \
  --src /home/user/Documents \
  --dst /home/user/Organized \
  --max-files 10 \
  --stage3-output test_results.json
```

**With local Ollama models (privacy/offline):**
```bash
# Make sure Ollama is running
ollama serve

# Download vision-capable model
ollama pull llama3.2-vision

# Run with local models only
python main.py \
  --config config.example.yaml \
  --src /home/user/Documents \
  --dst /home/user/Organized \
  --stage3-output results.json
```

**Skip Stage 3 (only scan and map, no AI analysis):**
```bash
python main.py \
  --config config.example.yaml \
  --src /home/user/Documents \
  --dst /home/user/Organized \
  --skip-stage3 \
  --output mapping_results.json
```

## Project Structure

```
airganizer/
├── main.py                      # Main entry point
├── requirements.txt             # Python dependencies
├── config.example.yaml          # Example configuration file
├── src/
│   ├── config.py               # Configuration handler
│   ├── models.py               # Data models
│   ├── stage1.py               # Stage 1: File scanning
│   ├── stage2.py               # Stage 2: Model discovery
│   ├── stage3.py               # Stage 3: AI analysis
│   ├── ai_interface.py         # AI provider interface
│   ├── model_discovery.py      # Model discovery logic
│   ├── cache.py                # Cache management
│   └── ...
├── docs/
│   ├── CONFIGURATION.md        # Configuration guide
│   ├── STAGE3_GUIDE.md         # Stage 3 documentation
│   └── ...
└── tests/
│   ├── __init__.py
│   ├── config.py               # Configuration handler
│   ├── models.py               # Data models (FileInfo, ModelInfo, Stage1Result)
│   ├── stage1.py               # Stage 1 implementation
│   ├── model_discovery.py      # AI model discovery system
│   └── mime_mapper.py          # MIME-to-model mapping with AI
├── test_data/                  # Test files
└── README.md
```

## Stage 1 Output

Stage 1 produces a comprehensive `Stage1Result` object containing:

1. **File Information**: All scanned files with metadata
2. **Unique MIME Types**: List of all unique MIME types found
3. **Available Models**: List of discovered AI models with capabilities
4. **MIME-to-Model Mapping**: AI-recommended mapping of which model should analyze each file type

Example output structure:
```json
{
  "source_directory": "/path/to/source",
  "total_files": 42,
  "files": [
    {
      "file_name": "document.pdf",
      "file_path": "/path/to/source/document.pdf",
      "mime_type": "application/pdf",
      "file_size": 1024000
    }
  ],
  "unique_mime_types": [
    "application/pdf",
    "image/jpeg",
    "text/plain"
  ],
  "available_models": [
    {
      "name": "gpt-4-vision",
      "type": "online",
      "provider": "openai",
      "model_name": "gpt-4-vision-preview",
      "capabilities": ["text", "image"]
    }
  ],
  "mime_to_model_mapping": {
    "application/pdf": "gpt-4",
    "image/jpeg": "gpt-4-vision",
    "text/plain": "llama3.2"
  },
  "model_connectivity": {
    "gpt-4": true,
    "gpt-4-vision": true,
    "llama3.2": true
  }
}
```

## Development Status

**Completed:**
- ✅ Stage 1: File scanning and enumeration

**Planned:**
- ⏳ Stage 2: AI-powered file analysis and categorization
- ⏳ Stage 3: File organization and moving
- ⏳ Additional features and optimizations

## Requirements

- Python 3.7+
- python-magic
- PyYAML
- requests
- openai (for OpenAI models)
- anthropic (for Anthropic models)
- libmagic1 (system library)

## Testing

Run the test script to verify Stage 1 functionality:
```bash
python test_stage1.py
```

This will:
1. Load the configuration
2. Scan the test_data directory
3. Display all discovered files and MIME types
4. Show available AI models
5. Display the AI-generated MIME-to-model mapping

## How It Works

### Stage 1 Workflow

1. **Configuration Loading**: Load settings from YAML config file
2. **Directory Scanning**: Recursively scan source directory for files
3. **File Analysis**: Collect metadata (name, path, MIME type, size) for each file
4. **MIME Type Extraction**: Extract unique MIME types from all files
5. **Model Discovery**: Discover available AI models based on configured method
6. **AI-Powered Mapping**: Use AI to recommend which model should analyze each MIME type
7. **Model Download**: Download required models (if in local_download mode)
8. **Connectivity Verification**: Test all models to ensure they're accessible
9. **Result Compilation**: Package all information into Stage1Result object

### MIME-to-Model Mapping

The system uses an AI "orchestrator" model to intelligently map file types to analysis models:

- **Vision models** (e.g., GPT-4 Vision, LLaVA) for images and visual content
- **Specialized models** for specific formats (PDFs, code files, etc.)
- **General models** for text and other content
- **Cost optimization** by preferring local models when appropriate

## Development Status

**Completed:**
- ✅ Stage 1: File scanning and enumeration
- ✅ MIME type detection and extraction
- ✅ Multi-method AI model discovery
- ✅ AI-powered MIME-to-model mapping
- ✅ Support for online and local models

**Planned:**
- ⏳ Stage 2: AI-powered file analysis and categorization
- ⏳ Stage 3: File organization and moving
- ⏳ Additional features and optimizations

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[MODELS.md](MODELS.md)** - Complete AI model system documentation
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and data flow diagrams
- **[STAGE1_SUMMARY.md](STAGE1_SUMMARY.md)** - Technical summary of Stage 1 deliverables
- **[config.example.yaml](config.example.yaml)** - Full configuration example

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

[License information to be added]
