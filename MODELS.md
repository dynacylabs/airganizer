# AI Model System Documentation

## Overview

The AI File Organizer uses a sophisticated model discovery and mapping system to intelligently select which AI model should analyze each file based on its MIME type.

## Architecture

### Components

1. **ModelDiscovery** (`src/model_discovery.py`)
   - Discovers available AI models based on configured method
   - Supports online APIs (OpenAI, Anthropic) and local models (Ollama)
   - Three discovery methods for different use cases

2. **MimeModelMapper** (`src/mime_mapper.py`)
   - Creates intelligent mappings between MIME types and AI models
   - Uses an AI "orchestrator" to recommend optimal model for each file type
   - Falls back to heuristic-based mapping if AI is unavailable

3. **AIModel** (data class in `model_discovery.py`)
   - Represents an AI model with capabilities and configuration
   - Tracks whether model is online/local and what it can process

## Model Discovery Methods

### Method 1: Config-Based (Recommended)

**Use when:** You know exactly which models you want to use and have API keys ready

**Configuration:**
```yaml
models:
  discovery_method: "config"
  available_models:
    - name: "gpt-4-vision"
      type: "online"
      provider: "openai"
      model_name: "gpt-4-vision-preview"
      api_key_env: "OPENAI_API_KEY"
      capabilities: ["text", "image"]
      description: "OpenAI GPT-4 with vision"
```

**Pros:**
- Full control over which models are used
- Mix online and local models
- Explicit API key management
- Best for production environments

**Cons:**
- Requires manual configuration
- Models must be specified in advance

### Method 2: Local Enumerate (Offline-First)

**Use when:** You want to use only local models and auto-discover what's available

**Configuration:**
```yaml
models:
  discovery_method: "local_enumerate"
  local_provider: "ollama"
  ollama:
    base_url: "http://localhost:11434"
```

**Pros:**
- Automatic discovery of installed models
- No API keys required
- Works completely offline
- Great for privacy-sensitive use cases

**Cons:**
- Only discovers already-installed models
- Limited to local inference
- Requires Ollama (or other provider) to be running

**Setup:**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull some models
ollama pull llama3.2
ollama pull llava

# Run the organizer
python main.py --config config.yaml --src ./data --dst ./organized
```

### Method 3: Local Download (Auto-Setup)

**Use when:** You want local-only inference but also want models auto-downloaded

**Configuration:**
```yaml
models:
  discovery_method: "local_download"
  local_provider: "ollama"
  ollama:
    base_url: "http://localhost:11434"
    auto_download_models:
      - "llama3.2:latest"
      - "llava:latest"
      - "mistral:latest"
```

**How it works:**
1. Discovers existing local models
2. Downloads models from auto_download_models list if missing
3. Creates MIME-to-model mapping
4. **Checks which models are required by the mapping**
5. **Downloads any additional required models not yet installed**
6. Verifies all models are accessible

**Pros:**
- Automatic model setup
- No API keys required
- Works offline after initial download
- Self-contained deployment
- **Ensures all required models are present**

**Cons:**
- Initial download can be large (GBs per model)
- Requires disk space
- Download time on first run

## MIME-to-Model Mapping

### AI-Powered Mapping

When a mapping model is configured, the system asks an AI to recommend which model should analyze each MIME type.

**Configuration:**
```yaml
models:
  mapping_model:
    type: "online"
    provider: "openai"
    model_name: "gpt-4"
    api_key_env: "OPENAI_API_KEY"
```

**How it works:**
1. System provides AI with list of available models and their capabilities
2. System provides list of unique MIME types found in files
3. AI analyzes and recommends optimal model for each MIME type
4. Recommendations consider:
   - Model capabilities (text, image, etc.)
   - File type requirements
   - Cost optimization (prefer local when appropriate)
   - Specialization (vision models for images, etc.)

**Example AI recommendation:**
```json
{
  "image/jpeg": "llava",           // Vision model for images
  "image/png": "llava",
  "application/pdf": "gpt-4",       // Advanced model for complex PDFs
  "text/plain": "llama3.2",         // Local model for simple text
  "text/html": "llama3.2",
  "application/json": "mistral"
}
```

### Heuristic Fallback Mapping

If no mapping model is configured, the system uses intelligent heuristics:

1. **For image MIME types** (`image/*`):
   - Prefer local vision models (llava, bakllava)
   - Fall back to online vision models (gpt-4-vision, claude-3-opus)

2. **For text MIME types** (`text/*`, `application/json`, `application/xml`):
   - Prefer local text models (llama, mistral)
   - Fall back to online text models (gpt-4, claude-3)

3. **For other types**:
   - Use most capable available model

## Supported Providers

### Online Providers

#### OpenAI
```yaml
- name: "gpt-4"
  type: "online"
  provider: "openai"
  model_name: "gpt-4"
  api_key_env: "OPENAI_API_KEY"
  capabilities: ["text"]
```

**Setup:**
```bash
export OPENAI_API_KEY="sk-..."
```

#### Anthropic (Claude)
```yaml
- name: "claude-3-opus"
  type: "online"
  provider: "anthropic"
  model_name: "claude-3-opus-20240229"
  api_key_env: "ANTHROPIC_API_KEY"
  capabilities: ["text", "image"]
```

**Setup:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Local Providers

#### Ollama (Recommended)
```yaml
local_provider: "ollama"
ollama:
  base_url: "http://localhost:11434"
```

**Setup:**
```bash
# Install
curl -fsSL https://ollama.com/install.sh | sh

# Start service
ollama serve

# Pull models
ollama pull llama3.2
ollama pull llava
ollama pull mistral
```

**Popular Models:**
- `llama3.2:latest` - General text analysis
- `llava:latest` - Vision + text analysis
- `mistral:latest` - Fast text analysis
- `codellama:latest` - Code analysis

## Model Capabilities

Models are tagged with capabilities that determine what they can process:

- **text**: Can analyze text-based content
- **image**: Can analyze images and visual content
- **audio**: Can analyze audio files (future)
- **video**: Can analyze video files (future)

The mapping system considers these capabilities when recommending models.

## Model Downloading & Verification

### Automatic Model Download

When using `local_download` discovery method, the system intelligently manages model availability:

**Phase 1: Initial Discovery**
- Checks for models in the `auto_download_models` list
- Downloads any that are missing

**Phase 2: Mapping-Based Download (NEW)**
- After creating MIME-to-model mapping
- Extracts unique models required by the mapping
- Checks if each required model exists locally
- Downloads missing models automatically
- Reports success/failure for each download

**Example Flow:**
```
1. Config specifies auto_download_models: [llama3.2, llava]
2. System downloads these if missing
3. AI creates mapping: {"image/jpeg": "llava", "text/plain": "mistral"}
4. System detects "mistral" is also needed
5. System downloads "mistral" automatically
6. All required models are now present
```

### Connectivity Verification

At the end of Stage 1, the system verifies connectivity to ALL models:

**Local Model Verification (Ollama)**
- Queries Ollama API for model list
- Confirms each required model exists
- Reports ✓ or ✗ for each model

**Online Model Verification**
- **OpenAI**: Tests API key and model access
- **Anthropic**: Validates API key configuration
- Reports connectivity status

**Readiness Check**
- Verifies all models in MIME-to-model mapping are accessible
- Reports any failures
- Warns if Stage 2 cannot proceed

**Output:**
```
Verifying AI model connectivity
============================================================
✓ llama3.2 is accessible
✓ llava is accessible
✓ gpt-4-vision is accessible
============================================================
✓ All 3 models are accessible
```

## Usage Examples

### Example 1: Production Setup with Online Models

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
      
    - name: "claude-3-opus"
      type: "online"
      provider: "anthropic"
      model_name: "claude-3-opus-20240229"
      api_key_env: "ANTHROPIC_API_KEY"
      capabilities: ["text", "image"]
```

### Example 2: Local-Only Setup

```yaml
models:
  discovery_method: "local_enumerate"
  local_provider: "ollama"
  
  # No mapping model - uses heuristics
  mapping_model: null
```

### Example 3: Hybrid Setup

```yaml
models:
  discovery_method: "config"
  
  mapping_model:
    type: "local"
    provider: "ollama"
    model_name: "llama3.2:latest"
  
  available_models:
    # Local models for cost-effective analysis
    - name: "llama3.2"
      type: "local"
      provider: "ollama"
      model_name: "llama3.2:latest"
      capabilities: ["text"]
      
    - name: "llava"
      type: "local"
      provider: "ollama"
      model_name: "llava:latest"
      capabilities: ["text", "image"]
    
    # Online model for complex cases
    - name: "gpt-4"
      type: "online"
      provider: "openai"
      model_name: "gpt-4"
      api_key_env: "OPENAI_API_KEY"
      capabilities: ["text"]
```

## Best Practices

1. **Start with config method** for production deployments
2. **Use local models** for high-volume processing to control costs
3. **Reserve online models** for complex analysis requiring advanced capabilities
4. **Configure mapping model** for intelligent optimization
5. **Test with small datasets** before processing large directories
6. **Monitor API costs** when using online models
7. **Keep Ollama updated** for best local model performance

## Troubleshooting

### "No AI models available"
- Check that Ollama is running (`ollama serve`)
- Verify models are installed (`ollama list`)
- Check API keys are set for online models
- Review configuration file syntax

### "Mapping model is not available"
- Verify API key environment variable is set
- Check internet connection for online models
- Ensure Ollama is running for local mapping models

### "Cannot connect to Ollama"
- Start Ollama: `ollama serve`
- Check URL in config matches Ollama address
- Verify port 11434 is not blocked by firewall

### "Required models not accessible"
- Check Ollama is running for local models
- Verify API keys for online models
- Review connectivity verification output
- Ensure models were downloaded successfully
- Check network connectivity for online APIs

### "Failed to download model"
- Verify Ollama is running
- Check disk space availability
- Ensure internet connection for model download
- Try manual download: `ollama pull <model-name>`

## Future Enhancements

- Support for additional providers (LlamaCPP, Transformers)
- Model performance tracking and optimization
- Cost estimation for online API usage
- Batch processing optimization
- Model caching and reuse
