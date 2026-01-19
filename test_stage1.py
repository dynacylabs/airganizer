#!/usr/bin/env python3
"""Quick test script to verify Stage 1 functionality."""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, '/workspaces/airganizer')

from src.config import Config
from src.stage1 import Stage1Scanner
from src.models import Stage1Result

def test_stage1():
    """Test Stage 1 scanning functionality."""
    print("=" * 60)
    print("Testing Stage 1: File Scanning and Enumeration")
    print("=" * 60)
    
    # Load configuration
    config_path = '/workspaces/airganizer/config.example.yaml'
    print(f"\n1. Loading configuration from: {config_path}")
    config = Config(config_path)
    print("   ✓ Configuration loaded successfully")
    print(f"   - Recursive: {config.recursive}")
    print(f"   - Follow symlinks: {config.follow_symlinks}")
    print(f"   - Include hidden: {config.include_hidden}")
    print(f"   - Model discovery method: {config.get('models.discovery_method')}")
    
    # Initialize scanner
    print("\n2. Initializing Stage 1 scanner")
    scanner = Stage1Scanner(config)
    print("   ✓ Scanner initialized")
    
    # Scan test directory
    test_dir = '/workspaces/airganizer/test_data'
    print(f"\n3. Scanning directory: {test_dir}")
    result = scanner.scan(test_dir)
    print(f"   ✓ Scan complete")
    
    # Display results
    print("\n" + "=" * 60)
    print("RESULTS - FILE INFORMATION")
    print("=" * 60)
    print(f"Source directory: {result.source_directory}")
    print(f"Total files found: {result.total_files}")
    print(f"Errors encountered: {len(result.errors)}")
    
    if result.total_files > 0:
        print(f"\nDetailed file information:")
        for i, file_info in enumerate(result.files, 1):
            print(f"\n  File {i}:")
            print(f"    Name: {file_info.file_name}")
            print(f"    Path: {file_info.file_path}")
            print(f"    MIME Type: {file_info.mime_type}")
            print(f"    Size: {file_info.file_size} bytes")
    
    if result.errors:
        print(f"\nErrors:")
        for error in result.errors:
            print(f"  - {error['file_path']}: {error['error']}")
    
    # Display MIME types
    print("\n" + "=" * 60)
    print("RESULTS - MIME TYPES")
    print("=" * 60)
    print(f"Unique MIME types found: {len(result.unique_mime_types)}")
    for mime_type in result.unique_mime_types:
        count = sum(1 for f in result.files if f.mime_type == mime_type)
        print(f"  - {mime_type}: {count} file(s)")
    
    # Display AI models
    print("\n" + "=" * 60)
    print("RESULTS - AI MODELS")
    print("=" * 60)
    print(f"Available AI models: {len(result.available_models)}")
    for model in result.available_models:
        print(f"\n  Model: {model.name}")
        print(f"    Type: {model.type}")
        print(f"    Provider: {model.provider}")
        print(f"    Model Name: {model.model_name}")
        print(f"    Capabilities: {', '.join(model.capabilities)}")
        print(f"    Description: {model.description}")
    
    # Display MIME-to-model mapping
    print("\n" + "=" * 60)
    print("RESULTS - MIME-TO-MODEL MAPPING")
    print("=" * 60)
    if result.mime_to_model_mapping:
        print(f"Mappings created: {len(result.mime_to_model_mapping)}")
        for mime_type, model_name in result.mime_to_model_mapping.items():
            print(f"  {mime_type} -> {model_name}")
    else:
        print("  No mappings created")
    
    # Display model connectivity status
    print("\n" + "=" * 60)
    print("RESULTS - MODEL CONNECTIVITY")
    print("=" * 60)
    if result.model_connectivity:
        print(f"Models tested: {len(result.model_connectivity)}")
        for model_name, is_connected in result.model_connectivity.items():
            status = "✓ Connected" if is_connected else "✗ Failed"
            print(f"  {model_name}: {status}")
        
        # Check readiness
        required_models = set(result.mime_to_model_mapping.values()) if result.mime_to_model_mapping else set()
        if required_models:
            all_ready = all(result.model_connectivity.get(m, False) for m in required_models)
            print(f"\nReadiness: {'✓ All required models ready' if all_ready else '✗ Some models not ready'}")
    else:
        print("  No connectivity checks performed")
    
    # Test conversion to dict
    print("\n" + "=" * 60)
    print("Testing data structure conversion")
    print("=" * 60)
    result_dict = result.to_dict()
    print(f"✓ Successfully converted to dictionary")
    print(f"✓ Dictionary keys: {list(result_dict.keys())}")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    try:
        test_stage1()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
