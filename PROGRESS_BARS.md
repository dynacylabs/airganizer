# Progress Bars Feature

## Overview

The AI File Organizer now includes dual progress bars that provide real-time visual feedback during processing. The progress display shows:

1. **Current Operation Info** - Details about the file or operation currently being processed
2. **Stage Progress Bar** - Progress within the current stage (e.g., 150/500 files analyzed)
3. **Overall Progress Bar** - Progress across all 5 stages (e.g., 3/5 stages complete)

## Visual Layout

```
┌─ Current Operation ────────────────────────────────────┐
│ [42/150] Analyzing: photo_2024_01_15.jpg              │
│ Path: /source/photos/photo_2024_01_15.jpg             │
│ MIME: image/jpeg                                        │
│ Size: 2458624 bytes                                     │
└────────────────────────────────────────────────────────┘

⠙ Stage 3: AI File Analysis    ━━━━━━━━╸━━━━━━━━━━  28%  42/150  ⏱ 00:02:15
⠙ Overall Progress              ━━━━━━━━━━━━━━━━━━  60%  3/5     ⏱ 00:05:30
```

## Features

### Dual Progress Tracking

- **Top Bar (Stage Progress)**: Tracks progress within the current stage
  - Completes to 100% for each stage
  - Shows items completed / total items
  - Displays estimated time remaining
  
- **Bottom Bar (Overall Progress)**: Tracks progress across all 5 stages
  - Each stage completion advances the bar by 20%
  - Shows stage X / 5
  - Displays estimated time remaining for entire pipeline

### Current Operation Display

Above the progress bars, a panel shows detailed information about what's currently being processed:

**Stage 1 - File Scanning:**
```
[25/100] Processing: document.pdf
Path: /source/documents/document.pdf
Size: 1048576 bytes
```

**Stage 2 - Model Discovery:**
```
Discovering available AI models...
or
Mapping 15 MIME types to models...
or
Verifying connectivity to 8 models...
```

**Stage 3 - AI File Analysis:**
```
[42/150] Analyzing: vacation_photo.jpg
Path: /source/photos/vacation_photo.jpg
MIME: image/jpeg
Size: 2458624 bytes
```

**Stage 4 - Taxonomy Planning:**
```
[Batch 2/5] Planning taxonomy for files 101-200
Batch size: 100 files
Total categories so far: 15
```

**Stage 5 - File Organization:**
```
[187/300] Moving organized file: report.pdf
Source: /source/docs/report.pdf
Target: Documents/Work/Reports/2024_Q1_report.pdf
```

## Progress Bar Behavior

### Stage-Specific Progress

Each stage reports progress differently based on its work:

1. **Stage 1 (File Scanning)**: Progress per file discovered
2. **Stage 2 (Model Discovery)**: 3 steps (discover → map → verify)
3. **Stage 3 (AI Analysis)**: Progress per file analyzed
4. **Stage 4 (Taxonomy Planning)**: Progress per batch processed
5. **Stage 5 (File Organization)**: Progress per file moved (organized + excluded + errors)

### Automatic Disabling

Progress bars are automatically disabled in debug mode because they interfere with debug logging output. Use `--verbose` for progress bars with INFO-level logging, or omit both flags for minimal output with progress bars.

```bash
# Progress bars enabled (default)
python main.py --config config.yaml --src source --dst dest

# Progress bars enabled with INFO logging
python main.py --config config.yaml --src source --dst dest --verbose

# Progress bars disabled (debug mode)
python main.py --config config.yaml --src source --dst dest --debug
```

## Configuration

Progress bars are controlled automatically:
- **Enabled**: When `--debug` flag is NOT present
- **Disabled**: When `--debug` flag is present

No configuration file changes needed.

## Implementation Details

### ProgressManager Class

Located in `src/progress.py`, the `ProgressManager` class handles:
- Creating and managing dual progress bars
- Updating file information display
- Stage progress tracking
- Overall pipeline progress tracking

### Integration Points

All stage processors accept an optional `progress_manager` parameter:

```python
# Stage 1
scanner = Stage1Scanner(config, cache_manager, progress_manager)

# Stage 2  
processor = Stage2Processor(config, cache_manager, progress_manager)

# Stage 3
processor = Stage3Processor(config, cache_manager, progress_manager)

# Stage 4
processor = Stage4Processor(config, cache_manager, progress_manager)

# Stage 5
processor = Stage5Processor(config, cache_manager, progress_manager)
```

### Context Manager Usage

The progress manager is used as a context manager to ensure proper cleanup:

```python
with progress_manager:
    # All stages run here
    stage1_result = scanner.scan(...)
    stage2_result = processor.process(...)
    # etc.
```

## Rich Library

Progress bars are powered by the [Rich](https://github.com/Textualize/rich) library, which provides:
- Beautiful terminal formatting
- Smooth progress bar animations
- Accurate time estimations
- Spinner animations
- Color support (when terminal supports it)

## Dependencies

Added to `requirements.txt`:
```
rich>=13.0.0
```

Install with:
```bash
pip install -r requirements.txt
```

## Usage Examples

### Basic Usage
```bash
python main.py --config config.yaml --src /data/unorganized --dst /data/organized
```

You'll see:
- Current file being processed
- Stage progress (e.g., "42/150 files analyzed")
- Overall progress (e.g., "3/5 stages complete")
- Time remaining estimates

### With Verbose Logging
```bash
python main.py --config config.yaml --src /data/unorganized --dst /data/organized --verbose
```

Progress bars show at the bottom, INFO logs appear above.

### Debug Mode (No Progress Bars)
```bash
python main.py --config config.yaml --src /data/unorganized --dst /data/organized --debug
```

Progress bars disabled, detailed DEBUG logs shown instead.

## Benefits

1. **Visual Feedback**: See exactly what's happening at all times
2. **Progress Estimates**: Know how long each stage will take
3. **Current File Info**: Understand which files are being processed
4. **Dual Context**: See both stage-level and pipeline-level progress
5. **Professional Appearance**: Modern, polished terminal UI
6. **No Configuration**: Works automatically with sensible defaults

## Technical Notes

### Performance Impact

Progress updates are efficient and add minimal overhead:
- Updates happen at most 4 times per second (refresh_per_second=4)
- No blocking operations
- Minimal CPU usage

### Terminal Compatibility

Progress bars work in:
- Modern terminal emulators (VS Code, iTerm2, Windows Terminal, etc.)
- SSH sessions
- tmux/screen sessions
- Standard bash/zsh shells

Fallback behavior:
- If terminal doesn't support colors, bars use ASCII characters
- If progress can't be displayed, silently disabled (no errors)

### Concurrent Operations

Progress tracking is NOT thread-safe. The current implementation assumes sequential processing, which matches the pipeline design. If parallel processing is added in the future, progress tracking would need synchronization.

## Future Enhancements

Potential improvements for future versions:
- Nested progress bars for sub-operations
- Configurable refresh rate
- Progress persistence across restarts
- Real-time statistics (files/second, MB/second)
- Stage-specific custom colors
- Export progress data to JSON/CSV

## Troubleshooting

### Progress bars not showing
- Check if `--debug` flag is present (disables progress)
- Verify `rich` library is installed: `pip list | grep rich`
- Try running with `--verbose` flag

### Progress bars look garbled
- Terminal may not support ANSI escape codes
- Try a different terminal emulator
- Check `TERM` environment variable

### Progress bars interfere with logging
- This is expected in debug mode
- Use `--verbose` instead of `--debug` for progress + logs
- Or use `--debug` to disable progress bars entirely
