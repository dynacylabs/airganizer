"""AI provider abstraction for multi-provider support."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import json


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    def generate_structure(
        self,
        file_chunk,  # Can be Dict or str
        current_structure: Dict[str, Any],
        format_type: str = 'json',
        debug: bool = False
    ) -> Dict[str, Any]:
        """
        Generate or refine directory structure based on file chunk.
        
        Args:
            file_chunk: Chunk of the actual file tree (dict for JSON, str for pathlist/compact)
            current_structure: Current theoretical directory structure
            format_type: Format of the file_chunk ('json', 'pathlist', 'compact')
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
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        response_format: str = "json_object",
        system_prompt: str = "You are an expert file organizer. Generate clean, logical directory structures in JSON format. You can reorganize and restructure categories as you process new data."
    ):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4)
            temperature: Model temperature (default: 0.3)
            max_tokens: Maximum tokens to generate (default: 4096)
            response_format: Response format type (default: json_object)
            system_prompt: System prompt for the AI
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.response_format = response_format
        self.system_prompt = system_prompt
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
        file_chunk,
        current_structure: Dict[str, Any],
        format_type: str = 'json',
        debug: bool = False
    ) -> Dict[str, Any]:
        """Generate structure using OpenAI."""
        client = self._get_client()
        
        prompt = self._build_prompt(file_chunk, current_structure, format_type)
        
        if debug:
            print(f"[DEBUG] OpenAI: Sending request to {self.model}...")
            print(f"[DEBUG] OpenAI: Prompt length: {len(prompt)} chars")
        
        completion_params = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        if self.response_format == "json_object":
            completion_params["response_format"] = {"type": "json_object"}
        
        response = client.chat.completions.create(**completion_params)
        
        if debug:
            print(f"[DEBUG] OpenAI: Received response")
            print(f"[DEBUG] OpenAI: Response length: {len(response.choices[0].message.content)} chars")
        
        try:
            result = json.loads(response.choices[0].message.content)
            # Validate structure has required keys
            if 'dirs' in result and 'files' in result:
                return result
            else:
                print(f"Warning: Invalid structure format from OpenAI")
                return current_structure
        except json.JSONDecodeError:
            print(f"Warning: Failed to parse OpenAI response")
            return current_structure
    
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
        file_chunk,
        current_structure: Dict[str, Any],
        format_type: str = 'json'
    ) -> str:
        """Build the prompt for structure generation."""
        
        # Format the file chunk based on type
        if format_type == 'pathlist':
            files_section = f"""File paths (one per line):
{file_chunk}"""
        elif format_type == 'compact':
            files_section = f"""Files (indented by directory):
{file_chunk}"""
        else:  # json
            files_section = f"""Files as JSON tree:
{json.dumps(file_chunk, indent=2)}"""
        
        return f"""You are analyzing a file system to create an organized directory structure.

Current theoretical structure:
{json.dumps(current_structure, indent=2)}

{files_section}

Your task:
1. Analyze the files in this chunk
2. Review the current theoretical structure
3. Generate an UPDATED directory structure that logically organizes ALL files seen so far
4. **IMPORTANT**: You can and SHOULD reorganize the existing structure when new data suggests a better organization
   - Example: If you previously created "photos/" flat, but now see photos organized by event/location, 
     restructure to "photos/HOBY/", "photos/Cancun/", etc.
   - You can consolidate categories, split them, rename them, or restructure hierarchies as needed
   - Each chunk gives you new information - use it to improve the organization
5. **PLACE each file from the current chunk into the appropriate category**
   - Add file names (not full paths) to the "files" arrays
   - Files should be placed in the most specific/appropriate category
6. Create semantic, clear category names
7. Respond with ONLY a JSON object in this EXACT format:

{{
  "dirs": {{
    "CategoryName": {{
      "dirs": {{}},
      "files": ["example.jpg", "photo.png"]
    }}
  }},
  "files": []
}}

Rules:
- Use clear, descriptive directory names
- Group related content together
- Don't create too many top-level categories
- REORGANIZE the structure when patterns emerge from new data
- Think holistically about the entire dataset, not just the current chunk
- Place ALL files from the current chunk into appropriate categories
- Return ONLY valid JSON, nothing else"""


class AnthropicProvider(AIProvider):
    """Anthropic (Claude) API provider."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        system_prompt: str = "You are an expert file organizer. Generate clean, logical directory structures in JSON format. You can reorganize and restructure categories as you process new data."
    ):
        """
        Initialize Anthropic provider.
        
        Args:
            api_key: Anthropic API key
            model: Model to use
            temperature: Model temperature (default: 0.3)
            max_tokens: Maximum tokens to generate (default: 4096)
            system_prompt: System prompt for the AI (used in user message since Anthropic doesn't have separate system role)
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
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
        file_chunk,
        current_structure: Dict[str, Any],
        format_type: str = 'json',
        debug: bool = False
    ) -> Dict[str, Any]:
        """Generate structure using Anthropic."""
        client = self._get_client()
        
        prompt = self._build_prompt(file_chunk, current_structure, format_type)
        
        if debug:
            print(f"[DEBUG] Anthropic: Sending request to {self.model}...")
            print(f"[DEBUG] Anthropic: Prompt length: {len(prompt)} chars")
        
        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
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
            # Validate structure has required keys
            if 'dirs' in result and 'files' in result:
                return result
            else:
                print(f"Warning: Invalid structure format from Anthropic")
                return current_structure
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
        file_chunk,
        current_structure: Dict[str, Any],
        format_type: str = 'json'
    ) -> str:
        """Build the prompt for structure generation."""
        
        # Format the file chunk based on type
        if format_type == 'pathlist':
            files_section = f"""File paths (one per line):
{file_chunk}"""
        elif format_type == 'compact':
            files_section = f"""Files (indented by directory):
{file_chunk}"""
        else:  # json
            files_section = f"""Files as JSON tree:
{json.dumps(file_chunk, indent=2)}"""
        
        return f"""You are analyzing a file system to create an organized directory structure.

Current theoretical structure:
{json.dumps(current_structure, indent=2)}

{files_section}

Your task:
1. Analyze the files in this chunk
2. Review the current theoretical structure
3. Generate an UPDATED directory structure that logically organizes ALL files seen so far
4. **IMPORTANT**: You can and SHOULD reorganize the existing structure when new data suggests a better organization
   - Example: If you previously created "photos/" flat, but now see photos organized by event/location, 
     restructure to "photos/HOBY/", "photos/Cancun/", etc.
   - You can consolidate categories, split them, rename them, or restructure hierarchies as needed
   - Each chunk gives you new information - use it to improve the organization
5. **PLACE each file from the current chunk into the appropriate category**
   - Add file names (not full paths) to the "files" arrays
   - Files should be placed in the most specific/appropriate category
6. Create semantic, clear category names
7. Respond with ONLY a JSON object in this EXACT format:

{{
  "dirs": {{
    "CategoryName": {{
      "dirs": {{}},
      "files": ["example.jpg", "photo.png"]
    }}
  }},
  "files": []
}}

Rules:
- Use clear, descriptive directory names
- Group related content together
- Don't create too many top-level categories
- REORGANIZE the structure when patterns emerge from new data
- Think holistically about the entire dataset, not just the current chunk
- Place ALL files from the current chunk into appropriate categories
- Return ONLY valid JSON, nothing else"""


class OllamaProvider(AIProvider):
    """Ollama local AI provider (supports GPU and Apple Metal)."""
    
    def __init__(
        self,
        model: str = "llama2",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.3,
        num_predict: int = 2048,
        system_prompt: str = "You are an expert file organizer. Generate clean, logical directory structures in JSON format. You can reorganize and restructure categories as you process new data."
    ):
        """
        Initialize Ollama provider.
        
        Args:
            model: Model name (e.g., 'llama2', 'mistral', 'codellama')
            base_url: Ollama server URL
            temperature: Model temperature (default: 0.3)
            num_predict: Maximum tokens to generate (default: 2048)
            system_prompt: System prompt for the AI
        """
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.num_predict = num_predict
        self.system_prompt = system_prompt
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
        file_chunk,
        current_structure: Dict[str, Any],
        format_type: str = 'json',
        debug: bool = False
    ) -> Dict[str, Any]:
        """Generate structure using Ollama."""
        client = self._get_client()
        
        prompt = self._build_prompt(file_chunk, current_structure, format_type)
        
        if debug:
            print(f"[DEBUG] Ollama: Sending request to {self.model}...")
            print(f"[DEBUG] Ollama: Prompt length: {len(prompt)} chars")
            print(f"[DEBUG] Ollama: Using Metal/GPU acceleration (if available)")
        
        response = client.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            format="json",
            options={
                "temperature": self.temperature,
                "num_predict": self.num_predict
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
            # Validate structure has required keys
            if 'dirs' in result and 'files' in result:
                return result
            else:
                print(f"Warning: Invalid structure format from Ollama")
                return current_structure
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
        file_chunk,
        current_structure: Dict[str, Any],
        format_type: str = 'json'
    ) -> str:
        """Build the prompt for structure generation."""
        
        # Format the file chunk based on type
        if format_type == 'pathlist':
            files_section = f"""File paths (one per line):
{file_chunk}"""
        elif format_type == 'compact':
            files_section = f"""Files (indented by directory):
{file_chunk}"""
        else:  # json
            files_section = f"""Files as JSON tree:
{json.dumps(file_chunk, indent=2)}"""
        
        return f"""You are analyzing a file system to create an organized directory structure.

Current theoretical structure:
{json.dumps(current_structure, indent=2)}

{files_section}

Your task:
1. Analyze the files in this chunk
2. Review the current theoretical structure
3. Generate an UPDATED directory structure that logically organizes ALL files seen so far
4. **IMPORTANT**: You can and SHOULD reorganize the existing structure when new data suggests a better organization
   - Example: If you previously created "photos/" flat, but now see photos organized by event/location, 
     restructure to "photos/HOBY/", "photos/Cancun/", etc.
   - You can consolidate categories, split them, rename them, or restructure hierarchies as needed
   - Each chunk gives you new information - use it to improve the organization
5. **PLACE each file from the current chunk into the appropriate category**
   - Add file names (not full paths) to the \"files\" arrays
   - Files should be placed in the most specific/appropriate category
6. Create semantic, clear category names
7. Respond with ONLY a JSON object in this EXACT format:

{{
  \"dirs\": {{
    \"CategoryName\": {{
      \"dirs\": {{}},\n      \"files\": [\"example.jpg\", \"photo.png\"]
    }}
  }},
  \"files\": []
}}

Rules:
- Use clear, descriptive directory names
- Group related content together
- Don't create too many top-level categories
- REORGANIZE the structure when patterns emerge from new data
- Think holistically about the entire dataset, not just the current chunk
- Place ALL files from the current chunk into appropriate categories
- Return ONLY valid JSON, nothing else"""
