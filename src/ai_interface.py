"""Interface for calling AI models from different providers."""

import base64
import logging
import os
import json
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List

from .config import Config
from .model_discovery import AIModel


logger = logging.getLogger(__name__)


class AIModelInterface:
    """Interface for interacting with AI models across different providers."""
    
    def __init__(self, config: Config):
        """
        Initialize the AI model interface.
        
        Args:
            config: Configuration object
        """
        self.config = config
    
    def analyze_file(
        self,
        file_path: str,
        mime_type: str,
        metadata: Dict[str, Any],
        model: AIModel
    ) -> Dict[str, Any]:
        """
        Analyze a file using the specified AI model.
        
        Args:
            file_path: Path to the file
            mime_type: MIME type of the file
            metadata: File metadata from Stage 1
            model: AIModel object to use for analysis
            
        Returns:
            Dictionary with proposed_filename, description, and tags
        """
        logger.info(f"Analyzing {file_path} with {model.name}")
        logger.debug(f"  - MIME type: {mime_type}")
        logger.debug(f"  - Provider: {model.provider}")
        logger.debug(f"  - Model: {model.name}")
        logger.debug(f"  - Metadata keys: {list(metadata.keys())}")
        
        # Route to appropriate provider
        if model.provider == "openai":
            return self._analyze_with_openai(file_path, mime_type, metadata, model)
        elif model.provider == "anthropic":
            return self._analyze_with_anthropic(file_path, mime_type, metadata, model)
        elif model.provider == "ollama":
            return self._analyze_with_ollama(file_path, mime_type, metadata, model)
        else:
            raise ValueError(f"Unsupported provider: {model.provider}")
    
    def _build_analysis_prompt(
        self,
        file_path: str,
        mime_type: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Build the prompt for file analysis.
        
        Args:
            file_path: Path to the file
            mime_type: MIME type of the file
            metadata: File metadata
            
        Returns:
            Prompt string
        """
        file_name = Path(file_path).name
        
        prompt = f"""You are analyzing a file for organization purposes. Please analyze this file and provide:

1. A proposed new filename (descriptive, concise, keep extension)
2. A detailed description of the file's contents
3. Relevant tags/keywords for categorization

File Information:
- Current filename: {file_name}
- MIME type: {mime_type}
- File size: {metadata.get('file_size', 'unknown')} bytes
"""
        
        # Add EXIF data if available
        if metadata.get('exif_data'):
            prompt += f"\n- EXIF data: {json.dumps(metadata['exif_data'], indent=2)}"
        
        # Add specific metadata
        if metadata.get('metadata'):
            prompt += f"\n- Additional metadata: {json.dumps(metadata['metadata'], indent=2)}"
        
        prompt += """

Please respond in JSON format with the following structure:
{
  "proposed_filename": "descriptive-name-with-extension",
  "description": "Detailed description of what's in this file",
  "tags": ["tag1", "tag2", "tag3"]
}

Important:
- Keep the original file extension
- Make the filename descriptive but concise (max 50 chars)
- Description should be 2-3 sentences
- Provide 3-7 relevant tags
- Tags should be lowercase, single words or hyphenated phrases
"""
        
        return prompt
    
    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the AI model's response.
        
        Args:
            response_text: Raw response text from the model
            
        Returns:
            Dictionary with proposed_filename, description, and tags
        """
        try:
            # Try to find JSON in the response
            logger.debug(f"Parsing AI response (length: {len(response_text)} chars)")
            # Some models wrap JSON in markdown code blocks
            if "```json" in response_text:
                logger.debug("Found JSON code block in response")
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_text = response_text[start:end].strip()
            elif "```" in response_text:
                logger.debug("Found generic code block in response")
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                json_text = response_text[start:end].strip()
            else:
                logger.debug("No code block markers, treating whole response as JSON")
                json_text = response_text.strip()
            
            # Parse JSON
            result = json.loads(json_text)
            logger.debug(f"Successfully parsed JSON with keys: {list(result.keys())}")
            
            # Validate required fields
            if not all(k in result for k in ['proposed_filename', 'description', 'tags']):
                raise ValueError("Missing required fields in response")
            
            # Ensure tags is a list
            if isinstance(result['tags'], str):
                result['tags'] = [tag.strip() for tag in result['tags'].split(',')]
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.debug(f"Raw response: {response_text}")
            
            # Return a fallback response
            return {
                'proposed_filename': Path(response_text).name if response_text else 'unknown.txt',
                'description': 'Failed to analyze file',
                'tags': ['unanalyzed']
            }
    
    def _analyze_with_openai(
        self,
        file_path: str,
        mime_type: str,
        metadata: Dict[str, Any],
        model: AIModel
    ) -> Dict[str, Any]:
        """Analyze file using OpenAI API."""
        logger.debug(f"[OpenAI] Starting analysis with model: {model.name}")
        api_key = os.getenv(model.api_key_env)
        if not api_key:
            logger.error(f"[OpenAI] API key not found in environment: {model.api_key_env}")
            raise ValueError(f"API key not found: {model.api_key_env}")
        
        base_url = self.config.get('models.openai.base_url', 'https://api.openai.com/v1')
        
        # Build prompt
        prompt = self._build_analysis_prompt(file_path, mime_type, metadata)
        
        # Prepare request
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        messages = [{'role': 'user', 'content': []}]
        
        # Add text prompt
        messages[0]['content'].append({
            'type': 'text',
            'text': prompt
        })
        
        # Add image if supported and file is an image
        if 'image' in model.capabilities and mime_type.startswith('image/'):
            try:
                with open(file_path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                
                messages[0]['content'].append({
                    'type': 'image_url',
                    'image_url': {
                        'url': f'data:{mime_type};base64,{image_data}'
                    }
                })
                logger.debug(f"Added image to OpenAI request")
            except Exception as e:
                logger.warning(f"Could not read image file: {e}")
        
        # If only text content, simplify message structure
        if len(messages[0]['content']) == 1:
            messages[0]['content'] = prompt
        
        payload = {
            'model': model.model_name,
            'messages': messages,
            'max_tokens': self.config.stage3_max_tokens,
            'temperature': self.config.stage3_temperature
        }
        
        try:
            response = requests.post(
                f'{base_url}/chat/completions',
                headers=headers,
                json=payload,
                timeout=self.config.stage3_timeout
            )
            response.raise_for_status()
            
            result = response.json()
            response_text = result['choices'][0]['message']['content']
            
            return self._parse_analysis_response(response_text)
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _analyze_with_anthropic(
        self,
        file_path: str,
        mime_type: str,
        metadata: Dict[str, Any],
        model: AIModel
    ) -> Dict[str, Any]:
        """Analyze file using Anthropic API."""
        api_key = os.getenv(model.api_key_env)
        if not api_key:
            raise ValueError(f"API key not found: {model.api_key_env}")
        
        base_url = self.config.get('models.anthropic.base_url', 'https://api.anthropic.com')
        
        # Build prompt
        prompt = self._build_analysis_prompt(file_path, mime_type, metadata)
        
        # Prepare request
        headers = {
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json'
        }
        
        content = []
        
        # Add image if supported and file is an image
        if 'image' in model.capabilities and mime_type.startswith('image/'):
            try:
                with open(file_path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                
                # Map MIME type to Anthropic's format
                media_type = mime_type
                if mime_type == 'image/jpg':
                    media_type = 'image/jpeg'
                
                content.append({
                    'type': 'image',
                    'source': {
                        'type': 'base64',
                        'media_type': media_type,
                        'data': image_data
                    }
                })
                logger.debug(f"Added image to Anthropic request")
            except Exception as e:
                logger.warning(f"Could not read image file: {e}")
        
        # Add text prompt
        content.append({
            'type': 'text',
            'text': prompt
        })
        
        payload = {
            'model': model.model_name,
            'max_tokens': self.config.stage3_max_tokens,
            'messages': [{
                'role': 'user',
                'content': content
            }]
        }
        
        try:
            response = requests.post(
                f'{base_url}/v1/messages',
                headers=headers,
                json=payload,
                timeout=self.config.stage3_timeout
            )
            response.raise_for_status()
            
            result = response.json()
            response_text = result['content'][0]['text']
            
            return self._parse_analysis_response(response_text)
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    def _analyze_with_ollama(
        self,
        file_path: str,
        mime_type: str,
        metadata: Dict[str, Any],
        model: AIModel
    ) -> Dict[str, Any]:
        """Analyze file using Ollama."""
        base_url = self.config.get('models.ollama.base_url', 'http://localhost:11434')
        
        # Build prompt
        prompt = self._build_analysis_prompt(file_path, mime_type, metadata)
        
        # Prepare request
        payload = {
            'model': model.model_name,
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': self.config.stage3_temperature,
                'num_predict': self.config.stage3_max_tokens
            }
        }
        
        # Add image if supported and file is an image
        if 'image' in model.capabilities and mime_type.startswith('image/'):
            try:
                with open(file_path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                
                payload['images'] = [image_data]
                logger.debug(f"Added image to Ollama request")
            except Exception as e:
                logger.warning(f"Could not read image file: {e}")
        
        try:
            response = requests.post(
                f'{base_url}/api/generate',
                json=payload,
                timeout=self.config.stage3_timeout
            )
            response.raise_for_status()
            
            result = response.json()
            response_text = result['response']
            
            return self._parse_analysis_response(response_text)
            
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise
