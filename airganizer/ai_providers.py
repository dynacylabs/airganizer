"""AI provider abstraction for multi-provider support."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import json


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    def generate_structure(
        self,
        file_chunk: Dict[str, Any],
        current_structure: Dict[str, Any],
        debug: bool = False
    ) -> Dict[str, Any]:
        """
        Generate or refine directory structure based on file chunk.
        
        Args:
            file_chunk: Chunk of the actual file tree
            current_structure: Current theoretical directory structure
            debug: Enable debug output
            
        Returns:
            Updated theoretical directory structure
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if the AI provider is accessible.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass


class OpenAIProvider(AIProvider):
    """OpenAI API provider."""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4)
        """
        self.api_key = api_key
        self.model = model
        self._client = None
    
    def _get_client(self):
        """Lazy load OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "OpenAI library not installed. Install with: pip install openai"
                )
        return self._client
    
    def generate_structure(
        self,
        file_chunk: Dict[str, Any],
        current_structure: Dict[str, Any],
        debug: bool = False
    ) -> Dict[str, Any]:
        """Generate structure using OpenAI."""
        client = self._get_client()
        
        prompt = self._build_prompt(file_chunk, current_structure)
        
        if debug:
            print(f"[DEBUG] OpenAI: Sending request to {self.model}...")
            print(f"[DEBUG] OpenAI: Prompt length: {len(prompt)} chars")
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert file organizer. Generate clean, logical directory structures in JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        if debug:
            print(f"[DEBUG] OpenAI: Received response")
            print(f"[DEBUG] OpenAI: Response length: {len(response.choices[0].message.content)} chars")
        
        result = json.loads(response.choices[0].message.content)
        return result.get('structure', current_structure)
    
    def test_connection(self) -> bool:
        """Test OpenAI connection."""
        try:
            client = self._get_client()
            # Simple test call
            client.models.list()
            return True
        except Exception:
            return False
    
    def _build_prompt(
        self,
        file_chunk: Dict[str, Any],
        current_structure: Dict[str, Any]
    ) -> str:
        """Build the prompt for structure generation."""
        return f"""You are analyzing a file system to create an organized directory structure.

Current theoretical structure:
{json.dumps(current_structure, indent=2)}

New files to consider:
{json.dumps(file_chunk, indent=2)}

Your task:
1. Analyze the files in the chunk
2. Review the current theoretical structure
3. Generate an UPDATED directory structure that logically organizes these files
4. The structure should only contain directories (folders), no file placements yet
5. Create semantic, clear category names
6. Respond with ONLY a JSON object in this format:

{{
  "structure": {{
    "dirs": {{
      "CategoryName": {{
        "dirs": {{}},
        "files": []
      }}
    }},
    "files": []
  }}
}}

Rules:
- Use clear, descriptive directory names
- Group related content together
- Don't create too many top-level categories
- Empty "files" arrays are required in the format
- Return ONLY valid JSON, nothing else"""


class AnthropicProvider(AIProvider):
    """Anthropic (Claude) API provider."""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize Anthropic provider.
        
        Args:
            api_key: Anthropic API key
            model: Model to use
        """
        self.api_key = api_key
        self.model = model
        self._client = None
    
    def _get_client(self):
        """Lazy load Anthropic client."""
        if self._client is None:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "Anthropic library not installed. Install with: pip install anthropic"
                )
        return self._client
    
    def generate_structure(
        self,
        file_chunk: Dict[str, Any],
        current_structure: Dict[str, Any],
        debug: bool = False
    ) -> Dict[str, Any]:
        """Generate structure using Anthropic."""
        client = self._get_client()
        
        prompt = self._build_prompt(file_chunk, current_structure)
        
        if debug:
            print(f"[DEBUG] Anthropic: Sending request to {self.model}...")
            print(f"[DEBUG] Anthropic: Prompt length: {len(prompt)} chars")
        
        response = client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=0.3,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Extract JSON from response
        content = response.content[0].text
        
        if debug:
            print(f"[DEBUG] Anthropic: Received response")
            print(f"[DEBUG] Anthropic: Response length: {len(content)} chars")
        
        # Try to parse JSON from the response
        try:
            # Look for JSON in code blocks or direct JSON
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()
            
            if debug:
                print(f"[DEBUG] Anthropic: Parsing JSON response...")
            
            result = json.loads(json_str)
            return result.get('structure', current_structure)
        except json.JSONDecodeError:
            # Fallback: return current structure if parsing fails
            print(f"Warning: Failed to parse AI response: {content}")
            if debug:
                print(f"[DEBUG] Anthropic: JSON parse failed, returning current structure")
            return current_structure
    
    def test_connection(self) -> bool:
        """Test Anthropic connection."""
        try:
            client = self._get_client()
            # Simple test call
            client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except Exception:
            return False
    
    def _build_prompt(
        self,
        file_chunk: Dict[str, Any],
        current_structure: Dict[str, Any]
    ) -> str:
        """Build the prompt for structure generation."""
        return f"""You are analyzing a file system to create an organized directory structure.

Current theoretical structure:
{json.dumps(current_structure, indent=2)}

New files to consider:
{json.dumps(file_chunk, indent=2)}

Your task:
1. Analyze the files in the chunk
2. Review the current theoretical structure
3. Generate an UPDATED directory structure that logically organizes these files
4. The structure should only contain directories (folders), no file placements yet
5. Create semantic, clear category names
6. Respond with ONLY a JSON object in this format:

{{
  "structure": {{
    "dirs": {{
      "CategoryName": {{
        "dirs": {{}},
        "files": []
      }}
    }},
    "files": []
  }}
}}

Rules:
- Use clear, descriptive directory names
- Group related content together
- Don't create too many top-level categories
- Empty "files" arrays are required in the format
- Return ONLY valid JSON, nothing else"""


class OllamaProvider(AIProvider):
    """Ollama local AI provider (supports GPU and Apple Metal)."""
    
    def __init__(
        self,
        model: str = "llama2",
        base_url: str = "http://localhost:11434"
    ):
        """
        Initialize Ollama provider.
        
        Args:
            model: Model name (e.g., 'llama2', 'mistral', 'codellama')
            base_url: Ollama server URL
        """
        self.model = model
        self.base_url = base_url
        self._client = None
    
    def _get_client(self):
        """Lazy load Ollama client."""
        if self._client is None:
            try:
                import ollama
                # Configure client with base_url
                self._client = ollama.Client(host=self.base_url)
            except ImportError:
                raise ImportError(
                    "Ollama library not installed. Install with: pip install ollama"
                )
        return self._client
    
    def generate_structure(
        self,
        file_chunk: Dict[str, Any],
        current_structure: Dict[str, Any],
        debug: bool = False
    ) -> Dict[str, Any]:
        """Generate structure using Ollama."""
        client = self._get_client()
        
        prompt = self._build_prompt(file_chunk, current_structure)
        
        if debug:
            print(f"[DEBUG] Ollama: Sending request to {self.model}...")
            print(f"[DEBUG] Ollama: Prompt length: {len(prompt)} chars")
            print(f"[DEBUG] Ollama: Using Metal/GPU acceleration (if available)")
        
        response = client.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert file organizer. Generate clean, logical directory structures in JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            format="json",
            options={
                "temperature": 0.3,
                "num_predict": 2048
            }
        )
        
        # Extract JSON from response
        content = response['message']['content']
        
        if debug:
            print(f"[DEBUG] Ollama: Received response")
            print(f"[DEBUG] Ollama: Response length: {len(content)} chars")
            print(f"[DEBUG] Ollama: Parsing JSON response...")
        
        try:
            result = json.loads(content)
            if debug:
                print(f"[DEBUG] Ollama: Successfully parsed JSON")
            return result.get('structure', current_structure)
        except json.JSONDecodeError:
            print(f"Warning: Failed to parse Ollama response: {content}")
            if debug:
                print(f"[DEBUG] Ollama: JSON parse failed, returning current structure")
            return current_structure
    
    def test_connection(self) -> bool:
        """Test Ollama connection."""
        try:
            client = self._get_client()
            # Try to list models as a connection test
            client.list()
            return True
        except Exception:
            return False
    
    def _build_prompt(
        self,
        file_chunk: Dict[str, Any],
        current_structure: Dict[str, Any]
    ) -> str:
        """Build the prompt for structure generation."""
        return f"""You are analyzing a file system to create an organized directory structure.

Current theoretical structure:
{json.dumps(current_structure, indent=2)}

New files to consider:
{json.dumps(file_chunk, indent=2)}

Your task:
1. Analyze the files in the chunk
2. Review the current theoretical structure
3. Generate an UPDATED directory structure that logically organizes these files
4. The structure should only contain directories (folders), no file placements yet
5. Create semantic, clear category names
6. Respond with ONLY a JSON object in this format:

{{
  "structure": {{
    "dirs": {{
      "CategoryName": {{
        "dirs": {{}},
        "files": []
      }}
    }},
    "files": []
  }}
}}

Rules:
- Use clear, descriptive directory names
- Group related content together
- Don't create too many top-level categories
- Empty "files" arrays are required in the format
- Return ONLY valid JSON, nothing else"""
