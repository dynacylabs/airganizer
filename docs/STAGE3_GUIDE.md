# Stage 3: AI-Powered File Analysis

## Overview

Stage 3 analyzes each file discovered in Stage 1 using the AI models assigned in Stage 2. For every file, it generates:
- **Proposed filename**: A descriptive, meaningful filename
- **Description**: What's in the file (summary for documents, description for images, etc.)
- **Tags**: Keywords for categorization and search

## What Stage 3 Does

### For Each File:
1. Retrieves the file information from Stage 1 (metadata, MIME type, etc.)
2. Looks up which AI model was assigned to handle that file type (from Stage 2)
3. Sends the file and its metadata to the AI model
4. Receives back:
   - Proposed new filename
   - Detailed description
   - List of relevant tags
5. Stores all this information in a unified structure

### AI Model Interaction

Stage 3 knows how to interact with different AI providers:

#### **OpenAI (GPT-4, GPT-4o)**
- For images: Sends the image visually using vision API
- For text/documents: Sends metadata and context
- Returns structured JSON with filename, description, tags

#### **Anthropic (Claude 3)**
- For images: Uses Claude's vision capabilities
- For documents: Analyzes based on metadata
- Returns structured analysis

#### **Ollama (Local models like LLaVA, Llama 3.2 Vision)**
- For images: Sends to vision-capable local models
- For text: Uses local LLM for analysis
- Fully offline operation

## Output Structure

### Stage3Result

```python
Stage3Result(
    stage2_result: Stage2Result      # Contains all Stage 1 & 2 data
    file_analyses: List[FileAnalysis]  # Analysis for each file
    total_analyzed: int               # Successfully analyzed files
    total_errors: int                 # Files that failed analysis
)
```

### FileAnalysis (for each file)

```python
FileAnalysis(
    file_path: str                    # Original file path
    assigned_model: str               # Model used for analysis
    proposed_filename: str            # AI-suggested filename
    description: str                  # What's in the file
    tags: List[str]                   # Categorization tags
    analysis_timestamp: str           # When analyzed
    error: Optional[str]              # Error message if failed
)
```

### Unified File Data

Stage 3 provides a method to get **everything** about a file in one place:

```python
{
    "file_info": {
        # From Stage 1
        "file_name": "IMG_1234.jpg",
        "file_path": "/photos/IMG_1234.jpg",
        "mime_type": "image/jpeg",
        "file_size": 2457600,
        "exif_data": {
            "Make": "Canon",
            "DateTime": "2024:03:15 14:30:22",
            "GPSLatitude": [37, 46, 29.82]
        },
        "metadata": {
            "width": 4000,
            "height": 3000
        }
    },
    "assigned_model": "gpt4o",  # From Stage 2
    "analysis": {
        # From Stage 3
        "file_path": "/photos/IMG_1234.jpg",
        "assigned_model": "gpt4o",
        "proposed_filename": "golden-gate-bridge-sunset.jpg",
        "description": "Photo of the Golden Gate Bridge at sunset with vibrant orange sky and calm water below",
        "tags": ["bridge", "sunset", "golden-gate", "san-francisco", "landscape"]
    }
}
```

## Usage

### Basic Usage

```bash
# Run all three stages
python main.py \
  --config config.example.yaml \
  --src /path/to/files \
  --dst /path/to/organized \
  --stage3-output unified_results.json
```

### Skip Stage 3 (run only Stages 1 & 2)

```bash
python main.py \
  --config config.example.yaml \
  --src /path/to/files \
  --dst /path/to/organized \
  --skip-stage3
```

### Test with Limited Files

```bash
# Analyze only first 10 files (good for testing)
python main.py \
  --config config.example.yaml \
  --src /path/to/files \
  --dst /path/to/organized \
  --max-files 10 \
  --stage3-output test_results.json
```

### Command Line Options

- `--skip-stage3`: Skip AI file analysis (only run Stages 1 & 2)
- `--max-files N`: Limit analysis to first N files (useful for testing)
- `--stage3-output FILE`: Save unified results (all stages) to JSON file
- `--output FILE`: Save complete Stage 3 result object to JSON

## Example Output

### Console Output

```
============================================================
Starting Stage 3: AI-powered file analysis
============================================================
Processing 247 files
------------------------------------------------------------
File 1/247: vacation_photo.jpg
  Path: /photos/vacation_photo.jpg
  MIME: image/jpeg
  Size: 2457600 bytes
  Assigned model: gpt4o
  ✓ Analysis complete
    Proposed name: eiffel-tower-sunset-paris.jpg
    Description: Photo of the Eiffel Tower at sunset with pink and orange sky, taken from Trocadéro Gardens
    Tags: eiffel-tower, paris, sunset, france, landmark

------------------------------------------------------------
File 2/247: report_2024.pdf
  Path: /documents/report_2024.pdf
  MIME: application/pdf
  Size: 524288 bytes
  Assigned model: claude_3_5_sonnet
  ✓ Analysis complete
    Proposed name: q4-2024-financial-report.pdf
    Description: Financial report for Q4 2024 including revenue analysis, expense breakdown, and projections
    Tags: finance, report, q4, 2024, business

============================================================
Stage 3 complete!
  Total files: 247
  Successfully analyzed: 245
  Errors: 2
============================================================
```

### JSON Output (--stage3-output)

```json
{
  "summary": {
    "source_directory": "/path/to/files",
    "total_files": 247,
    "analyzed_files": 245,
    "errors": 2,
    "unique_mime_types": ["image/jpeg", "image/png", "application/pdf", "text/plain"],
    "available_models": [
      {
        "name": "gpt4o",
        "type": "online",
        "provider": "openai",
        "model_name": "gpt-4o",
        "capabilities": ["text", "image"]
      }
    ],
    "mime_to_model_mapping": {
      "image/jpeg": "gpt4o",
      "application/pdf": "claude_3_5_sonnet"
    }
  },
  "files": [
    {
      "file_info": {
        "file_name": "vacation_photo.jpg",
        "file_path": "/photos/vacation_photo.jpg",
        "mime_type": "image/jpeg",
        "file_size": 2457600,
        "exif_data": {
          "Make": "Canon",
          "DateTime": "2024:03:15 14:30:22"
        },
        "metadata": {
          "width": 4000,
          "height": 3000
        }
      },
      "assigned_model": "gpt4o",
      "analysis": {
        "file_path": "/photos/vacation_photo.jpg",
        "assigned_model": "gpt4o",
        "proposed_filename": "eiffel-tower-sunset-paris.jpg",
        "description": "Photo of the Eiffel Tower at sunset with pink and orange sky",
        "tags": ["eiffel-tower", "paris", "sunset", "france", "landmark"],
        "analysis_timestamp": "2026-01-19T15:30:45.123456"
      }
    }
  ]
}
```

## AI Model Prompt

The AI models receive a structured prompt like:

```
You are analyzing a file for organization purposes. Please analyze this file and provide:

1. A proposed new filename (descriptive, concise, keep extension)
2. A detailed description of the file's contents
3. Relevant tags/keywords for categorization

File Information:
- Current filename: vacation_photo.jpg
- MIME type: image/jpeg
- File size: 2457600 bytes
- EXIF data: {"Make": "Canon", "DateTime": "2024:03:15 14:30:22"}
- Additional metadata: {"width": 4000, "height": 3000}

Please respond in JSON format with the following structure:
{
  "proposed_filename": "descriptive-name-with-extension",
  "description": "Detailed description of what's in this file",
  "tags": ["tag1", "tag2", "tag3"]
}

Important:
- Keep the original file extension
- Make the filename descriptive but concise (max 50 chars)
- Description should be 2-3 sentences
- Provide 3-7 relevant tags
- Tags should be lowercase, single words or hyphenated phrases
```

For images, the actual image is also sent to vision-capable models.

## Error Handling

Stage 3 handles errors gracefully:

- **Model not available**: Marks file as error, continues with others
- **API timeout**: Logs error, continues processing
- **Invalid response**: Uses fallback values, logs warning
- **File read error**: Records error, skips file

All errors are tracked and reported in the final summary.

## Performance Considerations

### Speed
- Processing time depends on:
  - Number of files
  - API response times (online models)
  - File sizes (for images)
  - Local GPU performance (Ollama)

### Cost
- **Online models**: Each file costs API tokens
  - Images: ~1000-2000 tokens per analysis
  - Documents: ~500-1000 tokens per analysis
- **Local models**: Free but slower

### Tips
- Use `--max-files` for testing before full run
- Use local models for cost-effective analysis
- Use `--skip-stage3` if you only need file enumeration
- Enable caching to avoid re-analyzing files

## Integration with Future Stages

Stage 3 output will be used by Stage 4 (not yet implemented) to:
- Rename files to proposed filenames
- Organize files by tags
- Create database/index with descriptions
- Generate folder structure based on categories

## Use Cases

### Photography Organization
- Analyze photos by content
- Auto-tag by subject, location, time
- Propose meaningful names (e.g., "beach-sunset-2024.jpg")

### Document Management
- Summarize PDFs and documents
- Extract key topics as tags
- Suggest descriptive filenames

### Media Library
- Identify video content
- Tag by genre, theme, quality
- Organize by content type

### Mixed File Collections
- Unified analysis across file types
- Consistent tagging strategy
- Smart organization suggestions

## API Reference

### Stage3Processor

```python
processor = Stage3Processor(config, cache_manager)
result = processor.process(stage2_result, use_cache=True, max_files=None)
```

### Stage3Result Methods

```python
# Get analysis for specific file
analysis = result.get_analysis_for_file("/path/to/file.jpg")

# Get unified data for specific file (all stages combined)
unified = result.get_unified_file_data("/path/to/file.jpg")

# Get unified data for all files
all_unified = result.get_all_unified_data()
```

## Next Steps

After Stage 3, you have complete information about every file:
- What it contains
- How to name it
- How to categorize it
- Where it came from
- All its technical metadata

Stage 4 (future) will use this to actually reorganize your files.
