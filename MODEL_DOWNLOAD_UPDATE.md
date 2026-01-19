# Stage 1 Enhancement: Model Download & Verification

## Overview

Stage 1 has been enhanced with intelligent model downloading and comprehensive connectivity verification to ensure all required AI models are available and accessible before proceeding to Stage 2.

## New Features

### 1. Mapping-Based Model Download

**Previous Behavior:**
- Only downloaded models from `auto_download_models` configuration list
- Could result in missing models if mapping required different models

**New Behavior:**
- Downloads models from `auto_download_models` (as before)
- **Creates MIME-to-model mapping**
- **Extracts unique models required by mapping**
- **Checks if required models exist locally**
- **Downloads any missing required models automatically**

**Example Scenario:**
```yaml
# Config specifies
auto_download_models:
  - "llama3.2:latest"
  - "llava:latest"

# AI creates mapping
{
  "text/plain": "llama3.2",
  "image/jpeg": "llava",
  "application/pdf": "mistral"  # Not in auto_download!
}

# System detects "mistral" is needed
# Automatically downloads "mistral"
# All required models now present
```

### 2. Model Existence Checking

**New Method: `_check_ollama_model_exists()`**
- Queries Ollama API for installed models
- Returns True/False for model existence
- Used before attempting downloads
- Prevents unnecessary re-downloads

**Flow:**
```
For each required model:
  1. Check if model exists locally
  2. If exists: Log success, continue
  3. If missing: Download model
  4. Verify download succeeded
```

### 3. Comprehensive Connectivity Verification

**New Method: `verify_model_connectivity()`**
- Tests connection to individual AI models
- Supports local (Ollama) and online (OpenAI, Anthropic) providers
- Returns connectivity status

**Verification Process:**

**Local Models (Ollama):**
- Query Ollama API for model list
- Check if specific model exists
- Report ✓ Connected or ✗ Failed

**Online Models (OpenAI):**
- Verify API key is set
- Test API access
- Report connectivity status

**Online Models (Anthropic):**
- Verify API key is set
- Validate API key configuration
- Report connectivity status

**New Method: `verify_all_models()`**
- Iterates through all available models
- Calls `verify_model_connectivity()` for each
- Returns dictionary mapping model name to status
- Provides summary statistics

### 4. Readiness Validation

**At End of Stage 1:**
- Checks if all models in MIME-to-model mapping are accessible
- Reports which models (if any) failed connectivity tests
- Warns if Stage 2 cannot proceed
- Provides clear status: ✓ Ready or ✗ Not Ready

## Code Changes

### src/model_discovery.py

**New Methods:**
```python
_check_ollama_model_exists(model_name: str) -> bool
    Check if Ollama model exists before downloading

download_required_models(mime_to_model_mapping, available_models) -> bool
    Download models needed by mapping (local_download mode only)

verify_model_connectivity(model: AIModel) -> bool
    Test connectivity to a specific model

verify_all_models(models: List[AIModel]) -> Dict[str, bool]
    Test connectivity to all models, return status map
```

### src/models.py

**Enhanced Stage1Result:**
```python
@dataclass
class Stage1Result:
    # ... existing fields ...
    model_connectivity: Dict[str, bool] = field(default_factory=dict)  # NEW
    
    def set_model_connectivity(self, connectivity: Dict[str, bool]) -> None:
        """Store connectivity test results"""
```

### src/stage1.py

**Enhanced Workflow:**
```python
# After MIME-to-model mapping:
1. Download required models
   model_discovery.download_required_models(mapping, models)

2. Verify connectivity to all models
   connectivity = model_discovery.verify_all_models(models)
   result.set_model_connectivity(connectivity)

3. Validate required models are accessible
   Check if all models in mapping are connected
   Report any failures
```

### main.py

**Enhanced Output:**
```python
# Display model connectivity status
for model_name, is_connected in model_connectivity.items():
    status = "✓ Connected" if is_connected else "✗ Failed"
    print(f"  {model_name}: {status}")

# Check readiness for Stage 2
if all_connected:
    print("✓ All required models are connected and ready")
else:
    print("✗ Some required models are not accessible")
```

## Updated Stage 1 Execution Flow

```
1. Load Configuration
2. Scan Directory for Files
3. Collect File Metadata
4. Extract Unique MIME Types
5. Discover Available Models
6. Create MIME-to-Model Mapping
7. ⭐ Download Required Models (if local_download mode)
   ├─ Check which models are required
   ├─ Verify if models exist
   └─ Download missing models
8. ⭐ Verify Model Connectivity
   ├─ Test all local models
   ├─ Test all online models
   └─ Report connectivity status
9. ⭐ Validate Readiness
   └─ Confirm all required models accessible
10. Package Results for Stage 2
```

## Output Changes

### Console Output

**Before:**
```
MIME-to-Model Mapping:
  text/plain -> llama3.2
  image/jpeg -> llava
```

**After:**
```
MIME-to-Model Mapping:
  text/plain -> llama3.2
  image/jpeg -> llava

============================================================
Ensuring required models are available
============================================================
Model llama3.2 (llama3.2:latest) already exists
Model llava (llava:latest) already exists
All required models are available

============================================================
Verifying AI model connectivity
============================================================
✓ llama3.2 is accessible
✓ llava is accessible
============================================================
✓ All 2 models are accessible

Model Connectivity Status:
  llama3.2: ✓ Connected
  llava: ✓ Connected

✓ All required models are connected and ready
```

### JSON Output

**Enhanced Structure:**
```json
{
  "source_directory": "/path/to/source",
  "total_files": 42,
  "files": [...],
  "unique_mime_types": [...],
  "available_models": [...],
  "mime_to_model_mapping": {
    "text/plain": "llama3.2",
    "image/jpeg": "llava"
  },
  "model_connectivity": {
    "llama3.2": true,
    "llava": true
  }
}
```

## Benefits

### 1. Automatic Model Management
- No manual model installation required
- System ensures all needed models are present
- Reduces setup friction

### 2. Early Failure Detection
- Identifies missing or inaccessible models before Stage 2
- Clear error messages for troubleshooting
- Prevents Stage 2 failures

### 3. Readiness Validation
- Confirms system is ready for Stage 2
- Tests both local and online connectivity
- Provides confidence before processing

### 4. Better User Experience
- Clear status indicators (✓/✗)
- Detailed logging of operations
- Helpful error messages

### 5. Robustness
- Handles partial model availability
- Graceful degradation
- Clear reporting of issues

## Usage Examples

### Example 1: Local Download Mode

```yaml
models:
  discovery_method: "local_download"
  local_provider: "ollama"
  ollama:
    auto_download_models:
      - "llama3.2:latest"
```

**What Happens:**
1. Downloads llama3.2 if missing
2. Discovers other installed models
3. Creates AI mapping (might choose other models)
4. Downloads any additional required models
5. Verifies all models accessible
6. Reports ready/not ready status

### Example 2: Hybrid Setup

```yaml
models:
  discovery_method: "config"
  available_models:
    - name: "local-llama"
      type: "local"
      provider: "ollama"
      model_name: "llama3.2:latest"
    - name: "gpt4"
      type: "online"
      provider: "openai"
      model_name: "gpt-4"
      api_key_env: "OPENAI_API_KEY"
```

**What Happens:**
1. Uses configured models (no download)
2. Creates AI mapping
3. Verifies Ollama connectivity (local)
4. Verifies OpenAI connectivity (online)
5. Reports status for each model
6. Confirms readiness

## Testing

**Updated test_stage1.py:**
- Tests model connectivity verification
- Displays connectivity status
- Shows readiness check results

**Run Test:**
```bash
python test_stage1.py
```

**Expected Output:**
```
RESULTS - MODEL CONNECTIVITY
============================================================
Models tested: 2
  llama3.2: ✓ Connected
  llava: ✓ Connected

Readiness: ✓ All required models ready
```

## Migration Notes

### For Existing Users

**No Breaking Changes:**
- Existing configurations continue to work
- New features activate automatically
- Backward compatible

**New Benefits:**
- Better error detection
- More reliable operation
- Clear readiness status

**Optional Enhancements:**
- Set discovery_method to "local_download" for automatic setup
- Review connectivity verification output
- Ensure API keys are set for online models

## Future Enhancements

Potential improvements:
- Parallel model downloads
- Download progress indicators
- Model size estimation
- Bandwidth throttling
- Retry logic for failed downloads
- Model caching strategies

## Conclusion

Stage 1 now provides end-to-end model management:
1. ✅ Discovers available models
2. ✅ Creates intelligent mappings
3. ✅ Downloads required models
4. ✅ Verifies connectivity
5. ✅ Validates readiness

This ensures Stage 2 can proceed with confidence that all required AI models are present and accessible.
