#!/usr/bin/env python3
"""
Test script for the analyze command.
Tests the new AI model recommendation system.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test that all new modules can be imported."""
    print("Testing imports...")
    
    try:
        from src.config import Config
        print("✓ Config imported")
        
        from src.models.registry import ModelRegistry, ModelInfo
        print("✓ ModelRegistry imported")
        
        from src.ai.local_client import OllamaClient
        print("✓ OllamaClient imported")
        
        from src.ai.model_recommender import ModelRecommender
        print("✓ ModelRecommender imported")
        
        from src.commands.analyze import analyze_command
        print("✓ analyze_command imported")
        
        print("\n✅ All imports successful!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import failed: {e}")
        return False

def test_config():
    """Test configuration system."""
    print("\nTesting configuration system...")
    
    from src.config import Config
    
    config = Config()
    
    # Test mode detection
    print(f"  AI mode: {config.get('ai.mode', 'online')}")
    print(f"  Is online mode: {config.is_online_mode()}")
    print(f"  Is local mode: {config.is_local_mode()}")
    
    # Test model management
    print(f"  Auto-download: {config.should_auto_download()}")
    print(f"  Ask AI for models: {config.get('analyze.ask_ai_for_models', True)}")
    
    # Test available models
    available = config.get('models.available_models', [])
    print(f"  Available models: {len(available)} models")
    
    print("✅ Configuration system working")
    return True

def test_model_registry():
    """Test model registry."""
    print("\nTesting model registry...")
    
    from src.models.registry import ModelRegistry
    
    registry = ModelRegistry()
    
    # Get all models
    all_models = registry.get_all_models()
    print(f"  Total models in registry: {len(all_models)}")
    
    # Get vision models
    vision_models = registry.get_models_for_capability("vision")
    print(f"  Vision models: {len(vision_models)}")
    for model in vision_models[:3]:
        print(f"    - {model.name} ({model.provider})")
    
    # Get models for image files
    image_models = registry.get_models_for_file_type("image/jpeg")
    print(f"  Models for image/jpeg: {len(image_models)}")
    
    print("✅ Model registry working")
    return True

def test_model_recommender():
    """Test model recommender (mock test without API calls)."""
    print("\nTesting model recommender...")
    
    from src.ai.model_recommender import ModelRecommender, create_recommendation_prompt
    from src.models.registry import ModelRegistry
    from src.config import Config
    
    config = Config()
    registry = ModelRegistry()
    
    recommender = ModelRecommender(config, registry)
    
    # Test prompt creation
    test_files = [
        {
            "file_path": "/test/image.jpg",
            "mime_type": "image/jpeg",
            "size": 1024000
        },
        {
            "file_path": "/test/document.pdf",
            "mime_type": "application/pdf",
            "size": 2048000
        }
    ]
    
    available_models = registry.get_all_models()
    prompt = create_recommendation_prompt(test_files, available_models)
    
    print(f"  Generated prompt length: {len(prompt)} characters")
    print(f"  Prompt includes {len(test_files)} files")
    print(f"  Prompt includes {len(available_models)} available models")
    
    # Test explicit mapping
    config.set('models.explicit_mapping', {
        'image/jpeg': 'gpt-4o-vision',
        'application/pdf': 'claude-3-5-sonnet-vision'
    })
    
    recommendations = recommender.recommend_models(test_files)
    print(f"  Got recommendations for {len(recommendations)} files")
    
    for file_path, rec in list(recommendations.items())[:2]:
        print(f"    {file_path}:")
        print(f"      Primary model: {rec['primary_model']}")
        print(f"      Source: {rec['source']}")
    
    print("✅ Model recommender working")
    return True

def test_analyze_command_help():
    """Test that analyze command is registered in CLI."""
    print("\nTesting analyze command CLI registration...")
    
    from src.main import main
    import subprocess
    
    # Test help output
    result = subprocess.run(
        [sys.executable, '-m', 'src.main', 'analyze', '-h'],
        capture_output=True,
        text=True
    )
    
    if 'analyze' in result.stdout and 'model recommendations' in result.stdout.lower():
        print("  ✓ Analyze command registered in CLI")
        print("  ✓ Help text includes model recommendations")
        print("✅ CLI integration working")
        return True
    else:
        print("  ❌ Analyze command not properly registered")
        print(f"  Output: {result.stdout[:200]}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Airganizer Phase 3: AI Model Recommendations")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("Model Registry", test_model_registry()))
    results.append(("Model Recommender", test_model_recommender()))
    results.append(("CLI Integration", test_analyze_command_help()))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed!")
        print("=" * 60)
        print("\nYou can now use the analyze command:")
        print("  python -m src.main analyze --help")
        print("  python -m src.main analyze -d test_data")
        return 0
    else:
        print("⚠️ Some tests failed")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
