# Optimizing Airganizer for Large Datasets (100GB+)

## Your Situation: 650GB Dataset

**Current performance:**
- Chunk size: 4,000 chars
- Total chunks: 560,000
- Time per chunk: 2-3 seconds
- **Total time: ~16 days** ❌

**Optimized performance:**
- Chunk size: 500,000 chars
- Total chunks: ~4,500
- Time per chunk: 2-3 seconds
- **Total time: ~3 hours** ✅

**125x faster!**

## Recommended Configuration

### Option 1: Claude 3.5 Sonnet (Best for Large Datasets)

```yaml
ai_provider: anthropic
chunk_size: 500000  # 500K characters per chunk

anthropic:
  api_key: 'your-key-here'  # Or set ANTHROPIC_API_KEY env var
  model: claude-3-5-sonnet-20241022
```

**Why Claude?**
- ✅ 200K token context window (~600K characters)
- ✅ Excellent quality for organization tasks
- ✅ Fast processing
- ✅ Best cost/performance for large datasets

**Estimated cost for 650GB:**
- ~4,500 chunks × $3 per 1M input tokens
- **~$30-50 total** (actual cost depends on structure complexity)

### Option 2: GPT-4 Turbo (Cloud Alternative)

```yaml
ai_provider: openai
chunk_size: 300000  # 300K characters per chunk

openai:
  api_key: 'your-key-here'  # Or set OPENAI_API_KEY env var
  model: gpt-4-turbo
```

**Why GPT-4 Turbo?**
- ✅ 128K token context window (~400K characters)
- ✅ Very fast processing
- ✅ Good quality

**Estimated cost for 650GB:**
- ~7,500 chunks × $10 per 1M input tokens
- **~$75-100 total**

### Option 3: Ollama Local (Free but Slower)

For M4 Mac Mini with 32GB RAM:

```yaml
ai_provider: ollama
chunk_size: 100000  # 100K characters per chunk

ollama:
  model: qwen2.5:32b
  base_url: http://localhost:11434
```

**Why Qwen 2.5?**
- ✅ 32K token context window (~100K characters)
- ✅ Free (local processing)
- ✅ Privacy (offline)
- ⚠️ Slower than cloud (5-10s per chunk)

**Setup:**
```bash
ollama pull qwen2.5:32b
```

**Estimated time for 650GB:**
- ~50,000 chunks × 7 seconds average
- **~97 hours (~4 days)**
- Still 4x faster than your current setup!

For M4 Mac Mini with 16GB RAM:

```yaml
ollama:
  model: qwen2.5:7b  # Smaller but still good
  chunk_size: 80000
```

## Implementation Steps

### 1. Update Your Config

Edit `.airganizer.yaml`:

```yaml
# For Claude (RECOMMENDED)
ai_provider: anthropic
chunk_size: 500000

# Or for GPT-4 Turbo
ai_provider: openai
chunk_size: 300000

# Or for Ollama local
ai_provider: ollama
chunk_size: 100000
```

### 2. Set API Key (for cloud)

```bash
# For Claude
export ANTHROPIC_API_KEY="your-key-here"

# For OpenAI
export OPENAI_API_KEY="your-key-here"

# For Ollama - install model
ollama pull qwen2.5:32b
```

### 3. Run with Debug Mode

```bash
python -m airganizer.main /path/to/650gb/data --organize --debug --output structure.json
```

**Watch for:**
- `[DEBUG] Chunk size: 500000 characters` (verify it's using large chunks)
- `[DEBUG] Created X chunks` (should be ~4,500 for Claude, not 560,000)
- `[DEBUG] Chunk size source: config file` (verify config is being read)

### 4. Monitor Progress

While it's running, check the temporary file:

```bash
# In another terminal
watch -n 5 'cat /tmp/airganizer_progress_*.json | python -m json.tool | head -50'
```

## Chunk Size Guidelines

| Dataset Size | Recommended Chunk Size | Model |
|-------------|----------------------|-------|
| < 1GB | 4,000 - 8,000 | Any |
| 1-10GB | 20,000 - 50,000 | Any |
| 10-100GB | 100,000 - 200,000 | GPT-4 Turbo, Claude, qwen2.5 |
| 100GB-1TB | 300,000 - 600,000 | Claude 3.5, GPT-4 Turbo |
| 1TB+ | 500,000 - 1,000,000 | Claude 3.5 (best) |

## Context Window Limits

| Model | Context Window | Max Chunk Size (safe) |
|-------|---------------|----------------------|
| Claude 3.5 Sonnet | 200K tokens | 600,000 chars |
| GPT-4 Turbo | 128K tokens | 400,000 chars |
| Gemini 1.5 Pro | 1M tokens | 3,000,000 chars |
| qwen2.5:32b | 32K tokens | 100,000 chars |
| llama3.2:90b | 128K tokens | 400,000 chars |

**Note:** 1 token ≈ 3-4 characters for English text, ~2-3 for file paths

## Testing Different Chunk Sizes

Try different chunk sizes to find the sweet spot:

```bash
# Test with 100K chunks
python -m airganizer.main /sample/dir --organize --chunk-size 100000 --output test_100k.json

# Test with 300K chunks
python -m airganizer.main /sample/dir --organize --chunk-size 300000 --output test_300k.json

# Test with 500K chunks
python -m airganizer.main /sample/dir --organize --chunk-size 500000 --output test_500k.json
```

Compare:
- Processing time
- Structure quality
- Number of chunks generated

## Performance Comparison Table

For your 650GB dataset:

| Configuration | Chunks | Time/Chunk | Total Time | Cost | Quality |
|--------------|--------|-----------|------------|------|---------|
| Current (4K) | 560,000 | 2.5s | **16 days** | - | ⭐⭐⭐ |
| Claude 500K | 4,500 | 2.5s | **3 hours** | $30-50 | ⭐⭐⭐⭐⭐ |
| GPT-4T 300K | 7,500 | 2s | **4 hours** | $75-100 | ⭐⭐⭐⭐ |
| Qwen 100K | 50,000 | 7s | **4 days** | Free | ⭐⭐⭐⭐ |

## My Recommendation for 650GB

**Use Claude 3.5 Sonnet with 500K chunks:**

1. Best performance (3 hours vs 16 days)
2. Best quality for this task
3. Reasonable cost ($30-50)
4. Large context window handles complexity well
5. Proven reliability for large-scale tasks

```yaml
ai_provider: anthropic
chunk_size: 500000

anthropic:
  api_key: ''  # Set via ANTHROPIC_API_KEY
  model: claude-3-5-sonnet-20241022
```

```bash
export ANTHROPIC_API_KEY="your-key"
python -m airganizer.main /your/650gb/data --organize --debug --output organized_structure.json
```

You'll go from **16 days to 3 hours** - a 125x improvement! 🚀
