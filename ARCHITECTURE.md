# System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AI FILE ORGANIZER                            │
│                           STAGE 1 SYSTEM                             │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                           USER INPUT                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Command Line Args:                                                  │
│    --config  → Configuration file path                               │
│    --src     → Source directory to scan                              │
│    --dst     → Destination directory                                 │
│    --output  → JSON output file (optional)                           │
│    --verbose → Enable debug logging                                  │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        CONFIGURATION LAYER                           │
│                          (src/config.py)                             │
├─────────────────────────────────────────────────────────────────────┤
│  • Load YAML configuration file                                      │
│  • Validate settings and set defaults                                │
│  • Provide typed access to configuration values                      │
│  • Handle general, stage1, and model settings                        │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      STAGE 1: FILE SCANNER                           │
│                         (src/stage1.py)                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────────────────────────────────────────┐         │
│  │  1. DIRECTORY TRAVERSAL                                 │         │
│  │     • Recursive directory walking                       │         │
│  │     • Apply exclusion rules (dirs, extensions)          │         │
│  │     • Handle symlinks based on config                   │         │
│  │     • Process hidden files if configured                │         │
│  └────────────────────────────────────────────────────────┘         │
│                          │                                            │
│                          ▼                                            │
│  ┌────────────────────────────────────────────────────────┐         │
│  │  2. FILE METADATA COLLECTION                            │         │
│  │     • Capture file name                                 │         │
│  │     • Get absolute file path                            │         │
│  │     • Detect MIME type (python-magic)                   │         │
│  │     • Get file size                                     │         │
│  │     • Track errors gracefully                           │         │
│  └────────────────────────────────────────────────────────┘         │
│                          │                                            │
│                          ▼                                            │
│  ┌────────────────────────────────────────────────────────┐         │
│  │  3. MIME TYPE EXTRACTION                                │         │
│  │     • Collect all MIME types from files                 │         │
│  │     • Create unique list                                │         │
│  │     • Sort for consistency                              │         │
│  │     • Count files per MIME type                         │         │
│  └────────────────────────────────────────────────────────┘         │
│                                                                       │
└───────────────────────────────────┬───────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    MODEL DISCOVERY SYSTEM                            │
│                    (src/model_discovery.py)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   METHOD 1   │  │   METHOD 2   │  │   METHOD 3   │             │
│  │    CONFIG    │  │    LOCAL     │  │    LOCAL     │             │
│  │              │  │  ENUMERATE   │  │   DOWNLOAD   │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         │                  │                  │                      │
│         │                  │                  │                      │
│         ▼                  ▼                  ▼                      │
│  ┌──────────────────────────────────────────────────────┐          │
│  │  Model Discovery Logic                               │          │
│  │                                                       │          │
│  │  • Read config file   • Query Ollama    • Query +    │          │
│  │  • Parse model defs   • List models     • Download   │          │
│  │  • Check API keys     • Detect caps     • List all   │          │
│  │  • Validate models    • Return list     • Return all │          │
│  └──────────────────────────────────────────────────────┘          │
│                             │                                        │
│                             ▼                                        │
│  ┌──────────────────────────────────────────────────────┐          │
│  │  Available Models List                               │          │
│  │  [AIModel, AIModel, AIModel, ...]                    │          │
│  │                                                       │          │
│  │  Each contains:                                      │          │
│  │    • name, type (online/local)                       │          │
│  │    • provider (openai/anthropic/ollama)              │          │
│  │    • model_name, capabilities                        │          │
│  │    • api_key_env (if online)                         │          │
│  └──────────────────────────────────────────────────────┘          │
│                                                                       │
└───────────────────────────────────┬───────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│              MIME-TO-MODEL MAPPING SYSTEM                            │
│                    (src/mime_mapper.py)                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Inputs:                                                             │
│    • List of unique MIME types                                       │
│    • List of available AI models                                     │
│    • Mapping model (orchestrator AI) [optional]                      │
│                                                                       │
│  ┌────────────────────────────────────────────────────────┐         │
│  │  AI-POWERED MAPPING (if orchestrator configured)       │         │
│  │                                                         │         │
│  │  1. Create prompt with:                                │         │
│  │     - Available models and capabilities                │         │
│  │     - MIME types to map                                │         │
│  │     - Requirements and constraints                     │         │
│  │                                                         │         │
│  │  2. Send to AI orchestrator:                           │         │
│  │     ┌─────────┐  ┌──────────┐  ┌────────┐            │         │
│  │     │ OpenAI  │  │ Anthropic│  │ Ollama │            │         │
│  │     └─────────┘  └──────────┘  └────────┘            │         │
│  │                                                         │         │
│  │  3. Parse JSON response:                               │         │
│  │     { "mime_type": "model_name", ... }                │         │
│  └────────────────────────────────────────────────────────┘         │
│                          │                                            │
│                          │ (fallback if AI fails)                    │
│                          ▼                                            │
│  ┌────────────────────────────────────────────────────────┐         │
│  │  HEURISTIC MAPPING (fallback or no orchestrator)       │         │
│  │                                                         │         │
│  │  • Image MIME types    → Vision models (llava/gpt-4v) │         │
│  │  • Text MIME types     → Text models (llama/gpt-4)    │         │
│  │  • Other types         → Most capable model           │         │
│  │  • Prefer local models → Cost optimization            │         │
│  └────────────────────────────────────────────────────────┘         │
│                          │                                            │
│                          ▼                                            │
│  ┌────────────────────────────────────────────────────────┐         │
│  │  MIME-to-Model Mapping                                 │         │
│  │  {                                                      │         │
│  │    "text/plain": "llama3.2",                           │         │
│  │    "image/jpeg": "llava",                              │         │
│  │    "application/pdf": "gpt-4",                         │         │
│  │    ...                                                  │         │
│  │  }                                                      │         │
│  └────────────────────────────────────────────────────────┘         │
│                                                                       │
└───────────────────────────────────┬───────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA MODELS LAYER                            │
│                         (src/models.py)                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────┐  ┌────────────────────┐                     │
│  │    FileInfo        │  │    ModelInfo       │                     │
│  ├────────────────────┤  ├────────────────────┤                     │
│  │ • file_name        │  │ • name             │                     │
│  │ • file_path        │  │ • type             │                     │
│  │ • mime_type        │  │ • provider         │                     │
│  │ • file_size        │  │ • model_name       │                     │
│  └────────────────────┘  │ • capabilities     │                     │
│                          │ • description      │                     │
│                          └────────────────────┘                     │
│                                                                       │
│  ┌──────────────────────────────────────────────────────┐          │
│  │              Stage1Result                            │          │
│  ├──────────────────────────────────────────────────────┤          │
│  │ • source_directory: str                              │          │
│  │ • total_files: int                                   │          │
│  │ • files: List[FileInfo]                              │          │
│  │ • errors: List[Dict]                                 │          │
│  │ • unique_mime_types: List[str]                       │          │
│  │ • available_models: List[ModelInfo]                  │          │
│  │ • mime_to_model_mapping: Dict[str, str]              │          │
│  │                                                       │          │
│  │ Methods:                                             │          │
│  │ • to_dict() → Convert to JSON-serializable dict      │          │
│  │ • extract_unique_mime_types()                        │          │
│  │ • set_models(models)                                 │          │
│  │ • set_mime_mapping(mapping)                          │          │
│  └──────────────────────────────────────────────────────┘          │
│                                                                       │
└───────────────────────────────────┬───────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          OUTPUT LAYER                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────┐              ┌────────────────────┐         │
│  │  Console Output    │              │   JSON Output      │         │
│  ├────────────────────┤              ├────────────────────┤         │
│  │ • Structured logs  │              │ • Complete data    │         │
│  │ • Progress info    │              │ • All files        │         │
│  │ • Summary stats    │              │ • All MIME types   │         │
│  │ • File samples     │              │ • All models       │         │
│  │ • Model list       │              │ • Full mapping     │         │
│  │ • Mapping display  │              │ • Serializable     │         │
│  └────────────────────┘              └────────────────────┘         │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    EXTERNAL INTEGRATIONS                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐                    │
│  │  OpenAI  │     │ Anthropic│     │  Ollama  │                    │
│  │   API    │     │   API    │     │   API    │                    │
│  ├──────────┤     ├──────────┤     ├──────────┤                    │
│  │ GPT-4    │     │ Claude-3 │     │ Llama3.2 │                    │
│  │ GPT-4V   │     │ Opus     │     │ LLaVA    │                    │
│  │          │     │ Sonnet   │     │ Mistral  │                    │
│  └──────────┘     └──────────┘     └──────────┘                    │
│                                                                       │
│  ┌──────────────────────────────────────────────────────┐          │
│  │           python-magic / libmagic                    │          │
│  │           (MIME type detection)                      │          │
│  └──────────────────────────────────────────────────────┘          │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      READY FOR STAGE 2                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Stage1Result object contains:                                       │
│    ✓ All files to analyze                                           │
│    ✓ Available AI models                                            │
│    ✓ Model assignments per MIME type                                │
│    ✓ Complete metadata for each file                                │
│                                                                       │
│  Next: Use assigned models to analyze each file                      │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
Source Directory
       │
       ├─► File 1 ──┐
       ├─► File 2   │
       ├─► File 3   ├──► Scanner ──► FileInfo objects ──┐
       ├─► File 4   │                                    │
       └─► File N ──┘                                    │
                                                          │
                                                          ▼
                                              ┌──────────────────────┐
                                              │  Stage1Result        │
                                              │                      │
                                              │  files: [...]        │
                                              └──────────────────────┘
                                                          │
                    ┌─────────────────────────────────────┴─────────┐
                    │                                               │
                    ▼                                               ▼
         Extract MIME types                            Discover Models
         ["text/plain",                                [Model1, Model2,
          "image/jpeg",                                 Model3, ...]
          "application/pdf"]                                  │
                    │                                         │
                    └──────────────┬──────────────────────────┘
                                   │
                                   ▼
                          Create AI Mapping
                          {
                            "text/plain": "llama3.2",
                            "image/jpeg": "llava",
                            "application/pdf": "gpt-4"
                          }
                                   │
                                   ▼
                        ┌────────────────────┐
                        │  Complete          │
                        │  Stage1Result      │
                        │  ready for Stage 2 │
                        └────────────────────┘
```

## Component Interaction

```
main.py
   │
   ├──► Config.load() ───────────────────────────┐
   │                                               │
   ├──► Stage1Scanner.scan()                      │
   │       │                                       │
   │       ├──► _scan_directory_recursive()       │
   │       ├──► _get_mime_type()                  │
   │       ├──► extract_unique_mime_types()       ▼
   │       │                                   Uses config
   │       └──► ModelDiscovery.discover()        settings
   │               │                               │
   │               ├──► _discover_from_config() ──┘
   │               ├──► _enumerate_ollama_models()
   │               └──► _download_ollama_model()
   │
   └──► MimeModelMapper.create_mapping()
           │
           ├──► _create_mapping_openai()
           ├──► _create_mapping_anthropic()
           ├──► _create_mapping_ollama()
           └──► _create_default_mapping()
```
