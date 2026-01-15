#!/bin/bash
# Airganizer Local Execution Script
# For macOS with Ollama (local models only)

set -e  # Exit on error

# Configuration
DIR="/Volumes/ssd"
OUTPUT_DIR="./data"
CHUNK_SIZE=100
PROVIDER="ollama"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Airganizer - Local AI File Organizer   ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo ""

# Check if directory exists
if [ ! -d "$DIR" ]; then
    echo -e "${YELLOW}⚠️  Warning: Directory $DIR does not exist${NC}"
    echo "Please update DIR variable in this script"
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Ollama is not running!${NC}"
    echo "Please start Ollama:"
    echo "  ollama serve"
    echo ""
    read -p "Press Enter once Ollama is running, or Ctrl+C to exit..."
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Phase 1: Scan
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}🔍 Phase 1: Scanning directory...${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo "Directory: $DIR"
echo "Output: $OUTPUT_DIR/metadata.json"
echo ""
echo -e "${YELLOW}Note: Including binwalk analysis (slower but more detailed)${NC}"
echo ""

python -m src.main scan "$DIR" \
  -o "$OUTPUT_DIR/metadata.json" \
  -v

echo -e "${GREEN}✅ Phase 1 complete!${NC}"
echo ""

# Phase 2: Propose Structure
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}🤖 Phase 2: AI Structure Proposal...${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo "Provider: $PROVIDER (local)"
echo "Chunk size: $CHUNK_SIZE files per batch"
echo "Output: $OUTPUT_DIR/proposed_structure.json"
echo ""
echo -e "${YELLOW}Note: First run will download models (5-10 min)${NC}"
echo ""

python -m src.main propose \
  -m "$OUTPUT_DIR/metadata.json" \
  -o "$OUTPUT_DIR/proposed_structure.json" \
  --provider "$PROVIDER" \
  --chunk-size "$CHUNK_SIZE"

echo -e "${GREEN}✅ Phase 2 complete!${NC}"
echo ""

# Phase 3: Analyze and Recommend Models
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}📊 Phase 3: Model Recommendations...${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo "Provider: $PROVIDER (local)"
echo "Output: $OUTPUT_DIR/analysis_results.json"
echo ""

python -m src.main analyze \
  -m "$OUTPUT_DIR/metadata.json" \
  -o "$OUTPUT_DIR/analysis_results.json" \
  --provider "$PROVIDER"

echo -e "${GREEN}✅ Phase 3 complete!${NC}"
echo ""

# Display Results
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              Results Summary               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${GREEN}📁 Proposed Directory Structure:${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
if command -v jq &> /dev/null; then
    jq -C '.structure | to_entries[] | {directory: .key, file_count: (.value.files | length)}' "$OUTPUT_DIR/proposed_structure.json"
else
    python -c "
import json
with open('$OUTPUT_DIR/proposed_structure.json') as f:
    data = json.load(f)
    for dir_name, info in data['structure'].items():
        print(f'{dir_name}: {len(info[\"files\"])} files')
"
fi
echo ""

echo -e "${GREEN}🎯 Model Recommendations Summary:${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
if command -v jq &> /dev/null; then
    echo "Unique models recommended:"
    jq -r '[.recommendations[].recommended_models[]] | unique | .[]' "$OUTPUT_DIR/analysis_results.json"
    echo ""
    echo "Recommendations by MIME type:"
    jq -r '.recommendations[] | "\(.mime_type): \(.recommended_models | join(", "))"' "$OUTPUT_DIR/analysis_results.json" | head -20
else
    python -c "
import json
with open('$OUTPUT_DIR/analysis_results.json') as f:
    data = json.load(f)
    models = set()
    for rec in data['recommendations']:
        models.update(rec['recommended_models'])
    print('Unique models recommended:')
    for model in sorted(models):
        print(f'  - {model}')
    print()
    print('Recommendations by MIME type:')
    mime_types = {}
    for rec in data['recommendations']:
        mime = rec['mime_type']
        if mime not in mime_types:
            mime_types[mime] = rec['recommended_models']
    for mime, models in list(mime_types.items())[:20]:
        print(f'{mime}: {', '.join(models)}')
"
fi
echo ""

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║            All Results Saved!              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""
echo "📄 Files created:"
echo "  - $OUTPUT_DIR/metadata.json (file listing)"
echo "  - $OUTPUT_DIR/proposed_structure.json (AI structure)"
echo "  - $OUTPUT_DIR/analysis_results.json (model recommendations)"
echo ""
echo "📖 View full results:"
echo "  cat $OUTPUT_DIR/proposed_structure.json | jq '.'"
echo "  cat $OUTPUT_DIR/analysis_results.json | jq '.'"
echo ""
echo -e "${GREEN}✅ Complete!${NC}"
