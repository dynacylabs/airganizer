# Running Airganizer Locally on macOS (M4 Mac Mini)

## Quick Start Guide for Local-Only Operation

### Prerequisites

**System Requirements:**
- M4 Mac Mini with 16GB RAM ✅
- macOS (Apple Silicon optimized)
- Python 3.8+
- Ollama for local AI models

---

## Step 1: Install Ollama

```bash
# Download and install Ollama for macOS
curl -fsSL https://ollama.com/install.sh | sh

# Or download from: https://ollama.com/download/mac

# Verify installation
ollama --version

# Start Ollama service (runs in background)
ollama serve
```

---

## Step 2: Configure Airganizer for Local-Only

Create configuration file at `~/.config/airganizer/config.json`:

```bash
mkdir -p ~/.config/airganizer
cat > ~/.config/airganizer/config.json << 'EOF'
{
  "ai": {
    "default_provider": "ollama",
    "providers": {
      "ollama": {
        "enabled": true,
        "base_url": "http://localhost:11434",
        "default_model": "llama3.2:latest"
      },
      "openai": {
        "enabled": false
      },
      "anthropic": {
        "enabled": false
      }
    }
  },
  "models": {
    "auto_download": true,
    "max_concurrent_loaded": 1,
    "auto_unload_idle": true,
    "idle_timeout_seconds": 300,
    "explicit_mapping": {},
    "available_models": {
      "llama3.2:latest": {
        "provider": "ollama",
        "tasks": ["text_analysis", "code_analysis", "structure_proposal"],
        "available": false,
        "auto_download": true
      },
      "codellama:13b": {
        "provider": "ollama",
        "tasks": ["code_analysis"],
        "available": false,
        "auto_download": true
      },
      "mistral:7b": {
        "provider": "ollama",
        "tasks": ["text_analysis", "document_analysis"],
        "available": false,
        "auto_download": true
      }
    }
  },
  "system": {
    "respect_resource_limits": true,
    "max_ram_usage_gb": 16
  },
  "processing": {
    "chunk_size": 100,
    "max_workers": 4
  }
}
EOF
```

**Key Settings for Your System:**
- `auto_download: true` - Automatically downloads models as needed
- `max_concurrent_loaded: 1` - Only one model in RAM at a time (optimal for 16GB)
- `chunk_size: 100` - Process 100 files per AI call (efficient for local models)
- `max_ram_usage_gb: 16` - Use your full 16GB RAM

---

## Step 3: Install Airganizer Dependencies

```bash
# Navigate to airganizer directory
cd /path/to/airganizer

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -m src.main --help
```

---

## Step 4: Run the Complete Workflow

### Option A: Full Automated Pipeline

```bash
#!/bin/bash
# Run complete analysis pipeline

DIR="/Volumes/ssd"
OUTPUT_DIR="./data"

echo "🔍 Phase 1: Scanning directory..."
python -m src.main scan "$DIR" -o "$OUTPUT_DIR/metadata.json" --no-binwalk

echo ""
echo "🤖 Phase 2: Generating organizational structure..."
python -m src.main propose \
  -m "$OUTPUT_DIR/metadata.json" \
  -o "$OUTPUT_DIR/proposed_structure.json" \
  --provider ollama \
  --chunk-size 100

echo ""
echo "📊 Phase 3: Getting model recommendations..."
python -m src.main analyze \
  -m "$OUTPUT_DIR/metadata.json" \
  -o "$OUTPUT_DIR/analysis_results.json" \
  --provider ollama

echo ""
echo "✅ Complete! Results saved to $OUTPUT_DIR/"
echo ""
echo "📁 View proposed structure:"
echo "   cat $OUTPUT_DIR/proposed_structure.json | jq '.structure'"
echo ""
echo "🎯 View model recommendations:"
echo "   cat $OUTPUT_DIR/analysis_results.json | jq '.recommendations'"
```

### Option B: Step-by-Step Commands

#### Phase 1: Scan Directory
```bash
python -m src.main scan /Volumes/ssd \
  -o data/metadata.json \
  --no-binwalk \
  -v
```

**Output:** `data/metadata.json` (file listing with metadata)

---

#### Phase 2: Get AI Structure Proposal
```bash
python -m src.main propose \
  -m data/metadata.json \
  -o data/proposed_structure.json \
  --provider ollama \
  --chunk-size 100
```

**What happens:**
1. First time: Downloads `llama3.2:latest` model (may take 5-10 minutes)
2. Processes files in chunks of 100
3. AI proposes organizational structure
4. Saves structure to `data/proposed_structure.json`

**View the proposed structure:**
```bash
# Pretty print the structure
cat data/proposed_structure.json | jq '.structure'

# Or view full file with rationale
cat data/proposed_structure.json | jq '.'
```

---

#### Phase 3: Get Model Recommendations
```bash
python -m src.main analyze \
  -m data/metadata.json \
  -o data/analysis_results.json \
  --provider ollama
```

**What happens:**
1. Groups files by MIME type
2. Asks AI which models to use for each file type
3. Filters models by your 16GB RAM limit
4. Saves recommendations to `data/analysis_results.json`

**View the recommendations:**
```bash
# Show all recommendations
cat data/analysis_results.json | jq '.recommendations'

# Show recommendations by MIME type
cat data/analysis_results.json | jq '.recommendations | group_by(.mime_type)'

# Show unique models recommended
cat data/analysis_results.json | jq '[.recommendations[].recommended_models[]] | unique'
```

---

## Step 5: View Results

### View Proposed Structure
```bash
# Simple view
jq -r '.structure | to_entries[] | "\(.key)/\n  \(.value.files | join("\n  "))"' data/proposed_structure.json

# With rationale
jq '.structure_rationale' data/proposed_structure.json
```

### View Model Recommendations
```bash
# Summary by file type
jq -r '.recommendations[] | "\(.mime_type): \(.recommended_models | join(", "))"' data/analysis_results.json

# Full details for specific file
jq '.recommendations[] | select(.file_path | contains("example.txt"))' data/analysis_results.json
```

### View System Resource Status
```bash
# Check what models are loaded
python -c "
from src.models import get_model_manager
manager = get_model_manager()
manager.print_status()
"
```

---

## Optimization Tips for 16GB RAM

### Recommended Models for Your System

**Best Choice (7-8GB RAM each):**
- `llama3.2:latest` (8B parameters) - General purpose, fast
- `mistral:7b` - Excellent for text analysis
- `codellama:7b` - Specialized for code

**Avoid (Too Large):**
- `llama3:70b` - Requires 40GB+ RAM
- `mixtral:8x7b` - Requires 32GB+ RAM

### Adjust Chunk Size Based on Performance

```bash
# Faster, more API calls
--chunk-size 50

# Slower, fewer API calls (recommended for local)
--chunk-size 100

# Maximum efficiency
--chunk-size 200
```

### Monitor Resource Usage

```bash
# Install htop for monitoring
brew install htop

# Run in separate terminal
htop

# Watch Ollama memory usage
ps aux | grep ollama
```

---

## Troubleshooting

### Ollama Not Starting
```bash
# Check if running
ps aux | grep ollama

# Restart Ollama
killall ollama
ollama serve
```

### Model Download Fails
```bash
# Manually download model
ollama pull llama3.2:latest

# Check available models
ollama list
```

### Out of Memory
```bash
# Reduce concurrent models in config
"max_concurrent_loaded": 1

# Use smaller model
"default_model": "mistral:7b"

# Reduce chunk size
--chunk-size 50
```

### Slow Performance
```bash
# Apple Silicon is optimized, but first run is slower
# Subsequent runs use cached models and are much faster

# Reduce processing if needed
"max_workers": 2
```

---

## Expected Timeline

**For /Volumes/ssd with ~10,000 files:**

1. **Phase 1 (Scan):** 2-5 minutes
2. **Phase 2 (Propose):** 
   - First time: 10-15 minutes (includes model download)
   - Subsequent: 5-10 minutes
3. **Phase 3 (Analyze):** 3-7 minutes

**Total: ~20-30 minutes first run, ~10-20 minutes after**

---

## Quick Reference Commands

```bash
# Full pipeline
python -m src.main scan /Volumes/ssd -o data/metadata.json --no-binwalk
python -m src.main propose -m data/metadata.json --provider ollama --chunk-size 100
python -m src.main analyze -m data/metadata.json --provider ollama

# View results
cat data/proposed_structure.json | jq '.structure'
cat data/analysis_results.json | jq '.recommendations'

# Check model status
ollama list
```
