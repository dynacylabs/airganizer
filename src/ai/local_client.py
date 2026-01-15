"""Local AI client support (Ollama, etc.)."""

import requests
from typing import Optional, Dict, Any, List
from ..ai.client import AIClient


class OllamaClient(AIClient):
    """Client for Ollama local AI models."""
    
    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3.2"):
        """
        Initialize Ollama client.
        
        Args:
            host: Ollama server host
            model: Model to use
        """
        self.host = host.rstrip('/')
        self.model = model
        
        # Check if Ollama is running
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            response.raise_for_status()
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
            return True
        except Exception:
            return False
