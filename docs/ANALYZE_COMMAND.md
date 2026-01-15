# Analyze Command - AI Model Recommendations

The `analyze` command is a new feature that uses AI to recommend which analysis models and tools should be used for each file type in your dataset.

## Overview

After scanning files and collecting metadata, the analyze command:
1. Groups files by MIME type
2. Sends file metadata to AI (online or local)
3. Gets recommendations for which models/tools to use
4. Saves recommendations with detailed reasoning

## Basic Usage

```bash
# Analyze from existing metadata
python -m src.main analyze --metadata data/metadata.json

# Scan and analyze in one command
python -m src.main analyze --directory /path/to/files

# Use specific AI provider
python -m src.main analyze --metadata data/metadata.json --provider anthropic

# Specify output file
python -m src.main analyze -m data/metadata.json -o results/analysis.json
```

## Command Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--metadata` | `-m` | Path to metadata JSON from scan command | None |
| `--directory` | `-d` | Directory to scan and analyze (alternative to --metadata) | None |
| `--output` | `-o` | Output file for analysis results | `data/analysis.json` |
| `--provider` | | AI provider (openai, anthropic, ollama) | From config |

## Output Format

The analysis command produces a JSON file with this structure:

```json
{
  "analyzed_at": "2024-01-15T10:30:00Z",
  "total_files": 156,
  "ai_provider": "openai",
  "ai_model": "gpt-4o",
  "file_recommendations": {
    "/path/to/document.pdf": {
      "primary_model": "claude-3-5-sonnet-vision",
      "analysis_tasks": [
        "Extract text content and structure",
        "Identify document type (invoice, report, etc.)",
        "Extract tables and figures",
        "Summarize key information"
      ],
      "reason": "PDF files require vision models to understand layout and extract structured data. Claude excels at document analysis.",
      "alternatives": [
        "gpt-4o-vision",
        "llama3.2-vision (local)"
      ],
      "source": "ai_recommended",
      "confidence": "high"
    },
    "/path/to/image.jpg": {
      "primary_model": "gpt-4o-vision",
      "analysis_tasks": [
        "Object detection and classification",
        "Scene understanding",
        "Extract visible text (OCR)",
        "Generate descriptive captions"
      ],
      "reason": "JPEG images benefit from GPT-4 Vision's strong object recognition and detailed scene analysis capabilities.",
      "alternatives": [
        "claude-3-5-sonnet-vision",
        "llama3.2-vision (local)"
      ],
      "source": "ai_recommended",
      "confidence": "high"
    },
    "/path/to/script.py": {
      "primary_model": "gpt-4o",
      "analysis_tasks": [
        "Code analysis and understanding",
        "Identify purpose and functionality",
        "Extract dependencies",
        "Suggest improvements"
      ],
      "reason": "Python code is well-handled by text models. GPT-4 excels at code understanding and analysis.",
      "alternatives": [
        "claude-3-5-sonnet",
        "llama3.2 (local)"
      ],
      "source": "ai_recommended",
      "confidence": "high"
    }
  },
  "mime_type_summary": {
    "application/pdf": {
      "count": 45,
      "recommended_model": "claude-3-5-sonnet-vision",
      "reason": "Optimal for document layout and text extraction"
    },
    "image/jpeg": {
      "count": 78,
      "recommended_model": "gpt-4o-vision",
      "reason": "Superior object detection and scene understanding"
    },
    "text/x-python": {
      "count": 33,
      "recommended_model": "gpt-4o",
      "reason": "Excellent code analysis capabilities"
    }
  }
}
```

## Configuration

### AI Mode Selection

Choose between online (cloud) or local (Ollama) AI:

```json
{
  "ai": {
    "mode": "online",
    "default_provider": "openai"
  }
}
```

Or for local AI:

```json
{
  "ai": {
    "mode": "local",
    "default_provider": "ollama",
    "ollama_base_url": "http://localhost:11434"
  }
}
```

### Explicit Model Mapping

If you don't want AI to recommend models, you can explicitly map file types to models:

```json
{
  "models": {
    "explicit_mapping": {
      "image/jpeg": "gpt-4o-vision",
      "image/png": "gpt-4o-vision",
      "application/pdf": "claude-3-5-sonnet-vision",
      "text/plain": "llama3.2",
      "text/x-python": "gpt-4o",
      "application/json": "llama3.2"
    }
  },
  "analyze": {
    "ask_ai_for_models": false
  }
}
```

With `ask_ai_for_models: false`, the tool will use your explicit mappings instead of asking AI.

### Available Models Tracking

Tell the tool which models you have access to:

```json
{
  "models": {
    "available_models": [
      "gpt-4o",
      "gpt-4o-vision",
      "claude-3-5-sonnet",
      "claude-3-5-sonnet-vision",
      "llama3.2",
      "llama3.2-vision"
    ]
  }
}
```

The AI will only recommend models from this list.

### Auto-Download (Local Models Only)

For local AI with Ollama, enable auto-download of models:

```json
{
  "models": {
    "auto_download": true
  },
  "ai": {
    "mode": "local"
  }
}
```

When enabled, if AI recommends a model that's not available locally, the tool will attempt to download it via Ollama.

### Batch Size

Control how many files to send to AI in one request:

```json
{
  "analyze": {
    "batch_size": 20
  }
}
```

Smaller batches = more API calls but more detailed per-file analysis.
Larger batches = fewer API calls but may sacrifice some detail.

## Workflow Integration

### Complete Analysis Pipeline

```bash
# Step 1: Scan directory and collect metadata
python -m src.main scan ~/Documents -o scan_results.json

# Step 2: Get AI model recommendations
python -m src.main analyze -m scan_results.json -o analysis_results.json

# Step 3: Get organizational structure proposal
python -m src.main propose -m scan_results.json -o structure_proposal.json

# Step 4: Review results
cat analysis_results.json
cat structure_proposal.json
```

### Using Different AI Providers

```bash
# Use OpenAI (default for online mode)
python -m src.main analyze -m data/metadata.json --provider openai

# Use Anthropic Claude
python -m src.main analyze -m data/metadata.json --provider anthropic

# Use local Ollama
python -m src.main analyze -m data/metadata.json --provider ollama
```

### Quick One-Shot Analysis

```bash
# Scan and analyze without intermediate files
python -m src.main analyze -d ~/Projects/my-app -o analysis.json
```

## How It Works

### 1. File Grouping

Files are grouped by MIME type and batched for efficient processing:

```
image/jpeg (45 files) → Batch 1 (20 files), Batch 2 (20 files), Batch 3 (5 files)
application/pdf (12 files) → Batch 1 (12 files)
text/x-python (8 files) → Batch 1 (8 files)
```

### 2. AI Prompt Construction

For each batch, a detailed prompt is created:

```markdown
You are an AI model recommendation expert. I have a list of files with metadata.
For each file, recommend which AI model(s) and analysis tools should be used.

Available models:
- gpt-4o-vision: Vision model, good for images/documents
- claude-3-5-sonnet-vision: Vision model, excellent for documents
- llama3.2-vision: Local vision model
- llama3.2: Local text model

Files:
1. /path/to/image.jpg (image/jpeg, 2.5MB)
   - Binwalk: JPEG image data
2. /path/to/doc.pdf (application/pdf, 1.2MB)
   - Binwalk: PDF document

For each file, provide:
- primary_model: Best model for this file
- analysis_tasks: What analyses to perform
- reason: Why this model is recommended
- alternatives: Other suitable models
```

### 3. Response Parsing

AI responds with structured recommendations:

```json
{
  "recommendations": [
    {
      "file_path": "/path/to/image.jpg",
      "primary_model": "gpt-4o-vision",
      "analysis_tasks": ["Object detection", "Scene understanding"],
      "reason": "GPT-4 Vision excels at image analysis",
      "alternatives": ["claude-3-5-sonnet-vision"]
    }
  ]
}
```

### 4. Caching

Recommendations are cached by MIME type to avoid redundant AI calls:

```python
# First time analyzing JPEG files - asks AI
analyze image/jpeg files → AI recommendation → cache

# Next time - uses cache
analyze more image/jpeg files → cached recommendation (instant)
```

Cache is stored in `data/config.json`:

```json
{
  "analyze": {
    "mime_type_cache": {
      "image/jpeg": {
        "primary_model": "gpt-4o-vision",
        "cached_at": "2024-01-15T10:30:00Z"
      }
    }
  }
}
```

## Decision Logic

The analyze command uses this decision hierarchy:

```
1. Explicit Config Mapping
   └─> If file MIME type in models.explicit_mapping
       └─> Use configured model

2. Cache Lookup
   └─> If MIME type cached in analyze.mime_type_cache
       └─> Use cached recommendation

3. AI Recommendation
   └─> Ask AI which model to use
       └─> Cache result for future files
```

## Use Cases

### Use Case 1: Large Mixed-Media Dataset

You have 1000+ files of various types and want AI to recommend specialized models:

```bash
python -m src.main scan /media/large-dataset -o dataset.json
python -m src.main analyze -m dataset.json -o recommendations.json
```

AI will analyze file types and recommend:
- Vision models for images/videos/PDFs
- Text models for documents/code
- Specialized models for audio/archives

### Use Case 2: Privacy-Conscious Local Analysis

You want analysis without sending data to cloud APIs:

```json
{
  "ai": {
    "mode": "local",
    "default_provider": "ollama"
  },
  "models": {
    "available_models": ["llama3.2", "llama3.2-vision"],
    "auto_download": true
  }
}
```

```bash
ollama serve
python -m src.main analyze -d ~/private-docs --provider ollama
```

All AI processing happens locally via Ollama.

### Use Case 3: Cost Optimization

You want to minimize API costs by using explicit mappings for common file types:

```json
{
  "models": {
    "explicit_mapping": {
      "image/jpeg": "llama3.2-vision",
      "image/png": "llama3.2-vision",
      "text/plain": "llama3.2"
    }
  },
  "analyze": {
    "ask_ai_for_models": true
  }
}
```

Common types use local models (free), rare types ask AI for recommendations.

### Use Case 4: Quality-First Analysis

You want the best models regardless of cost:

```json
{
  "models": {
    "available_models": [
      "gpt-4o-vision",
      "claude-3-5-sonnet-vision"
    ]
  },
  "ai": {
    "mode": "online",
    "default_provider": "openai"
  }
}
```

AI recommends premium models for optimal results.

## Troubleshooting

### "No AI provider configured"

Set up API keys:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

Or add to `data/config.json`:

```json
{
  "ai": {
    "openai_api_key": "sk-...",
    "anthropic_api_key": "sk-ant-..."
  }
}
```

### "Ollama connection failed"

Ensure Ollama is running:

```bash
ollama serve
```

Check connection:

```bash
curl http://localhost:11434/api/tags
```

### "Model not available"

For local models, pull them first:

```bash
ollama pull llama3.2
ollama pull llama3.2-vision
```

For online models, check your API subscription includes the model.

### "AI returned invalid JSON"

This can happen with:
- Very large batches (reduce `batch_size`)
- Complex prompts (simplify file metadata)
- Model limitations (try different provider)

## Best Practices

1. **Start with scan**: Always run scan first to collect quality metadata
2. **Use appropriate batch sizes**: 10-20 files for detailed analysis, 50+ for speed
3. **Cache wisely**: Let AI recommendations cache for common file types
4. **Mix explicit + AI**: Use explicit mappings for known types, AI for unknowns
5. **Monitor costs**: Use local models for bulk processing, premium models for critical files
6. **Iterate**: Review recommendations and adjust config based on results

## Future Enhancements

Planned features:

- [ ] Model download progress tracking
- [ ] Recommendation confidence scores
- [ ] Multi-model consensus (ask multiple AIs, compare results)
- [ ] Historical tracking of model performance
- [ ] Auto-tuning of model selection based on feedback
- [ ] Custom model definitions and capabilities

## See Also

- [AI Proposal Documentation](AI_PROPOSAL.md) - Structure proposal feature
- [Configuration Guide](../README.md#configuration) - Full config options
- [Model Registry](../src/models/registry.py) - Model tracking system
