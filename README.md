# Airganizer

AI-powered file sorting utility that helps you organize files intelligently.

## Project Structure

```
airganizer/
├── src/
│   ├── __init__.py           # Package initialization
│   ├── config.py             # Configuration management
│   ├── file_enumerator.py    # File enumeration logic
│   ├── metadata_extractor.py # Metadata extraction
│   └── stage1.py             # Stage 1 processor
├── config.yaml               # Configuration file
├── airganizer.py             # Main entry point
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Stage 1: File Enumeration and Metadata Collection

Stage 1 scans a source directory recursively and collects comprehensive metadata for each file.

### Features

- **Recursive directory scanning** with include/exclude pattern support
- **Basic file metadata**: name, path, size, timestamps
- **MIME type detection**
- **File hash calculation** (optional, MD5)
- **Image EXIF data** extraction (for JPEG, PNG, etc.)
- **Audio metadata** extraction (MP3, FLAC, OGG, etc.)
- **Video metadata** extraction (MP4, AVI, MKV, etc.)
- **Document metadata** extraction (PDF, DOCX, XLSX, PPTX)

### Metadata Collected

For all files:
- File name and path
- File size (bytes and human-readable)
- File extension
- Creation, modification, and access times
- MIME type and media type

Additional metadata by file type:
- **Images**: EXIF data (camera info, GPS, dimensions, etc.)
- **Audio**: Duration, bitrate, sample rate, channels, tags (artist, album, etc.)
- **Video**: Duration, codec, resolution, frame rate, audio tracks
- **Documents**: Author, creation/modification dates, page/slide count, etc.

## Installation

1. **Clone or create the project directory**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the utility** by editing `config.yaml`:
   ```yaml
   source:
     directory: "/path/to/your/files"
   
   destination:
     directory: "/path/to/organized/files"
   ```

## Configuration

Edit `config.yaml` to customize the behavior:

### Global Settings
- `global.dry_run`: Run in dry run mode (default: `true`)
  - **true**: Build a plan without moving/modifying files - each stage updates the plan
  - **false**: Execute the plan (only use in final stage when ready to move files)
  - In dry run mode, operations are recorded in the plan file for review

### Cache Configuration
- `cache.directory`: Directory for cache and temporary files (default: `.airganizer_cache`)
  - Used to store progress for resumability if the process is interrupted
  - All generated files (output, cache) are placed here by default
  - Error log (`errors.log`) is stored here
- `cache.error_files_directory`: Directory for files that had processing errors (default: `.airganizer_cache/error_files`)
  - Files that cause errors are automatically moved here and excluded from further processing

### Source Configuration
- `source.directory`: Directory to scan
- `source.include`: Glob patterns for files to include (default: `["*"]`)
- `source.exclude`: Glob patterns for files to exclude (e.g., `[".*", "*.tmp"]`)

### Destination Configuration
- `destination.directory`: Where organized files will be placed (used in later stages)

### Metadata Extraction
- `metadata.extract_exif`: Extract EXIF data from images (default: `true`)
- `metadata.extract_audio_metadata`: Extract audio metadata (default: `true`)
- `metadata.extract_video_metadata`: Extract video metadata (default: `true`)
- `metadata.extract_document_metadata`: Extract document metadata (default: `true`)

### Stage 1 Options
- `stage1.output_file`: Output JSON file name (default: `stage1_metadata.json`)
  - Relative paths are placed in the cache directory
  - Use absolute paths to place output elsewhere
- `stage1.plan_file`: Plan file for file operations (default: `airganizer_plan.json`)
  - Tracks all planned file moves, renames, and operations
  - Updated by each stage, executed in final stage
- `stage1.calculate_hash`: Calculate MD5 hash for each file (default: `false`)
- `stage1.max_file_size`: Maximum file size to process in MB, 0 = no limit (default: `0`)
- `stage1.cache_interval`: Save progress every N files (default: `100`)
- `stage1.resume_from_cache`: Resume from cache if available (default: `true`)

## Usage

### Run Stage 1

```bash
python airganizer.py
```

Or with custom config:

```bash
python airganizer.py --config /path/to/config.yaml
```

Or with custom output file:

```bash
python airganizer.py --output /path/to/output.json
```

### Output

Stage 1 produces a JSON file (`file_metadata.json` by default) containing:

```json
{
  "stage": 1,
  "description": "File enumeration and metadata collection",
  "source_directory": "/path/to/source",
  "destination_directory": "/path/to/destination",
  "total_files": 1234,
  "files": [
    {
      "file_name": "photo.jpg",
      "file_path": "/path/to/source/photos/photo.jpg",
      "file_extension": ".jpg",
      "file_size": 2048576,
      "file_size_human": "1.95 MB",
      "created_time": "2024-01-15T10:30:00",
      "modified_time": "2024-01-15T10:30:00",
      "accessed_time": "2024-01-16T08:00:00",
      "mime_type": "image/jpeg",
      "encoding": null,
      "media_type": "image",
      "exif": {
        "Make": "Canon",
        "Model": "EOS 5D Mark IV",
        "DateTime": "2024:01:15 10:30:00",
        "width": 6720,
        "height": 4480,
        "format": "JPEG"
      }
    }
  ]
}
```

The tool also prints statistics including:
- Total files processed
- Total size of all files
- Breakdown by media type

### Resumability

Stage 1 automatically saves progress to a cache file (in `.airganizer_cache/` by default) every 100 files. If the process is interrupted:

1. **Automatic Resume**: Simply run the command again - it will automatically detect the cache and resume from where it left off
2. **Manual Cache Control**: 
   - Set `cache.directory` in config to change cache location
   - Set `stage1.cache_interval` to change how often progress is saved
   - Set `stage1.resume_from_cache: false` to start fresh (ignoring cache)
3. **Cache Cleanup**: The cache is automatically deleted after successful completion

### Error Handling

**Error Logging:**
- All errors are logged to `errors.log` in the cache directory
- Console output is kept clean - errors don't clutter the terminal
- Each error includes: timestamp, file path, error message, and action taken
- Review the error log after processing: `cat .airganizer_cache/errors.log`

**Error File Handling:**

If Stage 1 encounters an error processing a file:

**In Dry Run Mode (default):**
1. **Recorded in Plan**: The problematic file and error are recorded in the plan file
2. **Logged to File**: Error details are written to `errors.log`
3. **No Files Moved**: The original file remains in place
4. **Excluded from Metadata**: File is NOT included in the output metadata
5. **Available for Review**: You can review all errors in the plan and log files
6. **Processing Continues**: The error doesn't stop the entire process

**In Real Mode (dry_run: false):**
1. **File is Moved**: The problematic file is automatically moved to the error files directory
2. **Logged to File**: Error details are written to `errors.log`
3. **Directory Structure Preserved**: The relative path from the source directory is preserved
4. **Error Log Created**: An `.error.txt` file is created alongside the moved file with details
5. **Excluded from Metadata**: File is NOT included in the output metadata
6. **Excluded from Processing**: The file is marked as processed and won't be retried on resume
7. **Processing Continues**: The error doesn't stop the entire process

### The Plan File

Airganizer operates by building a **plan** of operations across stages:

1. **Stage 1**: Enumerates files, records errors in plan
2. **Future Stages**: Will add categorization and organization decisions to the plan
3. **Final Stage**: Executes the plan (set `dry_run: false`)

The plan file (`airganizer_plan.json`) contains:
- All file operations to be performed (moves, renames, etc.)
- Reasons for each operation
- File metadata
- Timestamps and stage completion status

**Review the plan before execution:**
```bash
cat .airganizer_cache/airganizer_plan.json
```

## Dependencies

### Core
- **PyYAML**: Configuration file parsing
- **tqdm**: Progress bars

### Optional (for enhanced metadata extraction)
- **Pillow**: Image EXIF data
- **mutagen**: Audio metadata
- **pymediainfo**: Video metadata
- **PyPDF2**: PDF metadata
- **python-docx**: Word document metadata
- **openpyxl**: Excel metadata
- **python-pptx**: PowerPoint metadata

If optional dependencies are not installed, the tool will still work but skip the corresponding metadata extraction (with an error message in the output).

## Example Workflow

1. **Edit configuration**:
   ```yaml
   global:
     dry_run: true  # Keep true until final execution
   
   cache:
     directory: ".airganizer_cache"
     error_files_directory: ".airganizer_cache/error_files"
   
   source:
     directory: "/home/user/Downloads"
     exclude:
       - ".*"
       - "__pycache__"
   
   destination:
     directory: "/home/user/OrganizedFiles"
   
   stage1:
     output_file: "stage1_metadata.json"
     plan_file: "airganizer_plan.json"
     calculate_hash: false
     cache_interval: 100
     resume_from_cache: true
   ```

2. **Run Stage 1**:
   ```bash
   python airganizer.py --config config.yaml
   ```
   
   Or with default config file:
   ```bash
   python airganizer.py
   ```

3. **If interrupted, simply run again** - it will resume from the cache automatically!

3. **If interrupted, simply run again** - it will resume from the cache automatically!

4. **Review the output**:
   ```bash
   cat .airganizer_cache/stage1_metadata.json
   ```

5. **Review the plan**:
   ```bash
   cat .airganizer_cache/airganizer_plan.json
   ```
   
   The plan shows all operations that will be performed when you execute it.

## Roadmap

- ✅ **Stage 1**: File enumeration and metadata collection
- ✅ **Dry Run Mode**: Build execution plan without moving files
- 🔲 **Stage 2**: AI-powered file analysis and categorization
- 🔲 **Stage 3**: Build organization strategy
- 🔲 **Final Stage**: Execute the plan (actual file moves)

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
