"""Local AI client support (Ollama, etc.)."""

import requests
from typing import Optional, Dict, Any, List
from ..ai.client import AIClient


class OllamaClient(AIClient):
    """Client for Ollama local AI models."""
    
    def __init__(self, host: str = "http://localhost:11434", model: str = None, auto_download: bool = True):
        """
        Initialize Ollama client.
        
        Args:
            host: Ollama server host
            model: Model to use (defaults to llama3.2:3b, auto-downloads if needed)
            auto_download: Automatically download model if not available
        """
        self.host = host.rstrip('/')
        self.auto_download = auto_download
        
        # Check if Ollama is running
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            response.raise_for_status()
            
            data = response.json()
            available_models = [m['name'] for m in data.get('models', [])]
            
            # Determine which model to use
            if model is None:
                # Default preference: llama3.2:3b (small, fast, capable)
                model = 'llama3.2:3b'
            
            # Check if model is available
            if model not in available_models:
                if self.auto_download:
                    print(f"   Model '{model}' not found locally")
                    print(f"   Downloading model (this may take 5-10 minutes)...")
                    if not self.pull_model(model):
                        # Try fallback to available models
                        if available_models:
                            print(f"   Download failed, using available model: {available_models[0]}")
                            model = available_models[0]
                        else:
                            raise ValueError(
                                f"Model '{model}' not available and download failed. "
                                f"Please manually run: ollama pull {model}"
                            )
                else:
                    # No auto-download, try to use available model
                    if available_models:
                        preferred_models = ['llama3.2:3b', 'mistral:7b', 'qwen2.5:7b']
                        for preferred in preferred_models:
                            if preferred in available_models:
                                model = preferred
                                break
                        if model not in available_models:
                            model = available_models[0]
                        print(f"   Model '{model}' not found, using: {model}")
                    else:
                        raise ValueError(
                            f"No models available. Please run: ollama pull llama3.2:3b"
                        )
            else:
                print(f"   Using model: {model}")
            
            self.model = model
            
        except Exception as e:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.host}. "
                f"Make sure Ollama is running: {e}"
            )
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None,
                 temperature: float = 0.7, max_tokens: int = 4000) -> str:
        """Generate a response using Ollama."""
        # Combine system prompt and user prompt for /api/generate endpoint
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        data = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        response = requests.post(
            f"{self.host}/api/generate",
            json=data,
            timeout=120
        )
        
        response.raise_for_status()
        result = response.json()
        
        return result['response']
    
    def list_models(self) -> List[str]:
        """List available models in Ollama."""
        response = requests.get(f"{self.host}/api/tags")
        response.raise_for_status()
        
        data = response.json()
        return [model['name'] for model in data.get('models', [])]
    
    def pull_model(self, model_name: str) -> bool:
        """Pull/download a model in Ollama."""
        try:
            data = {"name": model_name}
            response = requests.post(
                f"{self.host}/api/pull",
                json=data,
                stream=True,
                timeout=600
            )
            response.raise_for_status()
            
            # Stream the download progress
            for line in response.iter_lines():
                if line:
                    try:
                        progress_data = eval(line)  # Ollama sends JSON-like updates
                        status = progress_data.get('status', '')
                        if 'completed' in progress_data or 'total' in progress_data:
                            completed = progress_data.get('completed', 0)
                            total = progress_data.get('total', 1)
                            percent = (completed / total * 100) if total > 0 else 0
                            print(f"   Progress: {percent:.1f}% - {status}", end='\r')
                    except:
                        pass
            
            print(f"\n   ✓ Model '{model_name}' downloaded successfully")
            return True
            
        except Exception as e:
            print(f"\n   ✗ Failed to download model: {e}")
            return False
            response.raise_for_status()
            return True
        except Exception:
            return False
