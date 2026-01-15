"""AI client for interacting with language models."""

import os
import json
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod


class AIClient(ABC):
    """Abstract base class for AI clients."""
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, 
                 temperature: float = 0.7, max_tokens: int = 4000) -> str:
        """Generate a response from the AI."""
        pass


class OpenAIClient(AIClient):
    """Client for OpenAI API."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            model: Model to use (default: gpt-4o)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = model
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not provided. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "OpenAI library not installed. Install with: pip install openai"
            )
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None,
                 temperature: float = 0.7, max_tokens: int = 4000) -> str:
        """Generate a response using OpenAI."""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content


class AnthropicClient(AIClient):
    """Client for Anthropic Claude API."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize Anthropic client.
        
        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            model: Model to use (default: claude-3-5-sonnet-20241022)
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.model = model
        
        if not self.api_key:
            raise ValueError(
                "Anthropic API key not provided. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "Anthropic library not installed. Install with: pip install anthropic"
            )
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None,
                 temperature: float = 0.7, max_tokens: int = 4000) -> str:
        """Generate a response using Anthropic Claude."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt if system_prompt else "You are a helpful assistant.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return message.content[0].text


class OllamaClient(AIClient):
    """Client for local Ollama models."""
    
    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3.2"):
        """
        Initialize Ollama client.
        
        Args:
            host: Ollama server host (default: http://localhost:11434)
            model: Model to use (default: llama3.2)
        """
        self.host = host.rstrip('/')
        self.model = model
        
        # Test connection
        try:
            import requests
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code != 200:
                raise ConnectionError(f"Cannot connect to Ollama at {self.host}")
        except Exception as e:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.host}. "
                f"Make sure Ollama is running. Error: {e}"
            )
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None,
                 temperature: float = 0.7, max_tokens: int = 4000) -> str:
        """Generate a response using Ollama."""
        import requests
        
        # Combine system and user prompt for Ollama
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        payload = {
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
            json=payload,
            timeout=120
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"Ollama API error: {response.text}")
        
        result = response.json()
        return result.get("response", "")
    
    def list_models(self) -> List[str]:
        """List available Ollama models."""
        import requests
        
        response = requests.get(f"{self.host}/api/tags")
        if response.status_code == 200:
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        return []
    
    def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama library."""
        import requests
        
        print(f"Pulling model {model_name}...")
        payload = {"name": model_name, "stream": False}
        
        response = requests.post(
            f"{self.host}/api/pull",
            json=payload,
            timeout=600  # 10 minutes for model download
        )
        
        return response.status_code == 200


def create_ai_client(provider: str = "openai", **kwargs) -> AIClient:
    """
    Factory function to create an AI client.
    
    Args:
        provider: AI provider ('openai', 'anthropic', or 'ollama')
        **kwargs: Additional arguments for the client
    
    Returns:
        AIClient instance
    """
    providers = {
        "openai": OpenAIClient,
        "anthropic": AnthropicClient,
        "claude": AnthropicClient,
        "ollama": lambda **kw: __import_ollama_client(**kw)
    }
    
    provider = provider.lower()
    if provider not in providers:
        raise ValueError(
            f"Unknown provider: {provider}. Available providers: {list(providers.keys())}"
        )
    
    return providers[provider](**kwargs)


def __import_ollama_client(**kwargs):
    """Lazy import Ollama client."""
    from .local_client import OllamaClient
    return OllamaClient(**kwargs)
