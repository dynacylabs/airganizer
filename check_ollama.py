#!/usr/bin/env python3
"""Check Ollama installation and status."""

import requests
import sys

def check_ollama():
    """Check if Ollama is running and list available models."""
    host = "http://localhost:11434"
    
    print("🔍 Checking Ollama status...")
    print("=" * 60)
    
    # Check if Ollama is running
    try:
        response = requests.get(f"{host}/api/version", timeout=5)
        print(f"✅ Ollama is running at {host}")
        if response.ok:
            print(f"   Version: {response.json().get('version', 'unknown')}")
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to Ollama at {host}")
        print("\nPlease start Ollama:")
        print("  ollama serve")
        return False
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
        return False
    
    print()
    
    # List available models
    try:
        response = requests.get(f"{host}/api/tags", timeout=5)
        response.raise_for_status()
        data = response.json()
        models = data.get('models', [])
        
        if models:
            print(f"📦 Available models ({len(models)}):")
            for model in models:
                name = model.get('name', 'unknown')
                size = model.get('size', 0) / (1024**3)  # Convert to GB
                print(f"   ✓ {name} ({size:.2f} GB)")
        else:
            print("⚠️  No models found!")
            print("\nDownload a model:")
            print("  ollama pull llama3.2:latest")
            return False
            
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        return False
    
    print()
    
    # Test a simple generation
    print("🧪 Testing model generation...")
    model_to_test = "llama3.2:latest"
    
    # Check if the model exists
    model_names = [m.get('name', '') for m in models]
    if model_to_test not in model_names:
        # Try without :latest suffix
        model_to_test = "llama3.2"
        if model_to_test not in model_names:
            print(f"⚠️  Model 'llama3.2' not found")
            print(f"   Available: {', '.join(model_names)}")
            if models:
                model_to_test = model_names[0]
                print(f"   Using first available model: {model_to_test}")
            else:
                return False
    
    try:
        test_data = {
            "model": model_to_test,
            "prompt": "Say 'Hello' and nothing else.",
            "stream": False,
            "options": {
                "num_predict": 10
            }
        }
        
        print(f"   Testing with model: {model_to_test}")
        response = requests.post(
            f"{host}/api/generate",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 404:
            print("❌ /api/generate endpoint not found (404)")
            print("   This might be an older Ollama version")
            print("   Try updating Ollama: brew upgrade ollama")
            return False
        
        response.raise_for_status()
        result = response.json()
        
        print(f"   ✅ Generation successful!")
        print(f"   Response: {result.get('response', '')[:100]}")
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"   Status code: {e.response.status_code}")
        print(f"   Response: {e.response.text[:200]}")
        return False
    except Exception as e:
        print(f"❌ Error testing generation: {e}")
        return False
    
    print()
    print("=" * 60)
    print("✅ All checks passed! Ollama is ready to use.")
    return True


if __name__ == '__main__':
    success = check_ollama()
    sys.exit(0 if success else 1)
