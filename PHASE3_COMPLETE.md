# Phase 3 Complete: AI Model Recommendation System

## Overview

Phase 3 adds an **AI-powered model recommendation system** that analyzes each file and determines which analysis models should be used based on file metadata. This enables intelligent, file-specific processing with support for both online and local AI models.

## New Features

### 1. AI Model Recommendations

For each file, the system now:
- Analyzes file metadata (MIME type, size, characteristics)
- Asks AI which models are best suited for analysis
- Recommends specific analysis types (OCR, image analysis, text extraction, etc.)
- Assigns priority levels (high/medium/low)
- Caches recommendations by MIME type to reduce API costs

### 2. Enhanced Configuration System

New configuration options in `~/.config/airganizer/config.json`:

```json
{
  "ai": {
    "mode": "online",  // or "local"
    "default_provider": "openai",
    "local": {
      "ollama_host": "http://localhost:11434",
      "ollama_model": "llama3.2"
    }
  },
  "models": {
    "auto_download": false,
    "explicit_mapping": {
      "image/jpeg": "gpt-4o-vision",
      "text/x-script.python": "claude-3-5-sonnet"
    },
    "available_models": [],
    "recommendations_cache": {}
  },
  "analyze": {
    "ask_ai_for_models": true
  }
}
```

### 3. Local AI Support (Ollama)

Full support for running models locally via Ollama:

```python
from src.ai import create_ai_client

# Create Ollama client
client = create_ai_client("ollama", model="llama3.2")

# Generate responses
response = client.generate(
    prompt="Analyze this file...",
    temperature=0.2
)

# List available models
models = client.list_models()

# Pull/download models
client.pull_model("llama3.2-vision")
```

### 4. Model Registry

Comprehensive tracking of available models:

```python
from src.models import get_model_registry

registry = get_model_registry()

# Get models for a file type
models = registry.get_models_for_filetype("image/jpeg")

# Mark model as available
registry.mark_available("llama3.2", True)

# Get all available models
available = registry.get_available_models()
```

### 5. Analyze Command

New CLI command for file analysis:

```bash
# Analyze a directory
python -m src analyze -d test_data -o data/analysis_results.json

# Analyze using metadata file
python -m src analyze -m data/metadata.json -o data/analysis_results.json

# Use specific AI provider
python -m src analyze -d test_data --provider ollama

# Use OpenAI
python -m src analyze -d test_data --provider openai
```

## Architecture

### New Modules

1. **`src/ai/model_recommender.py`** - AI-powered model recommendation engine
   - `ModelRecommender` class
   - `create_model_recommender()` factory function
   - Batch processing for efficiency
   - MIME-type based caching

2. **`src/ai/client.py`** (enhanced) - Multi-provider AI client
   - `OllamaClient` for local models
   - `OpenAIClient` for GPT models
   - `AnthropicClient` for Claude models
   - `create_ai_client()` factory function

3. **`src/commands/analyze.py`** - Analyze command implementation
   - `analyze_command()` function
   - Progress tracking
   - Result aggregation and statistics

4. **`src/config.py`** (enhanced) - Configuration management
   - `is_online_mode()` / `is_local_mode()`
   - `get_model_for_filetype()` - explicit mapping lookup
   - `should_auto_download()` - auto-download preference
   - `cache_model_recommendation()` - cache management
   - `add_available_model()` - track available models

5. **`src/models/registry.py`** - Model information registry
   - `ModelInfo` dataclass
   - `ModelRegistry` class
   - Track capabilities, providers, file type support
   - Mark models as available/unavailable

### Updated Workflow

The complete workflow is now:

1. **Scan** - Enumerate files recursively
2. **Collect Metadata** - Extract MIME type, size, binwalk data
3. **Propose Structure** - AI suggests organizational structure
4. **Analyze & Recommend** - AI recommends which models to use per file
5. **Store Results** - Save metadata + structure + recommendations

## Configuration Guide

### Online AI (OpenAI/Anthropic)

```bash
# Set API key
export OPENAI_API_KEY="your-key-here"
# or
export ANTHROPIC_API_KEY="your-key-here"

# Configure
python -m src config set ai.mode online
python -m src config set ai.default_provider openai
```

### Local AI (Ollama)

```bash
# Install Ollama (https://ollama.ai)
curl https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3.2

# Configure Airganizer
python -m src config set ai.mode local
python -m src config set ai.local.ollama_model llama3.2
```

### Explicit Model Mappings

```bash
# Map specific file types to models
python -m src config set models.explicit_mapping.image/jpeg gpt-4o-vision
python -m src config set models.explicit_mapping.text/x-script.python claude-3-5-sonnet
```

### Auto-Download

```bash
# Enable auto-download (for local models)
python -m src config set models.auto_download true

# Disable
python -m src config set models.auto_download false
```

## Usage Examples

### Basic Analysis

```python
from src.core import FileScanner, MetadataCollector, FileItem
from src.ai import create_model_recommender

# Scan directory
scanner = FileScanner("test_data")
files = scanner.get_all_files()

# Collect metadata
collector = MetadataCollector()
for file in files:
    metadata = collector.collect_metadata(file.file_path)
    file.mime_type = metadata.mime_type
    file.file_size = metadata.file_size

# Get recommendations
recommender = create_model_recommender(provider="openai")
recommendations = recommender.recommend_models(files)

# Process results
for file in files:
    rec = recommendations[file.file_path]
    print(f"{file.file_name}:")
    print(f"  Model: {rec['primary_model']}")
    print(f"  Analysis: {rec['analysis_types']}")
```

### With Custom Configuration

```python
from src.config import get_config

config = get_config()

# Set explicit mapping
config.set("models.explicit_mapping", {
    "image/jpeg": "gpt-4o-vision",
    "image/png": "gpt-4o-vision",
    "text/plain": "claude-3-5-sonnet"
})

# Enable caching
config.set("analyze.ask_ai_for_models", True)

# Now recommendations will use explicit mappings first
recommender = create_model_recommender()
recommendations = recommender.recommend_models(files)
```

### Check Model Availability

```python
from src.models import get_model_registry

registry = get_model_registry()

# Get all models that can handle images
image_models = registry.get_models_for_filetype("image/jpeg")

for model in image_models:
    print(f"{model.name}:")
    print(f"  Provider: {model.provider}")
    print(f"  Available: {model.is_available}")
    print(f"  Capabilities: {', '.join(model.capabilities)}")
```

## Output Format

The `analyze` command produces a JSON file with this structure:

```json
{
  "files": [
    {
      "file_path": "test_data/image.jpg",
      "file_name": "image.jpg",
      "mime_type": "image/jpeg",
      "file_size": 245678,
      "recommendation": {
        "primary_model": "gpt-4o-vision",
        "analysis_types": ["image_analysis", "ocr", "object_detection"],
        "rationale": "Image file requires vision model for comprehensive analysis",
        "source": "ai_recommendation",
        "priority": "high"
      }
    }
  ],
  "summary": {
    "total_files": 10,
    "files_with_recommendations": 10,
    "models_recommended": {
      "gpt-4o-vision": 5,
      "claude-3-5-sonnet": 3,
      "llama3.2": 2
    }
  }
}
```

## Testing

### Test the Analyze Feature

```bash
# Run test script
python test_analyze.py

# Run with specific test directory
python -m src analyze -d test_data

# Full workflow test
python -m src scan test_data -o data/metadata.json
python -m src propose -m data/metadata.json -o data/structure.json
python -m src analyze -m data/metadata.json -o data/analysis.json
```

### Test Local AI (Ollama)

```bash
# Make sure Ollama is running
ollama serve

# Pull a model
ollama pull llama3.2

# Test with Ollama
python -m src analyze -d test_data --provider ollama
```

## API Reference

### ModelRecommender

```python
class ModelRecommender:
    def __init__(self, ai_client: AIClient, model_registry: ModelRegistry):
        """Initialize recommender with AI client and model registry."""
    
    def recommend_models(
        self, 
        files: List[FileItem],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get model recommendations for files.
        
        Returns:
            Dict mapping file_path to recommendation dict with keys:
            - primary_model: str
            - analysis_types: List[str]
            - rationale: str
            - source: str ("ai_recommendation", "explicit_mapping", "cache", "fallback")
            - priority: str ("high", "medium", "low")
        """
```

### Config Methods

```python
config = get_config()

# Mode checks
config.is_online_mode() -> bool
config.is_local_mode() -> bool

# Model lookups
config.get_model_for_filetype(mime_type: str) -> Optional[str]
config.should_auto_download() -> bool

# Caching
config.cache_model_recommendation(mime_type: str, recommendation: dict)
config.get_model_recommendation_cache(mime_type: str) -> Optional[dict]

# Model tracking
config.add_available_model(model_name: str)
```

### ModelRegistry

```python
registry = get_model_registry()

# Lookup models
registry.get_model(name: str) -> Optional[ModelInfo]
registry.get_models_for_filetype(mime_type: str) -> List[ModelInfo]
registry.get_available_models(capability: Optional[str]) -> List[ModelInfo]

# Update availability
registry.mark_available(model_name: str, available: bool = True)

# Add custom models
registry.add_model(model: ModelInfo)
```

## Performance Considerations

### Caching

Model recommendations are cached by MIME type to reduce API costs:

```python
# First file with image/jpeg: calls AI
recommendation1 = recommender.recommend_models([jpeg_file1])

# Subsequent image/jpeg files: uses cache
recommendation2 = recommender.recommend_models([jpeg_file2])  # No AI call!
```

### Batching

The recommender processes files in batches for efficiency:

```python
# Processes in batches of similar file types
recommendations = recommender.recommend_models(files)  # Automatically batched
```

### Explicit Mappings

Skip AI calls entirely by using explicit mappings:

```python
config.set("models.explicit_mapping", {
    "image/jpeg": "gpt-4o-vision",
    "text/plain": "claude-3-5-sonnet"
})
# Files matching these types won't call AI
```

## Next Steps

1. **Phase 4: Actual File Analysis**
   - Execute recommended models on files
   - Extract structured data
   - Generate analysis reports

2. **Model Download Automation**
   - Auto-download Ollama models when recommended
   - Check disk space before downloading
   - Progress tracking for large models

3. **Advanced Features**
   - Multi-model analysis (use multiple models per file)
   - Confidence scoring
   - Cost estimation
   - Analysis scheduling

## Troubleshooting

### "No API key found"

Set the appropriate environment variable:
```bash
export OPENAI_API_KEY="your-key-here"
# or
export ANTHROPIC_API_KEY="your-key-here"
```

### "Cannot connect to Ollama"

Make sure Ollama is running:
```bash
ollama serve
```

Or update the host in config:
```bash
python -m src config set ai.local.ollama_host http://your-server:11434
```

### "No recommendations generated"

Check the configuration:
```bash
python -m src config get analyze.ask_ai_for_models
```

Should be `true`.

### Models not downloading

Enable auto-download:
```bash
python -m src config set models.auto_download true
```

## Summary

Phase 3 adds intelligent, AI-powered model selection that:

✅ Analyzes file metadata to recommend optimal analysis models  
✅ Supports both online (OpenAI/Anthropic) and local (Ollama) AI  
✅ Provides comprehensive configuration system  
✅ Caches recommendations to reduce API costs  
✅ Allows explicit model mappings for full control  
✅ Tracks model availability and capabilities  
✅ Includes new `analyze` CLI command  

The system is now ready for Phase 4: actual file analysis using the recommended models.
