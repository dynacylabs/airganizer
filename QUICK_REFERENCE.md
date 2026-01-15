# Airganizer Phase 3: Quick Reference

## Installation

```bash
# Clone and setup
git clone <repo>
cd airganizer
pip install -r requirements.txt

# Set API key
export OPENAI_API_KEY='your-key'
# or
export ANTHROPIC_API_KEY='your-key'
```

## CLI Commands

### Scan Files
```bash
python -m src scan /path/to/directory
python -m src scan /path -o data/files.json --no-binwalk -v
```

### Propose Structure
```bash
python -m src propose --metadata data/files.json
python -m src propose --directory /path --provider anthropic
```

### Analyze & Recommend Models (NEW!)
```bash
python -m src analyze --directory /path
python -m src analyze --metadata data/files.json
python -m src analyze -d /path --provider ollama -o data/results.json
```

## Configuration

Location: `~/.config/airganizer/config.json`

```json
{
  "ai": {
    "mode": "online",
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
      "text/plain": "claude-3-5-sonnet"
    }
  }
}
```

## Python API

### Basic Analysis
```python
from src.core import FileScanner, MetadataCollector, FileItem
from src.ai import create_model_recommender

# Scan
scanner = FileScanner('/path')
files = []
collector = MetadataCollector()

for file_path in scanner.scan():
    metadata = collector.collect_metadata(file_path)
    file_item = FileItem(
        file_path=str(file_path),
        file_name=file_path.name,
        mime_type=metadata.mime_type,
        file_size=metadata.file_size
    )
    files.append(file_item)

# Recommend
recommender = create_model_recommender(provider='openai')
recommendations = recommender.recommend_models(files)

# Review
for file in files:
    rec = recommendations[file.file_path]
    print(f"{file.file_name}: {rec['primary_model']}")
```

### Model Registry
```python
from src.models import get_model_registry

registry = get_model_registry()

# Get models for file type
models = registry.get_models_for_filetype("image/jpeg")

# Check availability
model = registry.get_model("gpt-4o-vision")
print(f"Available: {model.is_available}")

# Mark as available
registry.mark_available("llama3.2", True)
```

### Configuration
```python
from src.config import get_config

config = get_config()

# Check mode
if config.is_online_mode():
    print("Using cloud AI")

# Get explicit mapping
model = config.get_model_for_filetype("image/jpeg")

# Check auto-download
if config.should_auto_download():
    print("Auto-download enabled")

# Cache recommendation
config.cache_model_recommendation("image/jpeg", {
    'models': ['gpt-4o-vision'],
    'analysis_types': ['image_analysis'],
    'rationale': 'Vision model for images',
    'priority': 'high'
})
```

## Local AI Setup (Ollama)

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Start Ollama
ollama serve

# Pull models
ollama pull llama3.2
ollama pull llama3.2-vision

# Use with Airganizer
python -m src analyze -d /path --provider ollama
```

## Complete Workflow

```bash
# Step 1: Scan
python -m src scan /messy/directory -o data/files.json

# Step 2: Propose structure
python -m src propose -m data/files.json -o data/structure.json

# Step 3: Get model recommendations
python -m src analyze -m data/files.json -o data/analysis.json

# Step 4: Review
cat data/files.json | jq '.summary'
cat data/structure.json | jq '.root.subdirectories[].name'
cat data/analysis.json | jq '.summary.models_recommended'
```

## Output Formats

### Analyze Output
```json
{
  "files": [{
    "file_path": "/path/file.jpg",
    "file_name": "file.jpg",
    "mime_type": "image/jpeg",
    "recommendation": {
      "primary_model": "gpt-4o-vision",
      "analysis_types": ["image_analysis", "ocr"],
      "priority": "high",
      "source": "ai_recommendation"
    }
  }],
  "summary": {
    "total_files": 10,
    "models_recommended": {
      "gpt-4o-vision": 7,
      "claude-3-5-sonnet": 3
    }
  }
}
```

## Troubleshooting

### No API Key
```bash
export OPENAI_API_KEY='your-key'
```

### Ollama Not Running
```bash
ollama serve
```

### Model Not Available
```python
from src.models import get_model_registry
registry = get_model_registry()
registry.mark_available("llama3.2", True)
```

## AI Providers

| Provider | Setup | Model Examples |
|----------|-------|----------------|
| OpenAI | `export OPENAI_API_KEY=...` | gpt-4o, gpt-4o-vision |
| Anthropic | `export ANTHROPIC_API_KEY=...` | claude-3-5-sonnet |
| Ollama | `ollama serve` + `ollama pull <model>` | llama3.2, llama3.2-vision |

## Pre-configured Models

- **gpt-4o-vision** - OpenAI vision model
- **gpt-4o** - OpenAI text/code model
- **claude-3-5-sonnet-vision** - Anthropic vision model
- **claude-3-5-sonnet** - Anthropic text/code model
- **llama3.2-vision** - Ollama vision model (local)
- **llama3.2** - Ollama text/code model (local)

## Common Use Cases

### Analyze Images
```bash
python -m src analyze -d /path/to/images --provider openai
```

### Analyze Code
```bash
python -m src analyze -d /path/to/code --provider anthropic
```

### Use Local AI
```bash
ollama pull llama3.2
python -m src analyze -d /path --provider ollama
```

### Custom Model Mapping
```json
{
  "models": {
    "explicit_mapping": {
      "image/*": "gpt-4o-vision",
      "text/*": "claude-3-5-sonnet"
    }
  }
}
```

## Documentation

- **README.md** - Main documentation
- **PHASE3_COMPLETE.md** - Detailed Phase 3 guide
- **IMPLEMENTATION_SUMMARY.md** - Technical summary
- **docs/AI_PROPOSAL.md** - AI structure proposal guide

## Phase Status

- ✅ Phase 1: File scanning & metadata
- ✅ Phase 2: AI structure proposal
- ✅ Phase 3: AI model recommendations
- 📋 Phase 4: Execute analysis (coming soon)
- 📋 Phase 5: File organization (planned)

## Support

Report issues or contribute at: [GitHub repo]

## Quick Test

```bash
# Test with included test data
python test_analyze.py

# Or manually
python -m src analyze -d test_data
```
