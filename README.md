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

### Cache Configuration
- `cache.directory`: Directory for cache and temporary files (default: `.airganizer_cache`)
  - Used to store progress for resumability if the process is interrupted

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
- `stage1.output_file`: Output JSON file name (default: `file_metadata.json`)
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
   cache:
     directory: ".airganizer_cache"
   
   source:
     directory: "/home/user/Downloads"
     exclude:
       - ".*"
       - "__pycache__"
   
   destination:
     directory: "/home/user/OrganizedFiles"
   
   stage1:
     output_file: "downloads_metadata.json"
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
   cat downloads_metadata.json
   ```

## Roadmap

- ✅ **Stage 1**: File enumeration and metadata collection
- 🔲 **Stage 2**: AI-powered file analysis and categorization
- 🔲 **Stage 3**: File organization and moving
- 🔲 **Stage 4**: Duplicate detection and handling

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
