"""AI-powered MIME type to model mapping."""

import logging
import json
import os
from typing import List, Dict, Any, Optional

from .model_discovery import AIModel


logger = logging.getLogger(__name__)


class MimeModelMapper:
    """Maps MIME types to appropriate AI models using AI recommendations."""
    
    def __init__(self, mapping_model: Optional[AIModel]):
        """
        Initialize the MIME-to-model mapper.
        
        Args:
            mapping_model: The AI model to use for making recommendations
        """
        self.mapping_model = mapping_model
    
    def create_mapping(
        self, 
        mime_types: List[str], 
        available_models: List[AIModel]
    ) -> Dict[str, str]:
        """
        Create a mapping of MIME types to AI models.
        
        Args:
            mime_types: List of unique MIME types found in files
            available_models: List of available AI models
            
        Returns:
            Dictionary mapping MIME type to model name
        """
        if not self.mapping_model:
            logger.warning("No mapping model available, using default mapping")
            return self._create_default_mapping(mime_types, available_models)
        
        if not available_models:
            logger.error("No available models for mapping")
            return {}
        
        logger.info(f"Creating AI-powered mapping for {len(mime_types)} MIME types using {len(available_models)} models")
        
        # Use AI to create the mapping
        if self.mapping_model.provider == "openai":
            return self._create_mapping_openai(mime_types, available_models)
        elif self.mapping_model.provider == "anthropic":
            return self._create_mapping_anthropic(mime_types, available_models)
        elif self.mapping_model.provider == "ollama":
            return self._create_mapping_ollama(mime_types, available_models)
        else:
            logger.warning(f"Unsupported provider {self.mapping_model.provider}, using default mapping")
            return self._create_default_mapping(mime_types, available_models)
    
    def _create_prompt(self, mime_types: List[str], available_models: List[AIModel]) -> str:
        """
        Create the prompt for the AI to recommend model mappings.
        
        Args:
            mime_types: List of MIME types
            available_models: List of available models
            
        Returns:
            Prompt string
        """
        models_info = []
        for model in available_models:
            models_info.append({
                "name": model.name,
                "capabilities": model.capabilities,
                "description": model.description,
                "type": model.type
            })
        
        prompt = f"""You are an expert AI system architect. Your task is to recommend which AI model should be used to analyze each type of file based on its MIME type.

Available AI Models:
{json.dumps(models_info, indent=2)}

MIME Types to Map:
{json.dumps(mime_types, indent=2)}

Requirements:
1. For each MIME type, select the MOST APPROPRIATE model from the available models
2. Consider model capabilities (text, image, etc.) when making recommendations
3. Prefer specialized models for specific content types (e.g., vision models for images)
4. Balance between model capability and efficiency
5. Local models may be preferred for simple tasks to reduce API costs
6. Online models may be preferred for complex analysis requiring advanced capabilities

Return ONLY a valid JSON object with this exact structure:
{{
  "mime_type_1": "model_name_1",
  "mime_type_2": "model_name_2",
  ...
}}

Do not include any explanations or additional text. Only return the JSON mapping.
"""
        return prompt
    
    def _create_mapping_openai(
        self, 
        mime_types: List[str], 
        available_models: List[AIModel]
    ) -> Dict[str, str]:
        """
        Create mapping using OpenAI API.
        
        Args:
            mime_types: List of MIME types
            available_models: List of available models
            
        Returns:
            Dictionary mapping MIME type to model name
        """
        try:
            import openai
            
            api_key = os.getenv(self.mapping_model.api_key_env)
            if not api_key:
                logger.error(f"Missing API key: {self.mapping_model.api_key_env}")
                return self._create_default_mapping(mime_types, available_models)
            
            client = openai.OpenAI(api_key=api_key)
            
            prompt = self._create_prompt(mime_types, available_models)
            
            logger.info(f"Requesting MIME-to-model mapping from OpenAI ({self.mapping_model.model_name})")
            
            response = client.chat.completions.create(
                model=self.mapping_model.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert AI system architect specializing in model selection for different file types."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            mapping_json = response.choices[0].message.content
            mapping = json.loads(mapping_json)
            
            logger.info("Successfully created AI-powered MIME-to-model mapping")
            return mapping
            
        except Exception as e:
            logger.error(f"Error creating OpenAI mapping: {e}")
            return self._create_default_mapping(mime_types, available_models)
    
    def _create_mapping_anthropic(
        self, 
        mime_types: List[str], 
        available_models: List[AIModel]
    ) -> Dict[str, str]:
        """
        Create mapping using Anthropic API.
        
        Args:
            mime_types: List of MIME types
            available_models: List of available models
            
        Returns:
            Dictionary mapping MIME type to model name
        """
        try:
            import anthropic
            
            api_key = os.getenv(self.mapping_model.api_key_env)
            if not api_key:
                logger.error(f"Missing API key: {self.mapping_model.api_key_env}")
                return self._create_default_mapping(mime_types, available_models)
            
            client = anthropic.Anthropic(api_key=api_key)
            
            prompt = self._create_prompt(mime_types, available_models)
            
            logger.info(f"Requesting MIME-to-model mapping from Anthropic ({self.mapping_model.model_name})")
            
            response = client.messages.create(
                model=self.mapping_model.model_name,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            mapping_json = response.content[0].text
            # Extract JSON from response (may have markdown code blocks)
            if "```json" in mapping_json:
                mapping_json = mapping_json.split("```json")[1].split("```")[0].strip()
            elif "```" in mapping_json:
                mapping_json = mapping_json.split("```")[1].split("```")[0].strip()
            
            mapping = json.loads(mapping_json)
            
            logger.info("Successfully created AI-powered MIME-to-model mapping")
            return mapping
            
        except Exception as e:
            logger.error(f"Error creating Anthropic mapping: {e}")
            return self._create_default_mapping(mime_types, available_models)
    
    def _create_mapping_ollama(
        self, 
        mime_types: List[str], 
        available_models: List[AIModel]
    ) -> Dict[str, str]:
        """
        Create mapping using Ollama local model.
        
        Args:
            mime_types: List of MIME types
            available_models: List of available models
            
        Returns:
            Dictionary mapping MIME type to model name
        """
        try:
            import requests
            
            prompt = self._create_prompt(mime_types, available_models)
            
            logger.info(f"Requesting MIME-to-model mapping from Ollama ({self.mapping_model.model_name})")
            
            ollama_url = "http://localhost:11434/api/generate"
            
            response = requests.post(
                ollama_url,
                json={
                    "model": self.mapping_model.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            mapping_json = data.get('response', '{}')
            mapping = json.loads(mapping_json)
            
            logger.info("Successfully created AI-powered MIME-to-model mapping")
            return mapping
            
        except Exception as e:
            logger.error(f"Error creating Ollama mapping: {e}")
            return self._create_default_mapping(mime_types, available_models)
    
    def _create_default_mapping(
        self, 
        mime_types: List[str], 
        available_models: List[AIModel]
    ) -> Dict[str, str]:
        """
        Create a default mapping using simple heuristics.
        
        Args:
            mime_types: List of MIME types
            available_models: List of available models
            
        Returns:
            Dictionary mapping MIME type to model name
        """
        logger.info("Creating default MIME-to-model mapping using heuristics")
        
        if not available_models:
            return {}
        
        # Find models by capability
        vision_models = [m for m in available_models if m.has_capability("image")]
        text_models = [m for m in available_models if m.has_capability("text")]
        
        # Prefer local models for efficiency
        local_vision = [m for m in vision_models if m.type == "local"]
        local_text = [m for m in text_models if m.type == "local"]
        
        # Select default models
        default_vision = (local_vision or vision_models)[0] if (local_vision or vision_models) else None
        default_text = (local_text or text_models)[0] if (local_text or text_models) else None
        default_model = default_text or available_models[0]
        
        mapping = {}
        
        for mime_type in mime_types:
            # Image files
            if mime_type.startswith('image/'):
                if default_vision:
                    mapping[mime_type] = default_vision.name
                else:
                    mapping[mime_type] = default_model.name
            
            # Text-based files
            elif mime_type.startswith('text/') or \
                 mime_type in ['application/json', 'application/xml', 'application/pdf']:
                if default_text:
                    mapping[mime_type] = default_text.name
                else:
                    mapping[mime_type] = default_model.name
            
            # Default for everything else
            else:
                mapping[mime_type] = default_model.name
        
        return mapping
