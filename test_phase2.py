#!/usr/bin/env python3
"""
Test script to verify Phase 2 implementation (without requiring AI API keys).

Tests all components except actual AI calls.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all modules can be imported."""
    print("=" * 70)
    print("TEST 1: Module Imports")
    print("=" * 70)
    
    try:
        from src.core import FileScanner, MetadataCollector, MetadataStore
        print("✓ Core modules imported")
        
        from src.core.models import DirectoryNode, ProposedStructure, FileItem
        print("✓ Data models imported")
        
        from src.ai import AIClient
        print("✓ AI client interface imported")
        
        from src.ai.prompts import create_initial_prompt, create_update_prompt
        print("✓ Prompt templates imported")
        
        from src.ai.proposer import StructureProposer
        print("✓ Structure proposer imported")
        
        from src.commands import propose_command
        print("✓ Commands imported")
        
        from src.config import Config
        print("✓ Configuration imported")
        
        print("\n✅ All imports successful!\n")
        return True
    except Exception as e:
        print(f"\n❌ Import failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_data_models():
    """Test data model creation and serialization."""
    print("=" * 70)
    print("TEST 2: Data Models")
    print("=" * 70)
    
    try:
        from src.core.models import DirectoryNode, ProposedStructure, FileItem
        
        # Create directory structure
        root = DirectoryNode(
            name="test_root",
            description="Test root directory",
            path="/test",
            rationale="Test rationale"
        )
        
        subdir = DirectoryNode(
            name="subdir",
            description="Test subdirectory",
            path="/test/subdir"
        )
        
        root.add_subdirectory(subdir)
        root.add_file("test.txt")
        
        print("✓ Created directory nodes")
        
        # Create proposed structure
        structure = ProposedStructure(root=root)
        structure.metadata['test'] = 'value'
        
        print("✓ Created proposed structure")
        
        # Test serialization
        json_str = structure.to_json()
        print("✓ Serialized to JSON")
        
        # Test deserialization
        loaded = ProposedStructure.from_json(json_str)
        print("✓ Deserialized from JSON")
        
        # Verify
        assert loaded.root.name == "test_root"
        assert len(loaded.root.subdirectories) == 1
        assert len(loaded.root.files) == 1
        print("✓ Data integrity verified")
        
        # Test FileItem
        file_item = FileItem(
            file_path="/path/to/file.txt",
            file_name="file.txt",
            mime_type="text/plain",
            file_size=1024
        )
        print("✓ Created FileItem")
        
        simple_str = file_item.to_simple_string()
        assert "file.txt" in simple_str
        print("✓ FileItem string conversion works")
        
        print("\n✅ All data model tests passed!\n")
        return True
    except Exception as e:
        print(f"\n❌ Data model test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_prompts():
    """Test prompt generation."""
    print("=" * 70)
    print("TEST 3: Prompt Generation")
    print("=" * 70)
    
    try:
        from src.core.models import FileItem, ProposedStructure, DirectoryNode
        from src.ai.prompts import (
            create_initial_prompt,
            create_update_prompt,
            extract_json_from_response
        )
        
        # Create test files
        files = [
            FileItem("doc1.pdf", "doc1.pdf", "application/pdf", 1024),
            FileItem("photo.jpg", "photo.jpg", "image/jpeg", 2048),
            FileItem("script.py", "script.py", "text/x-script.python", 512)
        ]
        
        # Test initial prompt
        prompt = create_initial_prompt(files, 1, 1)
        assert "doc1.pdf" in prompt
        assert "application/pdf" in prompt
        assert "JSON" in prompt
        print("✓ Initial prompt generated")
        
        # Test update prompt
        root = DirectoryNode("root", "Root", "/root")
        structure = ProposedStructure(root=root)
        
        update_prompt = create_update_prompt(files, structure, 2, 3)
        assert "photo.jpg" in update_prompt
        assert "CURRENT STRUCTURE" in update_prompt
        print("✓ Update prompt generated")
        
        # Test JSON extraction
        test_response = '```json\n{"test": "value"}\n```'
        extracted = extract_json_from_response(test_response)
        assert '"test"' in extracted
        print("✓ JSON extraction works")
        
        print("\n✅ All prompt tests passed!\n")
        return True
    except Exception as e:
        print(f"\n❌ Prompt test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """Test configuration system."""
    print("=" * 70)
    print("TEST 4: Configuration")
    print("=" * 70)
    
    try:
        from src.config import Config
        
        config = Config()
        
        # Test defaults
        default_provider = config.get('ai.default_provider')
        assert default_provider == 'openai'
        print("✓ Default configuration loaded")
        
        # Test set/get
        config.set('test.value', 123)
        assert config.get('test.value') == 123
        print("✓ Configuration set/get works")
        
        # Test nested get
        chunk_size = config.get('ai.chunk_size')
        assert chunk_size == 50
        print("✓ Nested configuration access works")
        
        print("\n✅ All configuration tests passed!\n")
        return True
    except Exception as e:
        print(f"\n❌ Configuration test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_structure_persistence():
    """Test saving and loading structures."""
    print("=" * 70)
    print("TEST 5: Structure Persistence")
    print("=" * 70)
    
    try:
        from src.core.models import DirectoryNode, ProposedStructure
        import tempfile
        import os
        
        # Create structure
        root = DirectoryNode(
            name="persistent",
            description="Test persistence",
            path="/persistent"
        )
        root.add_file("file1.txt")
        root.add_file("file2.txt")
        
        structure = ProposedStructure(root=root)
        structure.metadata['files'] = 2
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
            f.write(structure.to_json())
        
        print("✓ Saved structure to file")
        
        # Load from file
        with open(temp_path, 'r') as f:
            loaded = ProposedStructure.from_json(f.read())
        
        print("✓ Loaded structure from file")
        
        # Verify
        assert loaded.root.name == "persistent"
        assert len(loaded.root.files) == 2
        assert loaded.metadata['files'] == 2
        print("✓ Data persisted correctly")
        
        # Cleanup
        os.unlink(temp_path)
        
        print("\n✅ All persistence tests passed!\n")
        return True
    except Exception as e:
        print(f"\n❌ Persistence test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "PHASE 2 VERIFICATION TESTS" + " " * 27 + "║")
    print("║" + " " * 12 + "AI Structure Proposal System" + " " * 28 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    tests = [
        ("Imports", test_imports),
        ("Data Models", test_data_models),
        ("Prompts", test_prompts),
        ("Configuration", test_config),
        ("Persistence", test_structure_persistence)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}\n")
            results.append((name, False))
    
    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:12} - {name}")
    
    print("\n" + "=" * 70)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 70)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Phase 2 implementation is working correctly.\n")
        print("Note: Actual AI functionality requires API keys and libraries:")
        print("  pip install openai anthropic")
        print("  export OPENAI_API_KEY='your-key' or ANTHROPIC_API_KEY='your-key'")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the output above.\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
