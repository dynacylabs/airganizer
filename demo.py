"""
Example demonstration of the chunking and organization flow.
This shows how the system would work without actually calling an AI.
"""

from airganizer.scanner import FileScanner
from airganizer.chunker import TreeChunker
import json


def demo_chunking():
    """Demonstrate the chunking process."""
    print("=" * 70)
    print("AIRGANIZER PHASE 1 DEMO: File Tree Chunking")
    print("=" * 70)
    
    # Scan the airganizer directory itself
    print("\n1. Scanning directory...")
    scanner = FileScanner('airganizer')
    tree = scanner.build_tree()
    
    tree_json = json.dumps(tree, indent=2)
    print(f"   Total tree size: {len(tree_json)} characters")
    
    # Demonstrate chunking with a small chunk size
    print("\n2. Chunking tree (max 500 chars per chunk)...")
    chunker = TreeChunker(max_chunk_size=500)
    chunks = chunker.chunk_tree(tree)
    
    print(f"   Created {len(chunks)} chunks\n")
    
    # Show each chunk
    for i, chunk in enumerate(chunks, 1):
        chunk_json = json.dumps(chunk, indent=2)
        print(f"\n--- Chunk {i} ({len(chunk_json)} chars) ---")
        print(chunk_json)
        print()
    
    # Explain the process
    print("\n" + "=" * 70)
    print("HOW THE AI ORGANIZATION WORKS:")
    print("=" * 70)
    print("""
1. Initial State:
   theoretical_structure = {"dirs": {}, "files": []}

2. Process Chunk 1:
   AI receives: chunk_1 + theoretical_structure
   AI returns: updated_structure_v1
   
3. Process Chunk 2:
   AI receives: chunk_2 + updated_structure_v1
   AI returns: updated_structure_v2
   
4. Process Chunk 3:
   AI receives: chunk_3 + updated_structure_v2
   AI returns: final_structure

The AI builds and refines the organization structure iteratively,
considering all files seen so far in each iteration.
""")
    
    # Show example theoretical structure
    print("=" * 70)
    print("EXAMPLE THEORETICAL STRUCTURE (what AI might generate):")
    print("=" * 70)
    
    example_structure = {
        "dirs": {
            "Source Code": {
                "dirs": {
                    "Python": {"dirs": {}, "files": []},
                    "Configuration": {"dirs": {}, "files": []}
                },
                "files": []
            },
            "Documentation": {
                "dirs": {},
                "files": []
            }
        },
        "files": []
    }
    
    print(json.dumps(example_structure, indent=2))
    print("\nNote: Files stay as empty arrays - placement happens in later phases!")


if __name__ == '__main__':
    demo_chunking()
