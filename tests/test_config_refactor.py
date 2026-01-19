#!/usr/bin/env python3
"""Test the new configuration system."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import Config
from model_discovery import ModelDiscovery


def test_config_loading():
    """Test that config loads with new structure."""
    print("Testing config loading...")
    
    # Create a test config
    test_config = {
        'directories': {
            'input_directory': '/tmp/input',
            'output_directory': '/tmp/output'
        },
        'models': {
            'model_mode': 'mixed',
            'discovery_method': 'auto',
            'openai': {
                'api_key_env': 'OPENAI_API_KEY',
                'auto_enumerate': True
            },
            'anthropic': {
                'api_key_env': 'ANTHROPIC_API_KEY',
                'auto_enumerate': True
            },
            'ollama': {
                'base_url': 'http://localhost:11434',
                'auto_enumerate': True
            }
        },
        'stage2': {
            'mapping_model': {
                'provider': 'openai',
                'model_name': 'gpt-4o'
            }
        }
    }
    
    config = Config(test_config)
    
    # Test property access
    assert config.model_mode == 'mixed', f"Expected 'mixed', got {config.model_mode}"
    assert config.discovery_method == 'auto', f"Expected 'auto', got {config.discovery_method}"
    
    print("✓ Config loading works")


def test_model_modes():
    """Test different model modes."""
    print("\nTesting model modes...")
    
    modes = ['online_only', 'local_only', 'mixed']
    
    for mode in modes:
        config_dict = {
            'models': {
                'model_mode': mode,
                'discovery_method': 'config',
                'openai': {'api_key_env': 'OPENAI_API_KEY'},
                'anthropic': {'api_key_env': 'ANTHROPIC_API_KEY'},
                'ollama': {'base_url': 'http://localhost:11434'}
            }
        }
        
        config = Config(config_dict)
        discovery = ModelDiscovery(config)
        
        assert discovery.model_mode == mode, f"Expected {mode}, got {discovery.model_mode}"
        print(f"  ✓ Mode '{mode}' works")
    
    print("✓ Model modes work")


def test_model_filtering():
    """Test model filtering by mode."""
    print("\nTesting model filtering...")
    
    from model_discovery import AIModel
    
    # Create test models
    models = [
        AIModel(
            name="gpt4o",
            type="online",
            provider="openai",
            model_name="gpt-4o",
            capabilities=["text", "image"],
            description="GPT-4o"
        ),
        AIModel(
            name="llama3_2_vision",
            type="local",
            provider="ollama",
            model_name="llama3.2-vision:latest",
            capabilities=["text", "image"],
            description="Llama 3.2 Vision"
        )
    ]
    
    # Test online_only
    config = Config({'models': {'model_mode': 'online_only'}})
    discovery = ModelDiscovery(config)
    filtered = discovery._filter_by_mode(models)
    assert len(filtered) == 1, f"Expected 1 online model, got {len(filtered)}"
    assert filtered[0].type == "online", "Expected online model"
    print("  ✓ online_only filtering works")
    
    # Test local_only
    config = Config({'models': {'model_mode': 'local_only'}})
    discovery = ModelDiscovery(config)
    filtered = discovery._filter_by_mode(models)
    assert len(filtered) == 1, f"Expected 1 local model, got {len(filtered)}"
    assert filtered[0].type == "local", "Expected local model"
    print("  ✓ local_only filtering works")
    
    # Test mixed
    config = Config({'models': {'model_mode': 'mixed'}})
    discovery = ModelDiscovery(config)
    filtered = discovery._filter_by_mode(models)
    assert len(filtered) == 2, f"Expected 2 models, got {len(filtered)}"
    print("  ✓ mixed filtering works")
    
    print("✓ Model filtering works")


def test_model_creation():
    """Test model creation helpers."""
    print("\nTesting model creation...")
    
    config = Config({
        'models': {
            'openai': {'api_key_env': 'OPENAI_API_KEY'},
            'anthropic': {'api_key_env': 'ANTHROPIC_API_KEY'},
            'ollama': {'base_url': 'http://localhost:11434'}
        }
    })
    
    discovery = ModelDiscovery(config)
    
    # Test OpenAI model creation
    openai_model = discovery._create_openai_model('gpt-4o')
    assert openai_model.type == "online"
    assert openai_model.provider == "openai"
    assert openai_model.model_name == "gpt-4o"
    assert "image" in openai_model.capabilities
    print("  ✓ OpenAI model creation works")
    
    # Test Anthropic model creation
    anthropic_model = discovery._create_anthropic_model('claude-3-5-sonnet-20241022')
    assert anthropic_model.type == "online"
    assert anthropic_model.provider == "anthropic"
    assert anthropic_model.model_name == "claude-3-5-sonnet-20241022"
    assert "image" in anthropic_model.capabilities
    print("  ✓ Anthropic model creation works")
    
    # Test Ollama model creation
    ollama_model = discovery._create_ollama_model('llama3.2-vision:latest')
    assert ollama_model.type == "local"
    assert ollama_model.provider == "ollama"
    assert ollama_model.model_name == "llama3.2-vision:latest"
    print("  ✓ Ollama model creation works")
    
    print("✓ Model creation works")


def test_backward_compatibility():
    """Test that old config format still works."""
    print("\nTesting backward compatibility...")
    
    old_config = {
        'models': {
            'available_models': [
                {
                    'name': 'gpt4o',
                    'type': 'online',
                    'provider': 'openai',
                    'model_name': 'gpt-4o',
                    'capabilities': ['text', 'image'],
                    'description': 'GPT-4o',
                    'api_key_env': 'OPENAI_API_KEY'
                }
            ]
        }
    }
    
    # Set API key for test
    os.environ['OPENAI_API_KEY'] = 'test-key'
    
    config = Config(old_config)
    discovery = ModelDiscovery(config)
    
    # This should use the old _discover_from_config path
    models = discovery._discover_from_config()
    
    assert len(models) == 1, f"Expected 1 model, got {len(models)}"
    assert models[0].name == 'gpt4o'
    assert models[0].type == 'online'
    
    print("✓ Backward compatibility works")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Configuration System Tests")
    print("=" * 60)
    
    try:
        test_config_loading()
        test_model_modes()
        test_model_filtering()
        test_model_creation()
        test_backward_compatibility()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
