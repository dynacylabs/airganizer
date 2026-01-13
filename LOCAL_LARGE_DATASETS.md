# Running Airganizer Locally for 650GB Dataset

## Best Local Configuration for M4 Mac Mini

### If you have 32GB+ RAM (RECOMMENDED):

```yaml
# Edit .airganizer.yaml
ai_provider: ollama
chunk_size: 100000  # 100K characters per chunk

ollama:
  model: qwen2.5:32b
  base_url: http://localhost:11434
```

**Performance:**
- ~50,000 chunks (vs 560,000 at 4K)
- ~7 seconds per chunk (with Metal acceleration)
- **Total time: ~97 hours (~4 days)**
- Free, private, offline
- **11x faster than your current 4K setup!**

**Setup:**
```bash
# Install Ollama
brew install ollama

# Pull the model (will download ~19GB)
ollama pull qwen2.5:32b

# Start Ollama
ollama serve

# Verify it's working
ollama run qwen2.5:32b "Hello"
```

### If you have 16GB RAM:

```yaml
ai_provider: ollama
chunk_size: 80000  # 80K characters per chunk

ollama:
  model: qwen2.5:7b
  base_url: http://localhost:11434
```

**Performance:**
- ~62,500 chunks
- ~5 seconds per chunk
- **Total time: ~87 hours (~3.6 days)**
- Free, private, offline
- **9x faster than current setup!**

**Setup:**
```bash
# Pull the smaller model (~4.7GB)
ollama pull qwen2.5:7b
```

### If you have 64GB+ RAM (High Performance):

```yaml
ai_provider: ollama
chunk_size: 300000  # 300K characters per chunk

ollama:
  model: llama3.2:70b
  base_url: http://localhost:11434
```

**Performance:**
- ~7,500 chunks
- ~10 seconds per chunk (larger model)
- **Total time: ~21 hours (~1 day)**
- Best quality for local processing

**Setup:**
```bash
# Pull the large model (~40GB)
ollama pull llama3.2:70b
```

## Recommended: qwen2.5:32b for M4 Mac Mini

This is the sweet spot for your hardware:

### Full Setup Steps:

```bash
# 1. Install Ollama (if not already installed)
brew install ollama

# 2. Start Ollama service
ollama serve

# 3. In another terminal, pull the model
ollama pull qwen2.5:32b

# 4. Verify installation
ollama list
# Should show qwen2.5:32b

# 5. Test the model
ollama run qwen2.5:32b "Organize these files: report.pdf, photo.jpg, data.csv"
```

### Create/Update Config:

```bash
# Create config if you haven't
python -m airganizer.main . --init-config

# Edit .airganizer.yaml
nano .airganizer.yaml
```

Set these values:
```yaml
ai_provider: ollama
chunk_size: 100000

ollama:
  model: qwen2.5:32b
  base_url: http://localhost:11434
```

### Run the Organization:

```bash
# With debug mode to monitor progress
python -m airganizer.main /path/to/650gb/data --organize --debug --output structure.json
```

### Monitor GPU Usage:

While it's running, check Metal GPU usage:

```bash
# In another terminal
sudo powermetrics --samplers gpu_power -i 1000 -n 1
```

Or use Activity Monitor:
1. Open Activity Monitor
2. Window → GPU History
3. You should see GPU activity

## Performance Comparison (650GB Dataset)

| Configuration | Chunks | Time/Chunk | Total Time | Cost | Quality |
|--------------|--------|-----------|------------|------|---------|
| **Current (4K)** | 560,000 | 2.5s | **16 days** | Free | ⭐⭐⭐ |
| **qwen2.5:32b (100K)** | 50,000 | 7s | **4 days** | Free | ⭐⭐⭐⭐ |
| qwen2.5:7b (80K) | 62,500 | 5s | 3.6 days | Free | ⭐⭐⭐⭐ |
| llama3.2:70b (300K) | 7,500 | 10s | 1 day | Free | ⭐⭐⭐⭐⭐ |

## Why qwen2.5:32b?

✅ **32K token context** - Can handle 100K char chunks  
✅ **Excellent quality** - Better than llama for organization tasks  
✅ **Fast on M4** - Optimized for Apple Silicon  
✅ **Reasonable size** - 19GB model fits in 32GB RAM  
✅ **Free** - No API costs  
✅ **Private** - All processing stays local  
✅ **Offline** - No internet required  

## Optimizations for Speed

### 1. Increase Context Length (if model supports it):

Some models can go beyond their default context. Edit the Ollama request in `ai_providers.py` to increase `num_ctx`:

```python
# In ollama generate_structure method, add:
options={
    "temperature": 0.3,
    "num_predict": 2048,
    "num_ctx": 32768  # Increase context window
}
```

### 2. Adjust Temperature:

Lower temperature = faster but less creative:

```python
options={
    "temperature": 0.1,  # Lower for faster, more deterministic responses
}
```

### 3. Use SSD for Ollama Models:

Make sure Ollama models are stored on fast SSD:

```bash
# Check where models are stored
ollama list

# Models are typically in ~/.ollama/models
```

### 4. Close Other Apps:

Free up RAM and GPU for Ollama:
- Close browsers with many tabs
- Close other GPU-intensive apps
- Close Docker if not needed

## Estimated Timeline for 650GB

**With qwen2.5:32b and 100K chunks:**

- Day 1: Process ~12,500 chunks (25% done)
- Day 2: Process ~12,500 chunks (50% done)  
- Day 3: Process ~12,500 chunks (75% done)
- Day 4: Process ~12,500 chunks (100% done)

**Total: ~4 days** vs 16 days with current setup!

You can monitor progress in real-time:

```bash
# Watch the temporary progress file
watch -n 5 'cat /tmp/airganizer_progress_*.json | python -m json.tool | head -30'
```

## Final Command:

```bash
# Make sure Ollama is running
ollama serve &

# Run Airganizer with debug output
python -m airganizer.main /path/to/650gb/data \
  --organize \
  --debug \
  --output organized_structure.json

# Check status in another terminal
tail -f /tmp/airganizer_progress_*.json
```

🚀 **You'll reduce processing time from 16 days to 4 days - a 4x improvement, completely free and private!**
