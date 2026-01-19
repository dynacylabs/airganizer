# Stage Architecture Update

## Overview

The AI File Organizer has been restructured from a single-stage to a two-stage architecture for better separation of concerns and modularity.

## New Two-Stage Design

### Stage 1: File Enumeration & Metadata Collection
**Location:** `src/stage1.py`

**Purpose:** Scan directories and collect comprehensive file metadata without any AI involvement.

**Responsibilities:**
- Recursive directory scanning
- MIME type detection
- EXIF data extraction (images)
- File-specific metadata (dimensions, pages, line counts, etc.)
- Binwalk analysis for embedded data
- Error tracking

**Output:** `Stage1Result` with:
- `files`: List[FileInfo] with metadata
- `unique_mime_types`: List[str]
- `total_files`: int
- `errors`: List[Dict]

### Stage 2: AI Model Discovery & Mapping
**Location:** `src/stage2.py`

**Purpose:** Discover AI models and create intelligent MIME-to-model mappings.

**Responsibilities:**
- AI model discovery (3 methods)
- MIME-to-model mapping using AI
- Model downloading (if needed)
- Connectivity verification

**Output:** `Stage2Result` with:
- `stage1_result`: Stage1Result (wrapped)
- `available_models`: List[ModelInfo]
- `mime_to_model_mapping`: Dict[str, str]
- `model_connectivity`: Dict[str, bool]

## Data Model Changes

### FileInfo (Enhanced)
```python
@dataclass
class FileInfo:
    file_name: str
    file_path: str
    mime_type: str
    file_size: int
    exif_data: Dict[str, Any] = field(default_factory=dict)      # NEW
    binwalk_output: str = ""                                      # NEW
    metadata: Dict[str, Any] = field(default_factory=dict)        # NEW
```

### Stage1Result (Simplified)
```python
@dataclass
class Stage1Result:
    source_directory: str
    total_files: int
    files: List[FileInfo]
    errors: List[Dict[str, str]]
    unique_mime_types: List[str] = field(default_factory=list)
    # REMOVED: available_models, mime_to_model_mapping, model_connectivity
```

### Stage2Result (NEW)
```python
@dataclass
class Stage2Result:
    stage1_result: Stage1Result
    available_models: List[ModelInfo] = field(default_factory=list)
    mime_to_model_mapping: Dict[str, str] = field(default_factory=dict)
    model_connectivity: Dict[str, bool] = field(default_factory=dict)
    
    def get_model_for_file(self, file_info: FileInfo) -> Optional[str]:
        """Get recommended model for a file based on its MIME type."""
        return self.mime_to_model_mapping.get(file_info.mime_type)
```

## Processing Flow

```
┌──────────────────────┐
│   Load Config        │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│    Stage 1           │
│  File Enumeration    │
│  & Metadata          │
├──────────────────────┤
│ • Scan directories   │
│ • Detect MIME types  │
│ • Extract EXIF       │
│ • Run binwalk        │
│ • Collect metadata   │
└──────┬───────────────┘
       │
       │ Stage1Result
       │
       ▼
┌──────────────────────┐
│    Stage 2           │
│  AI Model Discovery  │
│  & Mapping           │
├──────────────────────┤
│ • Discover models    │
│ • Map MIME→Model     │
│ • Download models    │
│ • Verify access      │
└──────┬───────────────┘
       │
       │ Stage2Result
       │
       ▼
┌──────────────────────┐
│  Stage 3+ (Future)   │
│  File Processing     │
└──────────────────────┘
```

## Usage Example

```bash
# Run both stages
python main.py \
  --config config.example.yaml \
  --src /path/to/files \
  --dst /path/to/destination \
  --output final_results.json \
  --stage1-output stage1_results.json
```

**Python API:**
```python
from src.config import Config
from src.stage1 import Stage1Scanner
from src.stage2 import Stage2Processor

# Configure
config = Config('config.yaml')

# Stage 1: File enumeration
scanner = Stage1Scanner(config)
stage1_result = scanner.scan('/path/to/files')

print(f"Files: {stage1_result.total_files}")
print(f"MIME types: {stage1_result.unique_mime_types}")

# Access file metadata
for file_info in stage1_result.files:
    print(f"{file_info.file_name}: {file_info.mime_type}")
    if file_info.exif_data:
        print(f"  EXIF: {file_info.exif_data}")
    if file_info.metadata:
        print(f"  Metadata: {file_info.metadata}")

# Stage 2: AI model mapping
processor = Stage2Processor(config)
stage2_result = processor.process(stage1_result)

print(f"Models: {len(stage2_result.available_models)}")
print(f"Mappings: {stage2_result.mime_to_model_mapping}")

# Get model for each file
for file_info in stage2_result.stage1_result.files:
    model = stage2_result.get_model_for_file(file_info)
    print(f"{file_info.file_name} → {model}")
```

## New Features

### Metadata Extraction
**Module:** `src/metadata_extractor.py`

#### EXIF Data Extraction
```python
def extract_exif_data(file_path: Path) -> Dict[str, Any]
```
Extracts EXIF metadata from images using `exifread` and `Pillow`.

#### MIME-Specific Metadata
```python
def extract_metadata_by_mime(file_path: Path, mime_type: str) -> Dict[str, Any]
```
Extracts metadata based on file type:
- **Images:** width, height, format, mode
- **PDFs:** page count, document properties
- **Text:** line count, character count

#### Binwalk Analysis
```python
def run_binwalk(file_path: Path) -> str
```
Runs binwalk to detect embedded files and data patterns.

## Migration Guide

### Old Code (Single Stage)
```python
scanner = Stage1Scanner(config)
result = scanner.scan('/path')

# Access everything from one result
files = result.files
models = result.available_models
mappings = result.mime_to_model_mapping
```

### New Code (Two Stages)
```python
# Stage 1: Files and metadata
scanner = Stage1Scanner(config)
stage1 = scanner.scan('/path')
files = stage1.files

# Stage 2: AI models
processor = Stage2Processor(config)
stage2 = processor.process(stage1)
models = stage2.available_models
mappings = stage2.mime_to_model_mapping

# Access stage1 data through stage2
all_files = stage2.stage1_result.files
```

## Dependencies

### New Python Packages
```
Pillow>=10.0.0          # Image processing
exifread>=3.0.0         # EXIF extraction
```

### System Tools
```bash
# Optional: binwalk for binary analysis
apt-get install binwalk   # Debian/Ubuntu
brew install binwalk      # macOS
```

## Testing

```bash
# Test both stages
python test_stages.py

# This creates test files and runs:
# 1. Stage 1: File enumeration + metadata
# 2. Stage 2: Model discovery + mapping
```

## Benefits

1. **Separation of Concerns**
   - Stage 1: File system operations
   - Stage 2: AI operations

2. **Modularity**
   - Can run Stage 1 standalone for metadata collection
   - Can skip Stage 2 if no AI models needed

3. **Testability**
   - Each stage can be tested independently
   - Mock data easily passed between stages

4. **Extensibility**
   - Easy to add Stage 3+ for processing
   - Clear interfaces between stages

5. **Performance**
   - Stage 1 can run without AI setup
   - Stage 2 only runs if needed

## Next Development

### Stage 3: AI-Powered Analysis
- Use mapped models to analyze files
- Extract semantic information
- Generate descriptions

### Stage 4: Organization Strategy
- Determine target structure
- Generate file destinations
- Handle conflicts

### Stage 5: File Operations
- Move/copy files
- Update metadata
- Generate reports

## Files Modified

- `src/models.py` - Updated FileInfo, Stage1Result; added Stage2Result
- `src/stage1.py` - Simplified, removed AI code, added metadata extraction
- `src/stage2.py` - NEW: All AI model operations
- `src/metadata_extractor.py` - NEW: Metadata extraction utilities
- `main.py` - Updated to run both stages sequentially
- `test_stages.py` - NEW: Test script for both stages
- `requirements.txt` - Added Pillow and exifread

## Summary

The restructuring provides a cleaner, more maintainable architecture with clear separation between file system operations (Stage 1) and AI operations (Stage 2). Each stage has a single, well-defined responsibility, making the codebase easier to understand, test, and extend.
