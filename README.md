# AI File Organizer (AIrganizer)

An intelligent file organization system that uses AI to automatically scan, analyze, categorize, and organize your files with zero manual effort.

## ✨ Features

### 🔍 Stage 1: File Scanning & Metadata Collection
- Recursive directory scanning with exclusion rules
- Comprehensive metadata extraction:
  - EXIF data from images (camera, GPS, timestamps)
  - File-specific metadata (dimensions, duration, page count)
  - Binwalk analysis for embedded data detection
- Hidden file and symlink support
- Intelligent file exclusion (by extension, directory, size)

### 🤖 Stage 2: AI Model Discovery & Mapping
- **Auto-discovery** of AI models from multiple providers
- **Centralized credentials** - configure API keys once per provider
- **Model modes**: online-only, local-only, or mixed
- **Intelligent MIME-to-model mapping** using AI recommendations
- **Automatic model download** for local deployment
- Support for OpenAI, Anthropic, and Ollama providers

### 🎯 Stage 3: AI-Powered File Analysis
- Analyzes each file with the most appropriate AI model
- Generates for every file:
  - **Proposed filename**: Descriptive, meaningful naming
  - **Description**: Content summary and context
  - **Tags**: Keywords for categorization
- Multi-provider support (GPT-4, Claude 3, LLaVA, etc.)
- Vision model support for images and visual content

### 📁 Stage 4: Taxonomic Structure Planning
- AI-powered hierarchical directory structure generation
- Multi-level categorization (not just flat folders)
- Intelligent file-to-category assignment with reasoning
- Scalable taxonomy that grows with your files

### 🚀 Stage 5: Physical File Organization
- Moves files to their designated locations
- Handles all three categories:
  - **Organized**: Successfully analyzed and categorized files
  - **Excluded**: Files excluded by rules (with detailed logs)
  - **Errors**: Files that failed analysis (with error logs)
- Dry-run mode for previewing changes
- Filename conflict resolution

### 💾 Advanced Features
- **Full resumability**: Permanent cache enables resuming from any interruption
- **Dual progress bars**: Real-time visual feedback on stage and overall progress
- **Comprehensive logging**: Debug, info, and error levels with detailed output
- **Flexible configuration**: YAML-based with CLI overrides
- **Privacy-focused**: Local model support for offline/private operation

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/dynacylabs/airganizer.git
cd airganizer

# Install Python dependencies
pip install -r requirements.txt

# Install system dependencies
sudo apt-get install libmagic1  # Debian/Ubuntu
# or
brew install libmagic  # macOS

# (Optional) Install Ollama for local AI models
curl -fsSL https://ollama.com/install.sh | sh
```

### Basic Usage

```bash
# Set API keys (for online models)
export OPENAI_API_KEY="your-api-key"
export ANTHROPIC_API_KEY="your-api-key"

# Copy and configure
cp config.example.yaml config.yaml
# Edit config.yaml with your preferences

# Run the complete pipeline
python main.py \
  --config config.yaml \
  --src /path/to/messy/files \
  --dst /path/to/organized/files
```

### 5-Minute Test Run

```bash
# Test with just 10 files
python main.py \
  --config config.yaml \
  --src /path/to/test/files \
  --dst /path/to/test/output \
  --max-files 10 \
  --verbose
```

## 📚 Documentation

- **[USAGE.md](USAGE.md)** - Complete usage guide with CLI reference and examples
- **[CONFIGURATION.md](CONFIGURATION.md)** - Comprehensive configuration reference
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Architecture, contributing guide, and development setup

## 🎯 Use Cases

- **Digital Hoarding Cleanup**: Organize years of accumulated files
- **Photo Library Management**: Automatically categorize photos by content, not just date
- **Document Organization**: Group documents by topic, project, or category
- **Privacy-Focused**: Use local AI models for sensitive files
- **Batch Processing**: Organize thousands of files automatically

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│  Stage 1: File Scanning & Metadata Collection      │
│  → Discovers all files, extracts metadata          │
│  → Cache: scan results, metadata, MIME types       │
└──────────────────┬──────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────┐
│  Stage 2: AI Model Discovery & Mapping             │
│  → Finds available AI models, maps MIME types      │
│  → Cache: model list, MIME→model mapping           │
└──────────────────┬──────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────┐
│  Stage 3: AI-Powered File Analysis                 │
│  → Analyzes each file with appropriate AI model    │
│  → Cache: AI analysis results (name, desc, tags)   │
└──────────────────┬──────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────┐
│  Stage 4: Taxonomic Structure Planning             │
│  → Creates hierarchical organization structure     │
│  → Cache: taxonomy tree, file assignments          │
└──────────────────┬──────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────┐
│  Stage 5: Physical File Organization               │
│  → Moves files to their organized locations        │
│  → Cache: move operations, conflict resolutions    │
└─────────────────────────────────────────────────────┘
```

### 💾 Cache System

The cache system provides **complete resumability** across all 5 stages:

- **Permanent cache**: No TTL - cache is valid until explicitly cleared
- **Stage-specific caching**: Each stage caches independently
- **Automatic resume**: Re-running continues from where it left off
- **Manual control**: `--clear-cache` to start fresh, `--no-cache` to bypass
- **Cache statistics**: `--cache-stats` to view what's cached

### 📊 Progress Tracking

Visual progress feedback with dual progress bars:

```
Stage 3: AI Analysis ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 45/100 files (45%)
📄 Analyzing: family_vacation_2023.jpg

Overall Progress    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 58% complete
```

- **Top bar**: Current stage progress with file count
- **Bottom bar**: Overall pipeline completion
- **File info**: Currently processing file name
- **Auto-disabled**: Turns off in debug mode for clean logs

## 🔧 Requirements

- Python 3.7+
- OpenAI API key (optional, for GPT models)
- Anthropic API key (optional, for Claude models)
- Ollama (optional, for local AI models)

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions welcome! See [DEVELOPMENT.md](DEVELOPMENT.md) for guidelines.

## 🙏 Acknowledgments

- Built with [Rich](https://github.com/Textualize/rich) for beautiful terminal UI
- Powered by OpenAI, Anthropic, and Ollama AI models
- Uses python-magic for file type detection

