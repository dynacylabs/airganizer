#!/bin/bash
# Airganizer Phase 3 Test Script
# Run this to test the analyze functionality

set -e  # Exit on error

echo "🧪 Airganizer Phase 3 - Test Runner"
echo "===================================="
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not activated"
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

echo "✓ Virtual environment: $VIRTUAL_ENV"
echo ""

# Check Python version
PYTHON_VERSION=$(python --version 2>&1)
echo "✓ $PYTHON_VERSION"
echo ""

# Check if dependencies are installed
echo "📦 Checking dependencies..."
if python -c "import magic; import openai; import anthropic" 2>/dev/null; then
    echo "✓ All dependencies installed"
else
    echo "⚠️  Missing dependencies. Installing..."
    pip install -q -r requirements.txt
    echo "✓ Dependencies installed"
fi
echo ""

# Check for API keys
echo "🔑 Checking API keys..."
if [[ -n "$OPENAI_API_KEY" ]]; then
    echo "✓ OPENAI_API_KEY found"
    PROVIDER="openai"
elif [[ -n "$ANTHROPIC_API_KEY" ]]; then
    echo "✓ ANTHROPIC_API_KEY found"
    PROVIDER="anthropic"
else
    echo "❌ No API keys found!"
    echo ""
    echo "Please set one of the following:"
    echo "  export OPENAI_API_KEY='your-key-here'"
    echo "  export ANTHROPIC_API_KEY='your-key-here'"
    echo ""
    echo "Or to test with local AI (Ollama):"
    echo "  1. Install: curl https://ollama.ai/install.sh | sh"
    echo "  2. Start: ollama serve"
    echo "  3. Pull model: ollama pull llama3.2"
    echo ""
    exit 1
fi
echo ""

# Create data directory
mkdir -p data

# Test 1: Run the test script
echo "📝 Test 1: Running test_analyze.py"
echo "-----------------------------------"
python test_analyze.py
echo ""

# Test 2: Test scan command
echo "📝 Test 2: Scanning test_data directory"
echo "----------------------------------------"
python -m src scan test_data -o data/test_scan.json --no-binwalk
echo ""

# Test 3: Test propose command
echo "📝 Test 3: AI structure proposal"
echo "--------------------------------"
python -m src propose -m data/test_scan.json -o data/test_structure.json --provider $PROVIDER
echo ""

# Test 4: Test analyze command
echo "📝 Test 4: AI model recommendations"
echo "-----------------------------------"
python -m src analyze -m data/test_scan.json -o data/test_analysis.json --provider $PROVIDER
echo ""

# Show results
echo "📊 Results Summary"
echo "=================="
echo ""

if [ -f data/test_scan.json ]; then
    echo "Scan results (data/test_scan.json):"
    cat data/test_scan.json | python -m json.tool | grep -A 2 "total_files"
    echo ""
fi

if [ -f data/test_structure.json ]; then
    echo "Structure proposal (data/test_structure.json):"
    echo "  Directories proposed:"
    cat data/test_structure.json | python -m json.tool | grep '"name"' | head -5
    echo ""
fi

if [ -f data/test_analysis.json ]; then
    echo "Analysis results (data/test_analysis.json):"
    cat data/test_analysis.json | python -m json.tool | grep -A 10 '"summary"'
    echo ""
fi

echo "✨ All tests complete!"
echo ""
echo "Review the results in the data/ directory:"
echo "  - data/test_scan.json      - File metadata"
echo "  - data/test_structure.json - Proposed structure"
echo "  - data/test_analysis.json  - Model recommendations"
