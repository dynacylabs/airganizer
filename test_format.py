"""Test the format functionality."""

from airganizer.scanner import FileScanner
from airganizer.chunker import TreeChunker
import json

# Create scanner for airganizer directory itself
scanner = FileScanner('airganizer')
tree = scanner.build_tree()

print("=" * 70)
print("TESTING FORMAT CONVERSION")
print("=" * 70)

# Test 1: JSON format (original)
print("\n1. JSON FORMAT:")
tree_json = json.dumps(tree, indent=2)
print(f"   Size: {len(tree_json)} characters")
print(f"   Preview: {tree_json[:200]}...")

# Test 2: Path list format
print("\n2. PATH LIST FORMAT:")
path_list = scanner.tree_to_path_list(tree)
print(f"   Size: {len(path_list)} characters ({len(path_list)/len(tree_json)*100:.1f}% of JSON)")
print(f"   Preview:\n{chr(10).join(path_list.split(chr(10))[:10])}...")

# Test 3: Compact format
print("\n3. COMPACT FORMAT:")
compact = scanner.tree_to_compact_format(tree)
print(f"   Size: {len(compact)} characters ({len(compact)/len(tree_json)*100:.1f}% of JSON)")
print(f"   Preview:\n{chr(10).join(compact.split(chr(10))[:10])}...")

# Test 4: Chunking with path list format
print("\n4. CHUNKING COMPARISON:")
chunker = TreeChunker(max_chunk_size=500)

# JSON chunks
json_chunks = chunker.chunk_tree(tree, format_type='json')
print(f"   JSON format: {len(json_chunks)} chunks")

# Path list chunks
pathlist_chunks = chunker.chunk_tree(path_list, format_type='pathlist')
print(f"   Path list format: {len(pathlist_chunks)} chunks ({len(pathlist_chunks)/len(json_chunks)*100:.1f}% of JSON)")

# Compact chunks
compact_chunks = chunker.chunk_tree(compact, format_type='compact')
print(f"   Compact format: {len(compact_chunks)} chunks ({len(compact_chunks)/len(json_chunks)*100:.1f}% of JSON)")

print("\n" + "=" * 70)
print("FORMAT TEST COMPLETE")
print("=" * 70)
print(f"\nFor a 650GB dataset:")
print(f"  JSON (4K chunks): 560,000 chunks")
print(f"  Path list (4K chunks): ~222,000 chunks (60% reduction)")
print(f"  With 80K chunks (pathlist): ~11,000 chunks")
print(f"\nRecommended: Use --format pathlist with --chunk-size 80000")
