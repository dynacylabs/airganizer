# 🚀 Quick Start Guide - Airganizer Phase 2

## What is Airganizer?

Airganizer is an AI-powered file organization tool that:
1. **Scans** your files and collects metadata
2. **Analyzes** them with AI to propose an organizational structure
3. (Coming soon) **Organizes** them automatically

## Installation

```bash
# Clone or navigate to airganizer directory
cd /path/to/airganizer

# Install dependencies
pip install -r requirements.txt

# Set up AI API key (choose one)
export OPENAI_API_KEY='your-openai-key'
# OR
export ANTHROPIC_API_KEY='your-anthropic-key'
```

## Basic Workflow

### Step 1: Scan Your Files

```bash
# Scan a directory to collect file metadata
python -m src scan /path/to/messy/files -o data/my_files.json -v
```

This creates a JSON file with:
- File paths and names
- MIME types
- File sizes
- (Optional) Binwalk analysis

### Step 2: Propose Organization

```bash
# Use AI to propose an organizational structure
python -m src propose --metadata data/my_files.json
```

The AI will:
- Analyze your files in chunks
- Propose logical categories
- Create a hierarchical directory structure
- Explain its reasoning

### Step 3: Review Results

```bash
# View the proposed structure
cat data/proposed_structure.json | jq '.root.subdirectories[].name'

# See the full structure with descriptions
cat data/proposed_structure.json | jq '.root.subdirectories[] | {name, description}'
```

## Examples

### Example 1: Quick Test

```bash
# Use the included test data
python -m src scan test_data -o data/test.json
python -m src propose --metadata data/test.json
```

### Example 2: Real Directory

```bash
# Scan your Downloads folder
python -m src scan ~/Downloads -o data/downloads.json --no-binwalk

# Get AI proposal
python -m src propose --metadata data/downloads.json --chunk-size 100
```

### Example 3: Using Claude

```bash
# Use Anthropic Claude instead of OpenAI
export ANTHROPIC_API_KEY='your-key'
python -m src propose \
  --metadata data/downloads.json \
  --provider anthropic \
  --temperature 0.2
```

## Command Reference

### Scan Command

```bash
python -m src scan <directory> [options]

Options:
  -o, --output PATH       Output JSON file (default: data/metadata.json)
  --no-binwalk           Skip binwalk analysis (faster)
  -v, --verbose          Show detailed progress
```

### Propose Command

```bash
python -m src propose [options]

Options:
  -m, --metadata PATH    Use pre-scanned metadata file
  -d, --directory PATH   Scan directory directly
  -o, --output PATH      Output file (default: data/proposed_structure.json)
  --provider NAME        AI provider: openai, anthropic (default: openai)
  --chunk-size N         Files per AI call (default: 50)
  --temperature N        AI creativity 0.0-1.0 (default: 0.3)
```

## Python API

### Scanning Files

```python
from src.core import FileScanner, MetadataCollector, MetadataStore

scanner = FileScanner('/path/to/directory')
collector = MetadataCollector(use_binwalk=False)
store = MetadataStore('output.json')

for file_path in scanner.scan():
    metadata = collector.collect_metadata(file_path)
    store.add_metadata(metadata)

store.save()
```

### Proposing Structure

```python
from src.core import FileItem
from src.ai import create_structure_proposer

# Create file items
files = [
    FileItem("doc.pdf", "doc.pdf", "application/pdf", 1024),
    # ... more files
]

# Generate proposal
proposer = create_structure_proposer(provider='openai')

def show_progress(chunk, total, msg):
    print(f"[{chunk}/{total}] {msg}")

structure = proposer.propose_structure(files, progress_callback=show_progress)
proposer.save_structure('structure.json')

# Review
summary = structure.get_summary()
print(f"Created {summary['total_directories']} directories")
```

## Tips & Best Practices

### For Better Results

1. **Use metadata**: Scan first for better AI analysis
   ```bash
   python -m src scan dir -o data.json
   python -m src propose --metadata data.json
   ```

2. **Adjust chunk size**: Larger = fewer API calls but higher cost
   ```bash
   python -m src propose --metadata data.json --chunk-size 100
   ```

3. **Lower temperature**: More consistent structures
   ```bash
   python -m src propose --metadata data.json --temperature 0.1
   ```

### Cost Management

- Start with small directories to test
- Increase chunk-size to reduce API calls
- Use `--no-binwalk` for faster scans
- Review costs in your AI provider dashboard

### Troubleshooting

**"API key not found"**
```bash
export OPENAI_API_KEY='your-key'
# or
export ANTHROPIC_API_KEY='your-key'
```

**"Module not found"**
```bash
pip install openai anthropic
```

**"Too many tokens"**
```bash
# Increase chunk size
python -m src propose --metadata data.json --chunk-size 100
```

## What's Next?

### Current Features (Phase 1-2) ✅
- [x] File scanning and metadata collection
- [x] AI structure proposal
- [x] Multiple AI provider support
- [x] Iterative refinement

### Coming Soon (Phase 3-5)
- [ ] Content-based file analysis
- [ ] Structure refinement with content
- [ ] File assignment to directories
- [ ] Actual file organization
- [ ] Dry-run and undo capabilities

## Getting Help

- **Documentation**: See `docs/AI_PROPOSAL.md` for detailed guide
- **Examples**: Check `examples/` directory
- **Technical Details**: Read `OVERVIEW.md` and `PHASE2_COMPLETE.md`

## Quick Reference Card

```bash
# Full workflow
python -m src scan ~/Documents -o data/docs.json
python -m src propose --metadata data/docs.json
cat data/proposed_structure.json | jq '.root.subdirectories'

# One-liner (direct scan)
python -m src propose --directory ~/Documents

# With custom settings
python -m src propose \
  --metadata data/docs.json \
  --provider anthropic \
  --chunk-size 100 \
  --temperature 0.2 \
  -o data/my_structure.json
```

---

**Ready to organize your files? Start with:**
```bash
python -m src scan /path/to/your/files -o data/files.json
python -m src propose --metadata data/files.json
```

**Questions or issues?** Check the documentation in the `docs/` directory!
