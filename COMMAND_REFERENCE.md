# Quick Command Reference

## Installation

```bash
# Clone repository
git clone <repository-url>
cd airganizer

# Install Python dependencies
pip install -r requirements.txt

# Install system dependencies
apt-get install python3-magic binwalk  # Debian/Ubuntu
brew install libmagic binwalk          # macOS
```

## Basic Commands

### Run Complete Pipeline (Stage 1 + Stage 2)
```bash
python main.py \
  --config config.example.yaml \
  --src /path/to/source \
  --dst /path/to/destination
```

### Run with Output Files
```bash
python main.py \
  --config config.example.yaml \
  --src /path/to/source \
  --dst /path/to/destination \
  --output final_results.json \
  --stage1-output stage1_results.json
```

### Run with Verbose Logging
```bash
python main.py \
  --config config.example.yaml \
  --src /path/to/source \
  --dst /path/to/destination \
  --verbose
```

### Run Tests
```bash
python test_stages.py
```

## Python API Quick Examples

### Example 1: File Enumeration Only
```python
from src.config import Config
from src.stage1 import Stage1Scanner

config = Config('config.example.yaml')
scanner = Stage1Scanner(config)
result = scanner.scan('/path/to/files')

print(f"Files: {result.total_files}")
print(f"MIME types: {result.unique_mime_types}")
```

### Example 2: Complete Pipeline
```python
from src.config import Config
from src.stage1 import Stage1Scanner
from src.stage2 import Stage2Processor

config = Config('config.example.yaml')

# Stage 1
scanner = Stage1Scanner(config)
stage1 = scanner.scan('/path/to/files')

# Stage 2
processor = Stage2Processor(config)
stage2 = processor.process(stage1)

# Use results
for file in stage2.stage1_result.files:
    model = stage2.get_model_for_file(file)
    print(f"{file.file_name} → {model}")
```

### Example 3: Access File Metadata
```python
# After Stage 1
for file_info in stage1_result.files:
    print(f"\nFile: {file_info.file_name}")
    print(f"  MIME: {file_info.mime_type}")
    print(f"  Size: {file_info.file_size} bytes")
    
    if file_info.exif_data:
        print(f"  EXIF fields: {len(file_info.exif_data)}")
    
    if file_info.metadata:
        print(f"  Metadata: {file_info.metadata}")
    
    if file_info.binwalk_output:
        print(f"  Binwalk: Available")
```

## Configuration Snippets

### Minimal Config
```yaml
general:
  log_level: INFO

stage1:
  recursive: true
  include_hidden: false

models:
  discovery_method: config
  config_models:
    - name: llama2
      type: local
      provider: ollama
      model_name: llama2:latest
      capabilities: [text]
```

### Local Models Only
```yaml
models:
  discovery_method: local_enumerate
  ollama:
    base_url: http://localhost:11434
```

### Online Models
```yaml
models:
  discovery_method: config
  openai:
    api_key: sk-...
  anthropic:
    api_key: sk-ant-...
  config_models:
    - name: gpt4
      type: online
      provider: openai
      model_name: gpt-4
      capabilities: [text, vision]
```

## Common Workflows

### Workflow 1: Scan and Analyze
```bash
# 1. Scan files and collect metadata
python main.py --config config.yaml --src ./files --dst ./organized --stage1-output scan.json

# 2. Review scan results
cat scan.json | jq '.unique_mime_types'

# 3. Review model mappings
cat scan.json | jq '.mime_to_model_mapping'
```

### Workflow 2: Test Before Processing
```bash
# 1. Run test on small directory
python main.py --config config.yaml --src ./test_files --dst ./test_output --verbose

# 2. Review logs for issues
# 3. Adjust config if needed
# 4. Run on full directory
python main.py --config config.yaml --src ./all_files --dst ./organized
```

## Troubleshooting Commands

### Check Ollama Status
```bash
curl http://localhost:11434/api/tags
```

### Check Python Dependencies
```bash
pip list | grep -E "(magic|PyYAML|requests|openai|anthropic|Pillow|exifread)"
```

### Check System Dependencies
```bash
which file
which binwalk
python -c "import magic; print(magic.Magic(mime=True).from_file('test.txt'))"
```

### Debug Mode
```bash
python main.py --config config.yaml --src ./files --dst ./organized --verbose 2>&1 | tee debug.log
```

## File Locations

| File | Purpose |
|------|---------|
| `main.py` | Entry point, runs both stages |
| `src/stage1.py` | File enumeration & metadata |
| `src/stage2.py` | AI model discovery & mapping |
| `src/models.py` | Data models |
| `src/config.py` | Configuration handler |
| `src/metadata_extractor.py` | Metadata extraction |
| `config.example.yaml` | Example configuration |
| `test_stages.py` | Test script |

## Quick Tips

1. **Start Small:** Test on a small directory first
2. **Check Logs:** Use `--verbose` to see what's happening
3. **Save Results:** Use `--output` to save results for review
4. **Check Config:** Verify model settings before running
5. **Test Connectivity:** Ensure Ollama/APIs are accessible

## Status Checks

```python
# Check Stage 1 success
if stage1_result.total_files > 0:
    print("✓ Files found")
if not stage1_result.errors:
    print("✓ No errors")

# Check Stage 2 success
if stage2_result.available_models:
    print("✓ Models discovered")
if stage2_result.mime_to_model_mapping:
    print("✓ Mappings created")
if all(stage2_result.model_connectivity.values()):
    print("✓ All models connected")
```

## Next Steps After Restructure

The two-stage architecture is complete! Next development:

1. **Stage 3:** AI-powered file analysis
2. **Stage 4:** Organization strategy
3. **Stage 5:** File operations

## Documentation Index

- [STAGE_SPLIT.md](STAGE_SPLIT.md) - Architecture details
- [RESTRUCTURE_COMPLETE.md](RESTRUCTURE_COMPLETE.md) - What changed
- [VISUAL_COMPARISON.md](VISUAL_COMPARISON.md) - Before/after diagrams
- [README.md](README.md) - Main documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
