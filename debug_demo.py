"""Test debug mode functionality."""

from airganizer.scanner import FileScanner
from airganizer.chunker import TreeChunker
import json

# Simulate what happens with debug mode
print("=" * 70)
print("DEBUG MODE EXAMPLE")
print("=" * 70)

print("\n[DEBUG] Initializing scanner...")
print("[DEBUG] Root path: /workspaces/airganizer/airganizer")

scanner = FileScanner('airganizer')

print("\n[DEBUG] Building file tree...")
tree = scanner.build_tree()

tree_json = json.dumps(tree)
print(f"[DEBUG] Tree size: {len(tree_json)} characters")
print(f"[DEBUG] Root files: {len(tree.get('files', []))}")
print(f"[DEBUG] Root directories: {len(tree.get('dirs', {}))}")

print("\n[DEBUG] Starting chunking process...")
print(f"[DEBUG] Chunk size: 500 characters")

chunker = TreeChunker(max_chunk_size=500)
chunks = chunker.chunk_tree(tree)

print(f"[DEBUG] Created {len(chunks)} chunks")
for i, chunk in enumerate(chunks, 1):
    chunk_json = json.dumps(chunk)
    print(f"[DEBUG] Chunk {i} size: {len(chunk_json)} chars")

print("\nProcessing 1 chunks...")
print("\nProcessing chunk 1/1...")

print("[DEBUG] Chunk 1 content preview:")
print(f"[DEBUG]   Files in chunk: {len(chunks[0].get('files', []))}")
print(f"[DEBUG]   Dirs in chunk: {len(chunks[0].get('dirs', {}))}")
print("[DEBUG] Sending to AI provider...")
print("[DEBUG] Ollama: Sending request to mistral:7b...")
print(f"[DEBUG] Ollama: Prompt length: 850 chars")
print("[DEBUG] Ollama: Using Metal/GPU acceleration (if available)")
print("[DEBUG] Ollama: Received response")
print("[DEBUG] Ollama: Response length: 345 chars")
print("[DEBUG] Ollama: Parsing JSON response...")
print("[DEBUG] Ollama: Successfully parsed JSON")
print("[DEBUG] Received response from AI")
print("[DEBUG] Current structure has 2 top-level categories")
print("  ✓ Structure updated")

print("\n" + "=" * 70)
print("Without --debug, you would only see:")
print("=" * 70)
print("Building file tree...")
print("Testing AI connection...")
print("✓ Connection successful\n")
print("Processing 1 chunks...")
print("\nProcessing chunk 1/1...")
print("  ✓ Structure updated")
