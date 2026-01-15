# Airganizer - Project Structure

## Complete File Tree

```
airganizer/
├── .git/                           # Git repository
├── .gitignore                      # Git ignore rules
├── .venv/                          # Python virtual environment
│
├── README.md                       # Main documentation
├── OVERVIEW.md                     # Detailed project overview
├── requirements.txt                # Python dependencies
├── install_binwalk.sh             # Binwalk installation script
├── demo.py                        # Interactive demonstration
│
├── src/                           # Main source code
│   ├── __init__.py               # Package initialization
│   ├── __main__.py               # Module entry point (python -m src)
│   ├── main.py                   # CLI implementation
│   └── core/                     # Core functionality modules
│       ├── __init__.py          # Core module exports
│       ├── scanner.py           # File enumeration (FileScanner)
│       ├── metadata_collector.py # Metadata extraction (MetadataCollector)
│       └── storage.py           # Data persistence (MetadataStore)
│
├── examples/                      # Usage examples
│   └── scan_example.py          # Example scanning script
│
├── test_data/                    # Sample test files
│   ├── sample_config.json       # JSON test file
│   ├── sample_script.py         # Python test file
│   └── sample_doc.md            # Markdown test file
│
└── data/                         # Output storage (generated)
    ├── metadata.json            # Default output file
    ├── test_metadata.json       # Test output
    └── demo_output.json         # Demo output
```

## File Descriptions

### Documentation Files

| File | Description |
|------|-------------|
| `README.md` | Main project documentation with installation and usage |
| `OVERVIEW.md` | Comprehensive technical overview and architecture |
| `requirements.txt` | Python package dependencies |
| `.gitignore` | Files to exclude from version control |

### Source Code Files

| File | Lines | Description |
|------|-------|-------------|
| `src/__init__.py` | 3 | Package version and metadata |
| `src/__main__.py` | 5 | Module entry point for `python -m src` |
| `src/main.py` | ~100 | Command-line interface implementation |
| `src/core/__init__.py` | 5 | Core module exports |
| `src/core/scanner.py` | ~60 | FileScanner class - recursive directory enumeration |
| `src/core/metadata_collector.py` | ~150 | MetadataCollector class - file metadata extraction |
| `src/core/storage.py` | ~90 | MetadataStore class - JSON persistence |

### Utility Files

| File | Description |
|------|-------------|
| `install_binwalk.sh` | Shell script to install binwalk |
| `demo.py` | Interactive demonstration script |
| `examples/scan_example.py` | Python API usage example |

### Test Files

| File | Type | Size |
|------|------|------|
| `test_data/sample_config.json` | JSON | 85 bytes |
| `test_data/sample_script.py` | Python | 156 bytes |
| `test_data/sample_doc.md` | Markdown | 156 bytes |

## Module Dependencies

```
main.py
  └─> core.FileScanner
  └─> core.MetadataCollector
  └─> core.MetadataStore

core.scanner (FileScanner)
  └─> pathlib.Path
  └─> os.walk

core.metadata_collector (MetadataCollector)
  └─> magic (python-magic)
  └─> subprocess (for binwalk)
  └─> core.storage.FileMetadata

core.storage (MetadataStore)
  └─> json
  └─> core.metadata_collector.FileMetadata
```

## Entry Points

### 1. Command-Line Interface
```bash
python -m src <directory> [options]
```

Entry: `src/__main__.py` → `src/main.py:main()`

### 2. Python API
```python
from src.core import FileScanner, MetadataCollector, MetadataStore
```

Entry: `src/core/__init__.py`

### 3. Demo Script
```bash
python demo.py
```

Entry: `demo.py:main()`

## Output Files (Generated)

| File | Description | Format |
|------|-------------|--------|
| `data/metadata.json` | Default scan output | JSON |
| `data/test_metadata.json` | Test scan output | JSON |
| `data/demo_output.json` | Demo script output | JSON |

## Code Statistics

- **Total Python Files**: 9
- **Total Lines of Code**: ~500
- **Core Modules**: 3 (scanner, metadata_collector, storage)
- **External Dependencies**: 1 (python-magic)
- **Optional Tools**: 1 (binwalk)

## Quick Start Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run on test data
python -m src test_data -v

# View output
cat data/metadata.json

# Run demo
python demo.py

# Scan your own directory
python -m src /path/to/your/directory
```

## Next Steps for Development

1. **Phase 2**: Add file hashing and duplicate detection
2. **Phase 3**: Integrate AI for categorization
3. **Phase 4**: Implement automatic organization
4. **Phase 5**: Add web interface and monitoring

---

**Generated**: January 15, 2026
