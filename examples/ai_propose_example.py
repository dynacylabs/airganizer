"""Example: AI-Powered Structure Proposal

This example demonstrates how to use Airganizer's AI capabilities to propose
an organizational structure for your files.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import FileItem
from src.ai import create_structure_proposer


def example_with_test_data():
    """Example using the test_data directory."""
    print("=" * 70)
    print("EXAMPLE: AI Structure Proposal")
    print("=" * 70)
    
    # For this example, we'll use mock data
    # In real usage, you'd load from metadata or scan a directory
    files = [
        FileItem("documents/report.pdf", "report.pdf", "application/pdf", 1024000),
        FileItem("documents/notes.txt", "notes.txt", "text/plain", 2048),
        FileItem("images/photo1.jpg", "photo1.jpg", "image/jpeg", 512000),
        FileItem("images/photo2.png", "photo2.png", "image/png", 256000),
        FileItem("code/script.py", "script.py", "text/x-script.python", 4096),
        FileItem("code/main.js", "main.js", "application/javascript", 8192),
        FileItem("data/data.csv", "data.csv", "text/csv", 16384),
        FileItem("data/config.json", "config.json", "application/json", 512),
    ]
    
    print(f"\n📁 Example files to organize:")
    for f in files:
        print(f"  - {f.file_path} [{f.mime_type}]")
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("\n⚠️  Warning: No API key found!")
        print("This example requires an AI API key.")
        print("\nTo run this example:")
        print("  export OPENAI_API_KEY='your-key-here'")
        print("  # or")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        print("\nThen run:")
        print("  python examples/ai_propose_example.py")
        return
    
    # Determine provider based on available key
    provider = 'openai' if os.getenv('OPENAI_API_KEY') else 'anthropic'
    print(f"\n🤖 Using AI provider: {provider}")
    
    # Create proposer
    print(f"\n⏳ Creating structure proposer...")
    proposer = create_structure_proposer(
        provider=provider,
        chunk_size=10,  # Small chunks for this example
        temperature=0.3
    )
    
    # Generate proposal
    print(f"\n🎯 Generating proposal...")
    
    def progress(chunk, total, msg):
        print(f"   [{chunk}/{total}] {msg}")
    
    structure = proposer.propose_structure(files, progress_callback=progress)
    
    # Display results
    print("\n✅ Proposal generated!")
    print("\n" + "=" * 70)
    print("PROPOSED STRUCTURE")
    print("=" * 70)
    
    print(f"\nRoot: {structure.root.name}")
    print(f"Description: {structure.root.description}")
    if structure.root.rationale:
        print(f"Rationale: {structure.root.rationale}")
    
    print(f"\nCategories:")
    for subdir in structure.root.subdirectories:
        print(f"\n  📁 {subdir.name}/")
        print(f"     Description: {subdir.description}")
        if subdir.rationale:
            print(f"     Rationale: {subdir.rationale}")
    
    # Save structure
    output_path = "data/example_structure.json"
    proposer.save_structure(output_path)
    print(f"\n💾 Structure saved to: {output_path}")
    
    # Summary
    summary = structure.get_summary()
    print(f"\n📊 Summary:")
    print(f"   Total directories: {summary['total_directories']}")
    print(f"   Files analyzed: {len(files)}")


if __name__ == '__main__':
    example_with_test_data()
