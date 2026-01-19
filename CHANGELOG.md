# Changelog

All notable changes to the AI File Organizer project.

## [2.0.0] - 2024 - Two-Stage Architecture

### 🎯 Major Architectural Change

Complete restructuring from single-stage to two-stage architecture with separation of concerns.

### ✨ Added

#### New Files
- `src/stage2.py` - New Stage 2 processor for AI operations
- `src/metadata_extractor.py` - Metadata extraction utilities
- `test_stages.py` - Comprehensive test script for both stages
- `STAGE_SPLIT.md` - Architecture documentation
- `RESTRUCTURE_COMPLETE.md` - Restructuring summary
- `VISUAL_COMPARISON.md` - Before/after visual comparison
- `COMMAND_REFERENCE.md` - Quick command reference
- `FINAL_SUMMARY.md` - Complete summary document

#### New Features
- **EXIF Data Extraction**: Automatic EXIF metadata extraction from images
- **File-Specific Metadata**: Dimensions for images, page counts for PDFs, line counts for text
- **Binwalk Integration**: Binary analysis for all files
- **Stage1Result Enhancement**: Added metadata fields to FileInfo
- **Stage2Result Class**: New result class wrapping Stage1Result with AI data
- **Command Line Options**: Added `--stage1-output` for separate stage results
- **Model Helper Method**: `Stage2Result.get_model_for_file()` convenience method

#### New Dependencies
- `Pillow>=10.0.0` - Image processing and metadata
- `exifread>=3.0.0` - EXIF data extraction
- `binwalk` (system tool, optional) - Binary analysis

### 🔧 Changed

#### src/models.py
- **Enhanced `FileInfo`**:
  - Added `exif_data: Dict[str, Any]`
  - Added `binwalk_output: str`
  - Added `metadata: Dict[str, Any]`

- **Simplified `Stage1Result`**:
  - Removed `available_models`
  - Removed `mime_to_model_mapping`
  - Removed `model_connectivity`
  - These are now in `Stage2Result`

- **Added `Stage2Result`**:
  - Wraps `Stage1Result`
  - Adds `available_models`
  - Adds `mime_to_model_mapping`
  - Adds `model_connectivity`
  - Provides `get_model_for_file()` helper

#### src/stage1.py
- **Removed**:
  - All AI model discovery code
  - MIME-to-model mapping logic
  - Model downloading logic
  - Connectivity verification logic
  - Imports for `model_discovery` and `mime_mapper`

- **Added**:
  - Import for `metadata_extractor`
  - EXIF data extraction for images
  - Metadata extraction based on MIME type
  - Binwalk execution for all files
  - Enhanced FileInfo construction with metadata

- **Simplified**:
  - Stage 1 now only handles file enumeration
  - Cleaner, more focused responsibility

#### main.py
- **Added**:
  - Import for `Stage2Processor`
  - Stage 2 execution after Stage 1
  - `--stage1-output` command line option
  - Enhanced output formatting for both stages
  - Separate summaries for each stage

- **Changed**:
  - Sequential execution: Stage 1 → Stage 2
  - `--output` now saves final Stage 2 results
  - More detailed progress reporting

#### requirements.txt
- Added `Pillow>=10.0.0`
- Added `exifread>=3.0.0`
- Added note about binwalk system tool

### 🎨 Improved

- **Separation of Concerns**: Clear distinction between file operations (Stage 1) and AI operations (Stage 2)
- **Modularity**: Each stage can be tested and used independently
- **Testability**: Easier to test individual components
- **Extensibility**: Simpler to add Stage 3+ for processing
- **Documentation**: Comprehensive documentation of new architecture
- **Error Handling**: Better error tracking and reporting
- **Logging**: More detailed and structured logging

### 📝 Documentation Updates

- Created comprehensive architecture documentation
- Added visual comparisons of before/after architecture
- Provided migration guide for existing code
- Added quick reference guides
- Enhanced code comments and docstrings

### 🔄 Migration Guide

**Before (v1.x):**
```python
scanner = Stage1Scanner(config)
result = scanner.scan('/path')
# Result has files, models, mappings all mixed
```

**After (v2.0):**
```python
# Stage 1: Files
scanner = Stage1Scanner(config)
stage1 = scanner.scan('/path')

# Stage 2: AI
processor = Stage2Processor(config)
stage2 = processor.process(stage1)

# Access files: stage2.stage1_result.files
# Access models: stage2.available_models
```

### ⚠️ Breaking Changes

1. **`Stage1Result` Structure Changed**:
   - `available_models` removed (now in `Stage2Result`)
   - `mime_to_model_mapping` removed (now in `Stage2Result`)
   - `model_connectivity` removed (now in `Stage2Result`)

2. **`FileInfo` Structure Enhanced**:
   - Added `exif_data` field
   - Added `binwalk_output` field
   - Added `metadata` field
   - Existing fields unchanged (backward compatible)

3. **Stage 1 Behavior Changed**:
   - No longer performs AI model operations
   - Returns results without AI model information
   - Must run Stage 2 separately for AI features

### ✅ Backward Compatibility

- Configuration files unchanged
- Model discovery unchanged
- MIME mapper unchanged
- Existing config.example.yaml still works
- Command line interface mostly unchanged (added `--stage1-output`)

### 🐛 Bug Fixes

None - this is a restructuring release, not a bug fix release.

### 🔒 Security

No security changes in this release.

### 🗑️ Deprecated

Nothing deprecated - clean restructure.

### 🚀 Performance

- **Potential Improvement**: Can run Stage 1 without AI setup overhead
- **Potential Improvement**: Can skip Stage 2 if AI models not needed
- **Trade-off**: Two-stage execution adds slight overhead but improves modularity

---

## [1.0.0] - 2024 - Initial Release

### Added

- Initial implementation of AI File Organizer
- Stage 1: Unified file scanning and AI model discovery
- Configuration system with YAML support
- Model discovery with 3 methods (config, local_enumerate, local_download)
- AI-powered MIME-to-model mapping
- Model downloading for Ollama
- Connectivity verification
- Support for local (Ollama) and online (OpenAI, Anthropic) models
- Comprehensive documentation
- Example configuration files
- Test scripts

### Features

- Recursive directory scanning
- MIME type detection using python-magic
- File exclusion rules (directories, extensions, hidden files)
- File size limits
- Symlink handling
- Error tracking and reporting
- JSON output support
- Verbose logging mode

---

## Version Numbering

- **Major version** (X.0.0): Significant architectural changes or breaking changes
- **Minor version** (x.X.0): New features, backward compatible
- **Patch version** (x.x.X): Bug fixes, backward compatible

## Links

- [Repository](https://github.com/your-repo/airganizer)
- [Documentation](README.md)
- [Architecture](STAGE_SPLIT.md)
- [Issues](https://github.com/your-repo/airganizer/issues)
