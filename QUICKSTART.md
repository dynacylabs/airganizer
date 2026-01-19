# Quick Start Guide

## Installation (5 minutes)

```bash
# 1. Clone and setup
git clone <repository-url>
cd airganizer
pip install -r requirements.txt
sudo apt-get install libmagic1  # Ubuntu/Debian

# 2. Install Ollama (for local AI - optional)
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
ollama pull llama3.2
ollama pull llava

# 3. Or set up online AI (optional)
export OPENAI_API_KEY="your-key-here"
```

## Run Your First Scan (1 minute)

```bash
# Basic scan with default heuristic mapping
python main.py \
  --config config.test.yaml \
  --src ./test_data \
  --dst ./output \
  --verbose

# Save results to JSON
python main.py \
  --config config.test.yaml \
  --src ./test_data \
  --dst ./output \
  --output results.json
```

## Configuration Templates

### Template 1: No AI Required (Fastest Setup)
```yaml
models:
  discovery_method: "config"
  mapping_model: null
  available_models:
    - name: "default"
      type: "local"
      provider: "ollama"
      model_name: "llama3.2:latest"
      capabilities: ["text"]
```

### Template 2: Local AI Only
```yaml
models:
  discovery_method: "local_enumerate"
  local_provider: "ollama"
  mapping_model: null
```

### Template 3: OpenAI + Local Hybrid
```yaml
models:
  discovery_method: "config"
  mapping_model:
    type: "online"
    provider: "openai"
    model_name: "gpt-4"
    api_key_env: "OPENAI_API_KEY"
  available_models:
    - name: "gpt-4-vision"
      type: "online"
      provider: "openai"
      model_name: "gpt-4-vision-preview"
      api_key_env: "OPENAI_API_KEY"
      capabilities: ["text", "image"]
    - name: "llama3.2"
      type: "local"
      provider: "ollama"
      model_name: "llama3.2:latest"
      capabilities: ["text"]
```

## Common Workflows

### Scan Documents Folder
```bash
python main.py \
  --config config.example.yaml \
  --src ~/Documents \
  --dst ~/Organized \
  --output scan_results.json \
  --verbose
```

### Scan with Auto-Download Models
```yaml
# Edit config.yaml
models:
  discovery_method: "local_download"
  ollama:
    auto_download_models:
      - "llama3.2:latest"
      - "llava:latest"
```

```bash
python main.py --config config.yaml --src ~/Downloads --dst ~/Sorted
```

## Understanding the Output

Stage 1 produces:
1. **File list** - All discovered files with metadata
2. **MIME types** - Unique content types found
3. **Available models** - AI models ready for analysis
4. **Mappings** - Which model will analyze each file type

Example output:
```
Total files found: 42
Unique MIME types: 8
Available AI models: 3
MIME-to-model mappings: 8

MIME Types:
  - text/plain: 15 file(s)
  - image/jpeg: 10 file(s)
  - application/pdf: 8 file(s)

Models:
  - llama3.2 (local/ollama)
  - llava (local/ollama)
  - gpt-4-vision (online/openai)

Mappings:
  text/plain -> llama3.2
  image/jpeg -> llava
  application/pdf -> gpt-4-vision
```

## Troubleshooting

### Problem: "No models available"
**Solution:** Install Ollama and pull a model
```bash
ollama serve
ollama pull llama3.2
```

### Problem: "Missing API key"
**Solution:** Set environment variable
```bash
export OPENAI_API_KEY="sk-..."
```

### Problem: "Permission denied"
**Solution:** Check directory permissions
```bash
chmod +r -R /path/to/source
```

## Next Steps

1. ✅ Run test scan with `test_data/`
2. ✅ Review output and mappings
3. ✅ Customize config for your needs
4. ✅ Scan your actual directories
5. ⏳ Wait for Stage 2 (AI file analysis)
6. ⏳ Wait for Stage 3 (File organization)

## Getting Help

- See [README.md](README.md) for full documentation
- See [MODELS.md](MODELS.md) for AI model details
- Check config.example.yaml for all options
- Run with `--verbose` for detailed logs

## Testing

```bash
# Quick test
python test_stage1.py

# Full test with output
python main.py \
  --config config.test.yaml \
  --src test_data \
  --dst output \
  --output test_results.json \
  --verbose
```
