"""AI-powered model recommendation system."""

import json
from typing import List, Dict, Any, Optional, Callable
from ..core.models import FileItem
from ..core.system_resources import get_system_resources, estimate_model_ram_usage
from ..models import ModelRegistry, get_model_registry, ModelManager, get_model_manager
from .client import AIClient, create_ai_client
from ..config import get_config


SYSTEM_PROMPT = """You are an expert in machine learning models and file analysis. Your task is to recommend the most appropriate analysis models for different file types.

Consider:
1. The file's MIME type and characteristics
2. Available models and their capabilities
3. The depth of analysis needed
4. Efficiency vs. thoroughness trade-offs

Respond with JSON only, no additional text."""


def create_recommendation_prompt(files: List[FileItem], available_models: List[str]) -> str:
    """
    Create prompt for AI to recommend models for files.
    
    Args:
        files: List of files to analyze
        available_models: List of available model names
    
    Returns:
        Formatted prompt string
    """
    file_list = []
    for f in files:
        file_info = {
            "file_name": f.file_name,
            "mime_type": f.mime_type,
            "file_size": f.file_size
        }
        file_list.append(file_info)
    
    prompt = f"""Recommend analysis models for these files:

FILES:
{json.dumps(file_list, indent=2)}

AVAILABLE MODELS:
{json.dumps(available_models, indent=2)}

For each file, recommend:
1. Primary model to use
2. Analysis tasks to perform (e.g., "extract_text", "classify_content", "detect_objects")
3. Reason for recommendation
4. Alternative models (if applicable)

Respond with JSON in this format:
{{
  "recommendations": [
    {{
      "file_name": "example.jpg",
      "mime_type": "image/jpeg",
      "primary_model": "gpt-4o-vision",
      "analysis_tasks": ["extract_text", "classify_content", "describe_image"],
      "reason": "Image file requires vision model for comprehensive analysis",
      "alternatives": ["claude-3-5-sonnet-vision"]
    }}
  ]
}}

Respond with ONLY the JSON structure, no additional text."""

    return prompt


class ModelRecommender:
    """Recommends analysis models for files using AI."""
    
    def __init__(self, ai_client: AIClient, model_registry: Optional[ModelRegistry] = None,
                 batch_size: int = 10, use_cache: bool = True):
        """
        Initialize ModelRecommender.
        
        Args:
            ai_client: AI client for making recommendations
            model_registry: Model registry (uses global if not provided)
            batch_size: Number of files to batch per AI call
            use_cache: Whether to use cached recommendations
        """
        self.ai_client = ai_client
        self.model_registry = model_registry or get_model_registry()
        self.batch_size = batch_size
        self.use_cache = use_cache
        self.config = get_config()
    
    def recommend_models(self, files: List[FileItem],
                        progress_callback: Optional[Callable[[int, int, str], None]] = None
                        ) -> Dict[str, Dict[str, Any]]:
        """
        Recommend models for a list of files.
        
        Args:
            files: List of files to get recommendations for
            progress_callback: Optional callback(processed, total, message)
        
        Returns:
            Dictionary mapping file_path to recommendation details
        """
        recommendations = {}
        
        # Check for explicit mappings first
        files_needing_ai = []
        for file_item in files:
            explicit_model = self.config.get_model_for_filetype(file_item.mime_type)
            
            if explicit_model:
                # User explicitly configured this file type
                recommendations[file_item.file_path] = {
                    "file_name": file_item.file_name,
                    "mime_type": file_item.mime_type,
                    "primary_model": explicit_model,
                    "analysis_tasks": ["analyze"],
                    "reason": "Explicitly configured by user",
                    "alternatives": [],
                    "source": "explicit_config"
                }
            elif self.use_cache:
                # Check cache
                cached = self.config.get_model_recommendation_cache(file_item.mime_type)
                if cached:
                    rec = cached.copy()
                    rec["file_name"] = file_item.file_name
                    rec["source"] = "cache"
                    recommendations[file_item.file_path] = rec
                else:
                    files_needing_ai.append(file_item)
            else:
                files_needing_ai.append(file_item)
        
        if not files_needing_ai:
            return recommendations
        
        # Process remaining files with AI in batches
        total_batches = (len(files_needing_ai) + self.batch_size - 1) // self.batch_size
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(files_needing_ai))
            batch = files_needing_ai[start_idx:end_idx]
            
            if progress_callback:
                progress_callback(
                    batch_idx + 1,
                    total_batches,
                    f"Getting model recommendations for batch {batch_idx + 1}/{total_batches}"
                )
            
            batch_recommendations = self._get_ai_recommendations(batch)
            recommendations.update(batch_recommendations)
        
        return recommendations
    
    def _get_ai_recommendations(self, files: List[FileItem]) -> Dict[str, Dict[str, Any]]:
        """Get AI recommendations for a batch of files."""
        # Get available models
        available_models = list(self.model_registry.models.keys())
        
        # Create prompt
        prompt = create_recommendation_prompt(files, available_models)
        
        try:
            # Get AI response
            response = self.ai_client.generate(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse response
            json_str = self._extract_json(response)
            data = json.loads(json_str)
            
            # Map to file paths and cache
            recommendations = {}
            for rec in data.get('recommendations', []):
                # Find matching file
                matching_file = next(
                    (f for f in files if f.file_name == rec.get('file_name')),
                    None
                )
                
                if matching_file:
                    rec['source'] = 'ai_recommendation'
                    recommendations[matching_file.file_path] = rec
                    
                    # Cache by MIME type
                    if self.use_cache and rec.get('mime_type'):
                        cache_entry = {k: v for k, v in rec.items() if k != 'file_name'}
                        self.config.cache_model_recommendation(rec['mime_type'], cache_entry)
            
            return recommendations
            
        except Exception as e:
            print(f"Warning: Failed to get AI recommendations: {e}")
            # Return fallback recommendations
            return self._create_fallback_recommendations(files)
    
    def _extract_json(self, response: str) -> str:
        """Extract JSON from AI response."""
        # Try to find JSON block markers
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            return response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            return response[start:end].strip()
        
        # Try to find JSON by looking for { }
        start = response.find("{")
        end = response.rfind("}") + 1
        
        if start != -1 and end > start:
            return response[start:end].strip()
        
        return response.strip()
    
    def _create_fallback_recommendations(self, files: List[FileItem]) -> Dict[str, Dict[str, Any]]:
        """Create fallback recommendations based on MIME types."""
        recommendations = {}
        
        for file_item in files:
            # Get models that can handle this file type
            capable_models = self.model_registry.get_models_for_filetype(file_item.mime_type)
            
            if capable_models:
                primary = capable_models[0]
                alternatives = [m.name for m in capable_models[1:3]]
            else:
                # Generic fallback
                primary_name = "gpt-4o"
                alternatives = ["claude-3-5-sonnet"]
            
            recommendations[file_item.file_path] = {
                "file_name": file_item.file_name,
                "mime_type": file_item.mime_type,
                "primary_model": primary.name if capable_models else primary_name,
                "analysis_tasks": ["analyze"],
                "reason": "Fallback recommendation based on MIME type",
                "alternatives": alternatives,
                "source": "fallback"
            }
        
        return recommendations


def create_model_recommender(provider: Optional[str] = None, **kwargs) -> ModelRecommender:
    """
    Factory function to create a ModelRecommender.
    
    Args:
        provider: AI provider (uses config default if not specified)
        **kwargs: Additional arguments for ModelRecommender
    
    Returns:
        ModelRecommender instance
    """
    config = get_config()
    
    if provider is None:
        if config.is_local_mode():
            provider = config.get('ai.local.default_model', 'ollama')
        else:
            provider = config.get('ai.default_provider', 'openai')
    
    # Create AI client
    if provider == 'ollama':
        host = config.get('ai.local.ollama_host', 'http://localhost:11434')
        model = config.get('ai.local.default_model', 'llama3.2')
        ai_client = create_ai_client('ollama', host=host, model=model)
    else:
        ai_client = create_ai_client(provider)
    
    batch_size = config.get('analyze.batch_size', 10)
    
    return ModelRecommender(
        ai_client=ai_client,
        batch_size=batch_size,
        **kwargs
    )
