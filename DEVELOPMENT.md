# Development Guide

Guide for developers who want to contribute to AIrganizer or understand its architecture.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Pipeline Stages](#pipeline-stages)
- [Key Components](#key-components)
- [Cache System](#cache-system)
- [Progress Tracking](#progress-tracking)
- [Development Setup](#development-setup)
- [Contributing](#contributing)
- [Code Style](#code-style)
- [Testing](#testing)

## Architecture Overview

AIrganizer follows a **5-stage pipeline architecture** with complete resumability through caching:

```
┌───────────────────────────────────────┐
│  main.py (Orchestrator)               │
│  - Configuration loading              │
│  - Pipeline coordination              │
│  - Progress tracking                  │
│  - Cache management                   │
└──────────┬────────────────────────────┘
           │
           ▼
┌───────────────────────────────────────┐
│  Stage 1: File Scanning               │
│  - src/stage1.py                      │
│  - Metadata extraction                │
│  - MIME type detection                │
└──────────┬────────────────────────────┘
           │ Cache: files + metadata
           ▼
┌───────────────────────────────────────┐
│  Stage 2: AI Model Discovery          │
│  - src/stage2.py                      │
│  - src/model_discovery.py             │
│  - MIME→model mapping                 │
└──────────┬────────────────────────────┘
           │ Cache: models + mapping
           ▼
┌───────────────────────────────────────┐
│  Stage 3: AI File Analysis            │
│  - src/stage3.py                      │
│  - src/ai_interface.py                │
│  - Generate names/descriptions/tags   │
└──────────┬────────────────────────────┘
           │ Cache: analysis results
           ▼
┌───────────────────────────────────────┐
│  Stage 4: Taxonomy Generation         │
│  - src/stage4.py                      │
│  - Hierarchical structure planning    │
│  - File categorization                │
└──────────┬────────────────────────────┘
           │ Cache: taxonomy + assignments
           ▼
┌───────────────────────────────────────┐
│  Stage 5: File Organization           │
│  - src/stage5.py                      │
│  - Physical file moving               │
│  - Conflict resolution                │
└───────────────────────────────────────┘
           Cache: move operations
```

### Design Principles

1. **Modularity**: Each stage is independent and testable
2. **Resumability**: Complete caching at every stage
3. **Flexibility**: Support for online and local AI models
4. **Observability**: Comprehensive logging and progress tracking
5. **Safety**: Dry-run mode, conflict handling, error recovery

## Project Structure

```
airganizer/
├── main.py                     # Pipeline orchestrator
├── requirements.txt            # Python dependencies
├── config.example.yaml         # Example configuration
│
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration loader
│   ├── models.py              # Data models (Pydantic)
│   ├── cache.py               # Cache management system
│   ├── progress.py            # Progress bar manager
│   │
│   ├── stage1.py              # Stage 1: File scanning
│   ├── stage2.py              # Stage 2: Model discovery
│   ├── stage3.py              # Stage 3: AI analysis
│   ├── stage4.py              # Stage 4: Taxonomy generation
│   ├── stage5.py              # Stage 5: File organization
│   │
│   ├── ai_interface.py        # AI provider abstraction
│   ├── model_discovery.py     # Model discovery logic
│   ├── mime_mapper.py         # MIME→model mapping
│   └── utils.py               # Utility functions
│
├── docs/ (removed - consolidated into these 4 files)
│
└── README.md                  # Project overview
    USAGE.md                   # Usage guide
    CONFIGURATION.md           # Configuration reference
    DEVELOPMENT.md             # This file
```

## Pipeline Stages

### Stage 1: File Scanning

**Purpose:** Discover files and extract metadata

**Implementation:** [src/stage1.py](src/stage1.py)

**Key functions:**
```python
def run_stage1(config: Config, progress_manager: Optional[ProgressManager] = None) -> Stage1Result:
    """
    Scan source directory and collect file metadata.
    
    Returns:
        Stage1Result with files, mime_types, and metadata
    """
```

**Outputs:**
- List of `FileInfo` objects with metadata
- Unique MIME types discovered
- Error tracking for inaccessible files

**Cache:** Stores scan results and metadata

### Stage 2: AI Model Discovery

**Purpose:** Discover AI models and map MIME types to models

**Implementation:** [src/stage2.py](src/stage2.py), [src/model_discovery.py](src/model_discovery.py)

**Key functions:**
```python
def run_stage2(
    config: Config, 
    stage1_result: Stage1Result,
    progress_manager: Optional[ProgressManager] = None
) -> Stage2Result:
    """
    Discover available AI models and create MIME→model mapping.
    
    Returns:
        Stage2Result with models and mapping
    """
```

**Outputs:**
- List of available AI models
- MIME type to model mapping
- Model connectivity status

**Cache:** Stores model list and MIME mapping

### Stage 3: AI-Powered Analysis

**Purpose:** Analyze each file with AI to generate names, descriptions, and tags

**Implementation:** [src/stage3.py](src/stage3.py), [src/ai_interface.py](src/ai_interface.py)

**Key functions:**
```python
def run_stage3(
    config: Config,
    stage2_result: Stage2Result,
    progress_manager: Optional[ProgressManager] = None
) -> Stage3Result:
    """
    Analyze files with AI models.
    
    Returns:
        Stage3Result with AI analysis for each file
    """
```

**Outputs:**
- Proposed filename for each file
- Content description
- Categorization tags
- Error tracking

**Cache:** Stores analysis results per file

### Stage 4: Taxonomy Generation

**Purpose:** Create hierarchical directory structure and assign files

**Implementation:** [src/stage4.py](src/stage4.py)

**Key functions:**
```python
def run_stage4(
    config: Config,
    stage3_result: Stage3Result,
    progress_manager: Optional[ProgressManager] = None
) -> Stage4Result:
    """
    Generate taxonomy structure and assign files to categories.
    
    Returns:
        Stage4Result with taxonomy tree and file assignments
    """
```

**Outputs:**
- Hierarchical taxonomy tree
- File-to-category assignments
- Assignment reasoning

**Cache:** Stores taxonomy and assignments

### Stage 5: File Organization

**Purpose:** Physically move files to organized locations

**Implementation:** [src/stage5.py](src/stage5.py)

**Key functions:**
```python
def run_stage5(
    config: Config,
    stage4_result: Stage4Result,
    progress_manager: Optional[ProgressManager] = None,
    dry_run: bool = False
) -> Stage5Result:
    """
    Move files to organized locations.
    
    Args:
        dry_run: If True, preview moves without executing
    
    Returns:
        Stage5Result with move operations and logs
    """
```

**Outputs:**
- Organized files in destination
- Excluded files log (with reasons)
- Error files log (with error details)
- Move operation summary

**Cache:** Stores move operations

## Key Components

### Cache System

**File:** [src/cache.py](src/cache.py)

**Core class:**
```python
class CacheManager:
    """
    Manages caching for all pipeline stages.
    
    Features:
    - No TTL (permanent cache)
    - Stage-specific cache namespaces
    - Automatic serialization
    - Cache statistics
    """
    
    def get_stage_cache(self, stage: int, key: str) -> Optional[Any]:
        """Get cached data for a specific stage."""
        
    def save_stage_cache(self, stage: int, key: str, data: Any):
        """Save data to stage-specific cache."""
        
    def clear_cache(self, stage: Optional[int] = None):
        """Clear cache for specific stage or all stages."""
        
    def get_stats(self) -> dict:
        """Get cache statistics."""
```

**Cache structure:**
```
.cache_airganizer/
├── stage1_files.json          # Scanned files
├── stage1_metadata.json       # File metadata
├── stage2_models.json         # Discovered models
├── stage2_mapping.json        # MIME→model mapping
├── stage3_analysis_<hash>.json # Per-file analysis
├── stage4_taxonomy.json       # Taxonomy tree
├── stage4_assignments.json    # File assignments
├── stage5_operations.json     # Move operations
└── cache_stats.json           # Cache metadata
```

**Design decisions:**
- **No TTL:** Cache is permanent until manually cleared
- **Granular caching:** Stage 3 caches per file for efficiency
- **Hash-based keys:** File content hashing for cache invalidation
- **JSON format:** Human-readable for debugging

### Progress Tracking

**File:** [src/progress.py](src/progress.py)

**Core class:**
```python
class ProgressManager:
    """
    Manages dual progress bars for visual feedback.
    
    Features:
    - Top bar: Current stage progress
    - Bottom bar: Overall pipeline progress
    - File info display
    - Auto-disable in debug mode
    """
    
    def start_stage(self, stage_name: str, total_items: int):
        """Start tracking a new stage."""
        
    def update_file_info(self, file_info: str):
        """Update currently processing file display."""
        
    def advance_stage(self, n: int = 1):
        """Advance stage progress bar."""
        
    def complete_stage(self):
        """Mark current stage as complete."""
```

**Visual layout:**
```
Stage 3: AI Analysis ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 45/100 files (45%)
📄 Analyzing: vacation_photo_2023.jpg

Overall Progress    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 58% complete
```

**Implementation details:**
- Built with [Rich](https://github.com/Textualize/rich) library
- Context manager pattern for clean setup/teardown
- Automatically disabled in debug/verbose mode
- 4 updates per second refresh rate

### AI Interface

**File:** [src/ai_interface.py](src/ai_interface.py)

**Core abstraction:**
```python
class AIInterface:
    """
    Unified interface for multiple AI providers.
    
    Supports:
    - OpenAI (GPT-4, GPT-4o)
    - Anthropic (Claude 3 family)
    - Ollama (local models)
    """
    
    def analyze_file(
        self, 
        file_path: str, 
        mime_type: str, 
        model_name: str
    ) -> FileAnalysis:
        """
        Analyze file with specified AI model.
        
        Returns:
            FileAnalysis with name, description, tags
        """
```

**Provider-specific implementations:**
- `OpenAIProvider`: OpenAI API integration
- `AnthropicProvider`: Anthropic API integration
- `OllamaProvider`: Ollama local model integration

**Key features:**
- Automatic provider selection based on model name
- Vision model support for images
- Retry logic with exponential backoff
- Rate limiting and timeout handling

### Data Models

**File:** [src/models.py](src/models.py)

**Core models (Pydantic):**

```python
class FileInfo(BaseModel):
    """Information about a single file."""
    file_name: str
    file_path: str
    mime_type: str
    file_size: int
    metadata: Optional[dict] = None

class FileAnalysis(BaseModel):
    """AI analysis results for a file."""
    proposed_filename: str
    description: str
    tags: List[str]

class Stage1Result(BaseModel):
    """Results from Stage 1 (file scanning)."""
    source_directory: str
    total_files: int
    files: List[FileInfo]
    unique_mime_types: List[str]

class Stage2Result(BaseModel):
    """Results from Stage 2 (model discovery)."""
    available_models: List[ModelInfo]
    mime_to_model_mapping: Dict[str, str]
    model_connectivity: Dict[str, bool]

class Stage3Result(BaseModel):
    """Results from Stage 3 (AI analysis)."""
    analyzed_files: List[Tuple[FileInfo, FileAnalysis]]
    errors: List[Tuple[str, str]]

class Stage4Result(BaseModel):
    """Results from Stage 4 (taxonomy)."""
    taxonomy: dict
    file_assignments: Dict[str, str]
    reasoning: Dict[str, str]

class Stage5Result(BaseModel):
    """Results from Stage 5 (organization)."""
    organized_files: List[str]
    excluded_files: List[Tuple[str, str]]
    error_files: List[Tuple[str, str]]
    move_operations: int
```

**Benefits of Pydantic:**
- Automatic validation
- Type safety
- JSON serialization/deserialization
- IDE autocomplete support

## Development Setup

### Prerequisites

- Python 3.7+
- pip
- git

### Installation

```bash
# Clone repository
git clone https://github.com/dynacylabs/airganizer.git
cd airganizer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt  # If exists

# Install system dependencies
sudo apt-get install libmagic1  # Debian/Ubuntu
# or
brew install libmagic  # macOS
```

### Optional: Local AI Setup

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Download models
ollama pull llama3.2-vision
ollama pull llava
ollama pull llama3.2

# Start Ollama service
ollama serve
```

### Running from Source

```bash
# Basic run
python main.py --config config.example.yaml --src ./test --dst ./output

# Debug mode
python main.py --config config.example.yaml --src ./test --dst ./output --verbose

# Test with limited files
python main.py --config config.example.yaml --src ./test --dst ./output --max-files 5
```

## Contributing

We welcome contributions! Here's how to get started:

### Contribution Workflow

1. **Fork the repository**
   ```bash
   gh repo fork dynacylabs/airganizer
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow code style guidelines
   - Add tests if applicable
   - Update documentation

4. **Test your changes**
   ```bash
   python main.py --config config.example.yaml --src ./test --dst ./output --verbose
   ```

5. **Commit with clear messages**
   ```bash
   git commit -m "Add feature: brief description"
   ```

6. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

### Areas for Contribution

#### High Priority
- Additional AI provider support (Google Gemini, local LLMs)
- Performance optimizations for large file sets
- Web UI for configuration and monitoring
- Docker containerization
- Additional file format support

#### Medium Priority
- Enhanced metadata extraction
- Custom taxonomy templates
- Batch processing improvements
- API rate limiting improvements
- Documentation improvements

#### Good First Issues
- Additional example configurations
- Bug fixes
- Documentation typos
- Code comments
- Example scripts

## Code Style

### Python Style Guide

Follow [PEP 8](https://pep8.org/) with these specifics:

```python
# Imports: standard lib, third-party, local
import os
import sys

from rich.progress import Progress
import yaml

from src.models import FileInfo
from src.config import Config

# Type hints for all functions
def process_file(file_path: str, config: Config) -> Optional[FileInfo]:
    """
    Process a single file.
    
    Args:
        file_path: Absolute path to file
        config: Configuration object
        
    Returns:
        FileInfo object if successful, None otherwise
    """
    pass

# Constants in UPPER_CASE
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

# Classes in PascalCase
class FileProcessor:
    """Processes files for organization."""
    
    def __init__(self, config: Config):
        self.config = config
```

### Docstring Format

Use Google-style docstrings:

```python
def analyze_file(file_path: str, model: str, retries: int = 3) -> FileAnalysis:
    """
    Analyze a file with the specified AI model.
    
    Args:
        file_path: Absolute path to the file to analyze
        model: Name of the AI model to use
        retries: Number of retry attempts on failure
        
    Returns:
        FileAnalysis object with proposed name, description, and tags
        
    Raises:
        ValueError: If file_path doesn't exist
        AIConnectionError: If AI model is unreachable
        
    Example:
        >>> analysis = analyze_file("/path/to/file.jpg", "gpt-4o")
        >>> print(analysis.proposed_filename)
        "sunset_beach_vacation_2023.jpg"
    """
```

### Logging

Use consistent logging levels:

```python
import logging

logger = logging.getLogger(__name__)

# DEBUG: Detailed information for debugging
logger.debug(f"Processing file: {file_path}")

# INFO: General informational messages
logger.info(f"Stage 3 complete: {files_processed} files analyzed")

# WARNING: Warning messages for recoverable issues
logger.warning(f"Model {model_name} slow to respond, retrying...")

# ERROR: Error messages for failures
logger.error(f"Failed to analyze {file_path}: {error}")

# CRITICAL: Critical errors that stop execution
logger.critical(f"Cache directory not writable: {cache_dir}")
```

## Testing

### Manual Testing

```bash
# Test Stage 1 only
python main.py --config config.yaml --src ./test --dst ./out --skip-stage3 --skip-stage4 --skip-stage5

# Test with specific files
python main.py --config config.yaml --src ./test --dst ./out --max-files 5 --verbose

# Test cache system
python main.py --config config.yaml --src ./test --dst ./out --cache-stats
python main.py --config config.yaml --src ./test --dst ./out --clear-cache all
```

### Integration Testing

Create test scenarios in `test/` directory:

```
test/
├── images/
│   ├── photo1.jpg
│   └── photo2.png
├── documents/
│   ├── doc1.pdf
│   └── doc2.txt
└── mixed/
    └── various_files...
```

Run integration test:
```bash
python main.py --config config.yaml --src ./test --dst ./test_output --verbose
```

### Performance Testing

```bash
# Large file set
python main.py --config config.yaml --src ./large_dataset --dst ./output --verbose

# Monitor cache performance
python main.py --config config.yaml --src ./test --dst ./out --cache-stats
```

## Debugging

### Enable Verbose Logging

```bash
python main.py --config config.yaml --src ./test --dst ./out --verbose
```

### Inspect Cache

```bash
# View cache statistics
python main.py --config config.yaml --src ./test --dst ./out --cache-stats

# Manually inspect cache files
ls -lah .cache_airganizer/
cat .cache_airganizer/stage1_files.json | python -m json.tool
```

### Test AI Connectivity

```python
# Test OpenAI
import openai
openai.api_key = "your-key"
models = openai.Model.list()
print(models)

# Test Ollama
import requests
response = requests.get("http://localhost:11434/api/tags")
print(response.json())
```

## Roadmap

### Version 1.0 (Current)
- ✅ Complete 5-stage pipeline
- ✅ Full caching system
- ✅ Dual progress bars
- ✅ Multi-provider AI support

### Version 1.1 (Planned)
- ⏳ Web UI for configuration
- ⏳ Docker support
- ⏳ Additional AI providers (Gemini)
- ⏳ Performance optimizations

### Version 2.0 (Future)
- ⏳ Plugin system
- ⏳ Custom taxonomy templates
- ⏳ REST API
- ⏳ Cloud deployment options

## License

MIT License - See LICENSE file for details.

## Contact

- **Issues:** [GitHub Issues](https://github.com/dynacylabs/airganizer/issues)
- **Discussions:** [GitHub Discussions](https://github.com/dynacylabs/airganizer/discussions)
- **Email:** [contact info]

## Acknowledgments

- [Rich](https://github.com/Textualize/rich) - Beautiful terminal UI
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
- [python-magic](https://github.com/ahupp/python-magic) - MIME type detection
- OpenAI, Anthropic, and Ollama for AI capabilities
