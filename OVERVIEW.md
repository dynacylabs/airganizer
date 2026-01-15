# Airganizer Project Overview

## Project Summary

Airganizer is an AI-powered file system organizing tool designed to analyze and organize files based on their metadata and content. This document provides a comprehensive overview of the current implementation and future roadmap.

## Current Implementation (Phase 1)

### Completed Features

✅ **Core Infrastructure**
- Project structure with modular design
- Python package setup with proper imports
- Configuration and dependency management

✅ **File Enumeration**
- Recursive directory scanning
- Hidden file/directory filtering
- Generator-based iteration for memory efficiency
- Path validation and error handling

✅ **Metadata Collection**
- File path and name extraction
- Exact MIME type detection using python-magic
- MIME encoding detection
- File size calculation
- Binwalk integration (optional)
- Comprehensive error handling

✅ **Data Storage**
- JSON-based metadata persistence
- Structured data format
- Timestamp tracking
- Summary statistics generation

✅ **Command-Line Interface**
- User-friendly CLI with argparse
- Multiple output options
- Verbose mode
- Progress tracking
- Pretty-printed summaries

## Architecture

### Module Structure

```
src/
├── __init__.py              # Package initialization
├── __main__.py              # Module entry point
├── main.py                  # CLI implementation
└── core/
    ├── __init__.py          # Core module exports
    ├── scanner.py           # File enumeration
    ├── metadata_collector.py # Metadata extraction
    └── storage.py           # Data persistence
```

### Key Components

#### 1. FileScanner (`core/scanner.py`)
**Purpose**: Enumerate all files in a directory recursively

**Key Methods**:
- `scan()` - Generator that yields file paths
- `get_all_files()` - Returns list of all files
- `count_files()` - Counts total files

**Features**:
- Filters hidden files/directories
- Path validation
- Memory-efficient iteration

#### 2. MetadataCollector (`core/metadata_collector.py`)
**Purpose**: Extract comprehensive metadata from files

**Key Methods**:
- `collect_metadata()` - Collects all metadata for a file
- `_get_mime_type()` - Determines MIME type and encoding
- `_run_binwalk()` - Executes binwalk analysis

**Features**:
- Deterministic MIME type detection
- Optional binwalk analysis
- Timeout protection
- Error recovery

**Data Collected**:
- File path (absolute)
- File name
- MIME type
- MIME encoding
- File size
- Binwalk output (optional)
- Error information (if any)

#### 3. MetadataStore (`core/storage.py`)
**Purpose**: Persist and retrieve metadata

**Key Methods**:
- `add_metadata()` - Add single metadata entry
- `add_batch()` - Add multiple entries
- `save()` - Write to JSON file
- `load()` - Read from JSON file
- `get_summary()` - Generate statistics

**Features**:
- JSON serialization
- Automatic directory creation
- Summary statistics
- Timestamp tracking

#### 4. CLI (`main.py`)
**Purpose**: Command-line interface for end users

**Features**:
- Directory validation
- Progress reporting
- Configurable output
- Summary display
- Error handling

## Data Format

### FileMetadata Structure

```python
@dataclass
class FileMetadata:
    file_path: str          # Absolute path to file
    file_name: str          # Base file name
    mime_type: str          # Exact MIME type
    mime_encoding: str      # Character encoding
    file_size: int          # Size in bytes
    binwalk_output: str     # Binwalk analysis (optional)
    error: str              # Error message (if any)
```

### JSON Output Format

```json
{
  "scan_date": "2026-01-15T17:40:15.319755",
  "total_files": 3,
  "files": [
    {
      "file_path": "/path/to/file.py",
      "file_name": "file.py",
      "mime_type": "text/x-script.python",
      "mime_encoding": "us-ascii",
      "file_size": 156,
      "binwalk_output": null,
      "error": null
    }
  ]
}
```

## Usage Examples

### 1. Basic CLI Usage

```bash
# Scan a directory
python -m src /path/to/directory

# With custom output
python -m src /path/to/directory -o custom.json

# Without binwalk (faster)
python -m src /path/to/directory --no-binwalk

# Verbose mode
python -m src /path/to/directory -v
```

### 2. Python API Usage

```python
from src.core import FileScanner, MetadataCollector, MetadataStore

# Initialize
scanner = FileScanner('/path/to/directory')
collector = MetadataCollector(use_binwalk=False)
store = MetadataStore('output.json')

# Process files
for file_path in scanner.scan():
    metadata = collector.collect_metadata(file_path)
    store.add_metadata(metadata)

# Save and summarize
store.save()
summary = store.get_summary()
```

### 3. Custom Processing

```python
from src.core import FileScanner, MetadataCollector

scanner = FileScanner('/path/to/directory')
collector = MetadataCollector(use_binwalk=True)

# Custom filtering and processing
for file_path in scanner.scan():
    metadata = collector.collect_metadata(file_path)
    
    # Custom logic based on MIME type
    if metadata.mime_type.startswith('image/'):
        # Process images
        pass
    elif metadata.mime_type.startswith('text/'):
        # Process text files
        pass
```

## Dependencies

### Core Dependencies
- **python-magic** (0.4.27): MIME type detection
  - Provides accurate, deterministic MIME type identification
  - Uses libmagic for file type detection

### Optional Dependencies
- **binwalk**: Deep binary file analysis
  - Installation: `sudo apt-get install binwalk`
  - Provides detailed information about embedded files/data
  - Can detect file signatures, compression, encryption

## Performance Considerations

### Memory Efficiency
- Generator-based file iteration (not loading all paths at once)
- Streaming JSON writes for large datasets
- Per-file processing (no batch loading)

### Speed Optimizations
- Optional binwalk (can be disabled for faster scans)
- Progress tracking for user feedback
- Timeout protection on external tools

### Scalability
- Handles directories with thousands of files
- Graceful error handling for inaccessible files
- No recursion limits (uses os.walk)

## Testing

### Test Data
Located in `test_data/` directory:
- `sample_script.py` - Python script (text/x-script.python)
- `sample_doc.md` - Markdown document (text/plain)
- `sample_config.json` - JSON file (application/json)

### Verification
Run the demo to verify functionality:
```bash
python demo.py
```

## Future Enhancements (Planned)

### Phase 2: Enhanced Analysis
- [ ] File hash calculation (MD5, SHA256)
- [ ] Extended attributes extraction
- [ ] Image metadata (EXIF data)
- [ ] Audio/video metadata
- [ ] Archive content inspection
- [ ] Duplicate detection

### Phase 3: AI Integration
- [ ] AI-powered file categorization
- [ ] Content-based similarity analysis
- [ ] Automatic tagging system
- [ ] Smart organization suggestions
- [ ] Pattern recognition

### Phase 4: Organization Features
- [ ] Automatic file moving/copying
- [ ] Rule-based organization
- [ ] Custom categorization schemes
- [ ] Conflict resolution
- [ ] Undo/rollback functionality

### Phase 5: Advanced Features
- [ ] Database backend (SQLite/PostgreSQL)
- [ ] Web interface
- [ ] Watch mode (monitor directories)
- [ ] Scheduled scans
- [ ] Report generation
- [ ] Plugin system

## Contributing

### Adding New Analyzers
To add a new file analyzer:

1. Create a new module in `src/analyzers/`
2. Implement analysis function
3. Integrate with MetadataCollector
4. Add to FileMetadata dataclass
5. Update JSON schema

### Adding New Storage Backends
To add a new storage backend:

1. Inherit from base storage class
2. Implement required methods
3. Add configuration options
4. Update CLI to support new backend

## Troubleshooting

### Common Issues

**Issue**: MIME type detection not working
- **Solution**: Ensure python-magic is installed correctly
- **Linux**: May need `libmagic1` package

**Issue**: Binwalk timeout
- **Solution**: Use `--no-binwalk` flag for large binary files
- **Alternative**: Increase timeout in `_run_binwalk()`

**Issue**: Permission errors
- **Solution**: Ensure read permissions on target directory
- **Alternative**: Run with appropriate user privileges

## License

[To be added]

## Contact

[To be added]

---

**Last Updated**: January 15, 2026
**Version**: 0.1.0
**Status**: Phase 1 Complete
