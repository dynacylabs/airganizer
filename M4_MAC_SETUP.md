# Running Airganizer on M4 Mac Mini with Metal/MPS Support

This guide shows how to run Airganizer with local AI acceleration on Apple Silicon (M4 Mac Mini).

## Prerequisites

- M4 Mac Mini (or any Apple Silicon Mac)
- macOS 13.0 or later
- Python 3.9+

## Step 1: Install Ollama

Ollama automatically uses Metal Performance Shaders (MPS) for GPU acceleration on Apple Silicon.

```bash
# Install via Homebrew
brew install ollama

# Or download from https://ollama.ai/download
```

## Step 2: Start Ollama

```bash
# Start Ollama service (runs in background)
ollama serve
```

**Note**: Leave this terminal running, or Ollama will run as a background service automatically.

## Step 3: Pull an AI Model

Choose a model based on your needs and RAM:

```bash
# Recommended for M4 Mac Mini (16GB+ RAM)
ollama pull llama3.2:3b          # Fast, 3B parameters, ~2GB
ollama pull mistral:7b           # Balanced, 7B parameters, ~4GB
ollama pull llama3.2:11b         # Best quality, 11B parameters, ~7GB

# For 32GB+ RAM
ollama pull llama3.2:70b         # Highest quality, 70B parameters, ~40GB
```

**Recommended for file organization**: `mistral:7b` or `llama3.2:11b`

## Step 4: Verify Metal/GPU Usage

```bash
# Check if model is loaded
ollama list

# Test a model (should show GPU usage in Activity Monitor)
ollama run mistral:7b "Organize these files: report.pdf, photo.jpg"
```

**Monitor GPU usage**:
1. Open Activity Monitor
2. Go to Window → GPU History
3. You should see GPU activity when Ollama runs

## Step 5: Install Airganizer Dependencies

```bash
cd /path/to/airganizer

# Install Ollama Python client
pip install ollama
```

## Step 6: Configure Airganizer

```bash
# Create config file
python -m airganizer.main . --init-config

# Edit .airganizer.yaml
```

Update `.airganizer.yaml`:

```yaml
# Airganizer Configuration File

ai_provider: ollama
chunk_size: 4000

openai:
  api_key: ''
  model: gpt-4

anthropic:
  api_key: ''
  model: claude-3-5-sonnet-20241022

ollama:
  model: mistral:7b  # Change this to your preferred model
  base_url: http://localhost:11434
```

## Step 7: Run Airganizer

```bash
# Test with a directory
python -m airganizer.main ~/Documents --organize --output structure.json

# Or specify model directly
python -m airganizer.main ~/Downloads --organize --provider ollama
```

## Performance Tips for M4 Mac Mini

### Memory Considerations

- **8GB RAM**: Use `llama3.2:3b` or smaller models
- **16GB RAM**: Use `mistral:7b` or `llama3.2:11b` (recommended)
- **32GB+ RAM**: Use `llama3.2:70b` for best quality

### Optimize Performance

```bash
# Check available models and sizes
ollama list

# Remove unused models to free memory
ollama rm <model-name>

# Monitor memory usage
ollama ps
```

### Metal/MPS Optimization

Ollama automatically uses Metal - no additional configuration needed! The M4's GPU will be utilized automatically for:

- Model inference
- Token generation
- Embedding computation

### Verify Metal Acceleration

```bash
# In another terminal while Ollama is running
# Check GPU usage
sudo powermetrics --samplers gpu_power -i 1000 -n 1
```

## Troubleshooting

### Issue: "Connection refused"

```bash
# Ensure Ollama is running
ollama serve

# Or check if already running
ps aux | grep ollama
```

### Issue: Model is slow

```bash
# Try a smaller model
ollama pull llama3.2:3b

# Update config to use smaller model
# Edit .airganizer.json: "model": "llama3.2:3b"
```

### Issue: Out of memory

```bash
# Use a smaller model or close other apps
# Check memory usage
ollama ps

# Remove large models
ollama rm llama3.2:70b
```

## Complete Example

```bash
# 1. Start Ollama (if not running)
ollama serve &

# 2. Pull a good model for M4
ollama pull mistral:7b

# 3. Test Ollama
ollama run mistral:7b "Hello"

# 4. Install Python dependencies
pip install ollama

# 5. Configure Airganizer
python -m airganizer.main . --init-config
# Edit .airganizer.yaml to set model: "mistral:7b"

# 6. Run organization
python -m airganizer.main ~/Documents --organize --output organized_structure.json

# 7. View results
cat organized_structure.json | python -m json.tool
```

## Expected Performance (M4 Mac Mini)

| Model | RAM Usage | Speed (tokens/sec) | Quality |
|-------|-----------|-------------------|---------|
| llama3.2:3b | ~2GB | ~80-100 | Good |
| mistral:7b | ~4GB | ~40-60 | Better |
| llama3.2:11b | ~7GB | ~30-40 | Best |
| llama3.2:70b | ~40GB | ~10-15 | Excellent |

*Speeds are approximate on M4 with Metal acceleration*

## Advantages of Local AI (Ollama + M4)

✅ **Privacy**: All processing happens locally  
✅ **No API costs**: Free to use  
✅ **Fast**: Metal GPU acceleration  
✅ **Offline**: No internet required  
✅ **No rate limits**: Process as much as you want  

## Alternative: Cloud AI Providers

If you prefer cloud AI for better quality:

### OpenAI (Best Quality)
```bash
export OPENAI_API_KEY="sk-..."
python -m airganizer.main ~/Documents --organize --provider openai
```

### Anthropic Claude (Good Balance)
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python -m airganizer.main ~/Documents --organize --provider anthropic
```

---

**Recommendation for M4 Mac Mini**: Start with `mistral:7b` - it offers the best balance of speed, quality, and memory usage for file organization tasks.
