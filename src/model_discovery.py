"""AI model discovery and management."""

import logging
import os
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from .config import Config


logger = logging.getLogger(__name__)


@dataclass
class AIModel:
    """Represents an AI model available for analysis."""
    
    name: str
    type: str  # "online" or "local"
    provider: str  # "openai", "anthropic", "ollama", etc.
    model_name: str
    capabilities: List[str]  # ["text", "image", "audio", etc.]
    description: str
    api_key_env: Optional[str] = None  # Environment variable name for API key
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert AIModel to dictionary."""
        return asdict(self)
    
    def has_capability(self, capability: str) -> bool:
        """Check if model has a specific capability."""
        return capability in self.capabilities
    
    def is_available(self) -> bool:
        """Check if the model is available (e.g., API key exists for online models)."""
        if self.type == "online" and self.api_key_env:
            api_key = os.getenv(self.api_key_env)
            if not api_key:
                logger.warning(f"Model {self.name} requires {self.api_key_env} environment variable")
                return False
        return True


class ModelDiscovery:
    """Discovers and manages available AI models."""
    
    def __init__(self, config: Config):
        """
        Initialize the model discovery system.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.discovery_method = config.get('models.discovery_method', 'config')
        self.model_mode = config.get('models.model_mode', 'mixed')
        self.local_provider = config.get('models.local_provider', 'ollama')
        self.ollama_base_url = config.get('models.ollama.base_url', 'http://localhost:11434')
    
    def _filter_by_mode(self, models: List[AIModel]) -> List[AIModel]:
        """
        Filter models based on model_mode setting.
        
        Args:
            models: List of all discovered models
            
        Returns:
            Filtered list based on model_mode (online_only, local_only, mixed)
        """
        if self.model_mode == "mixed":
            return models
        elif self.model_mode == "online_only":
            return [m for m in models if m.type == "online"]
        elif self.model_mode == "local_only":
            return [m for m in models if m.type == "local"]
        else:
            logger.warning(f"Unknown model_mode: {self.model_mode}, using all models")
            return models
    
    def discover_models(self) -> List[AIModel]:
        """
        Discover available AI models based on configured method.
        
        Returns:
            List of available AIModel objects
        """
        logger.info(f"Discovering models using method: {self.discovery_method}, mode: {self.model_mode}")
        
        if self.discovery_method == "config":
            models = self._discover_from_config()
        elif self.discovery_method == "auto":
            models = self._auto_discover_models()
        elif self.discovery_method == "local_enumerate":
            models = self._discover_local_models()
        elif self.discovery_method == "local_download":
            models = self._discover_and_download_models()
        else:
            logger.error(f"Unknown discovery method: {self.discovery_method}")
            return []
        
        # Filter models based on model_mode
        filtered_models = self._filter_by_mode(models)
        logger.info(f"Discovered {len(models)} models, {len(filtered_models)} after filtering by mode '{self.model_mode}'")
        
        return filtered_models
    
    def _auto_discover_models(self) -> List[AIModel]:
        """
        Auto-discover models from all configured providers.
        
        Returns:
            List of AIModel objects from auto-enumeration
        """
        logger.info("Auto-discovering models from configured providers")
        models = []
        
        # Check OpenAI
        openai_config = self.config.get('models.openai', {})
        if openai_config.get('auto_enumerate', True):
            openai_models = self._enumerate_openai_models()
            models.extend(openai_models)
        else:
            # Use manual list if provided
            manual_models = openai_config.get('models', [])
            if manual_models:
                logger.info(f"Using manually specified OpenAI models: {manual_models}")
                for model_name in manual_models:
                    models.append(self._create_openai_model(model_name))
        
        # Check Anthropic
        anthropic_config = self.config.get('models.anthropic', {})
        if anthropic_config.get('auto_enumerate', True):
            anthropic_models = self._enumerate_anthropic_models()
            models.extend(anthropic_models)
        else:
            # Use manual list if provided
            manual_models = anthropic_config.get('models', [])
            if manual_models:
                logger.info(f"Using manually specified Anthropic models: {manual_models}")
                for model_name in manual_models:
                    models.append(self._create_anthropic_model(model_name))
        
        # Check Ollama (local)
        ollama_config = self.config.get('models.ollama', {})
        if ollama_config.get('auto_enumerate', True):
            ollama_models = self._enumerate_ollama_models()
            models.extend(ollama_models)
            
            # Auto-download if configured
            auto_download = ollama_config.get('auto_download_models', [])
            if auto_download:
                existing_names = [m.model_name for m in ollama_models]
                for model_name in auto_download:
                    if model_name not in existing_names:
                        if self._download_ollama_model(model_name):
                            models.append(self._create_ollama_model(model_name))
        
        logger.info(f"Auto-discovered {len(models)} models total")
        return models
    
    def _discover_from_config(self) -> List[AIModel]:
        """
        Method 1: Get models from configuration file.
        Uses the legacy config_models section or new provider-specific sections.
        
        Returns:
            List of AIModel objects from config
        """
        logger.info("Discovering models from configuration file")
        
        # First try the legacy available_models list
        available_models = self.config.get('models.available_models', [])
        if available_models:
            logger.info("Using legacy 'available_models' configuration")
            models = []
            
            for model_config in available_models:
                model = AIModel(
                    name=model_config.get('name'),
                    type=model_config.get('type'),
                    provider=model_config.get('provider'),
                    model_name=model_config.get('model_name'),
                    capabilities=model_config.get('capabilities', []),
                    description=model_config.get('description', ''),
                    api_key_env=model_config.get('api_key_env')
                )
                
                # Check if model is available
                if model.is_available():
                    models.append(model)
                    logger.info(f"Added model: {model.name} ({model.type}/{model.provider})")
                else:
                    logger.warning(f"Skipping unavailable model: {model.name}")
            
            return models
        
        # Otherwise, use the new provider-specific sections
        logger.info("Using new provider-specific configuration")
        models = []
        
        # Get OpenAI models
        openai_config = self.config.get('models.openai', {})
        openai_models = openai_config.get('models', [])
        api_key_env = openai_config.get('api_key_env', 'OPENAI_API_KEY')
        
        for model_name in openai_models:
            model = self._create_openai_model(model_name)
            if model.is_available():
                models.append(model)
                logger.info(f"Added OpenAI model: {model_name}")
            else:
                logger.warning(f"Skipping unavailable OpenAI model: {model_name} (missing {api_key_env})")
        
        # Get Anthropic models
        anthropic_config = self.config.get('models.anthropic', {})
        anthropic_models = anthropic_config.get('models', [])
        api_key_env = anthropic_config.get('api_key_env', 'ANTHROPIC_API_KEY')
        
        for model_name in anthropic_models:
            model = self._create_anthropic_model(model_name)
            if model.is_available():
                models.append(model)
                logger.info(f"Added Anthropic model: {model_name}")
            else:
                logger.warning(f"Skipping unavailable Anthropic model: {model_name} (missing {api_key_env})")
        
        # Get Ollama models
        ollama_config = self.config.get('models.ollama', {})
        ollama_models = ollama_config.get('models', [])
        
        for model_name in ollama_models:
            model = self._create_ollama_model(model_name)
            models.append(model)
            logger.info(f"Added Ollama model: {model_name}")
        
        return models
    
    def _discover_local_models(self) -> List[AIModel]:
        """
        Method 2: Enumerate local models only.
        
        Returns:
            List of locally available AIModel objects
        """
        logger.info("Enumerating local models")
        
        if self.local_provider == "ollama":
            return self._enumerate_ollama_models()
        else:
            logger.error(f"Unsupported local provider: {self.local_provider}")
            return []
    
    def _discover_and_download_models(self) -> List[AIModel]:
        """
        Method 3: Enumerate local models and download if needed.
        
        Returns:
            List of locally available AIModel objects (after downloads)
        """
        logger.info("Discovering local models with auto-download enabled")
        
        if self.local_provider == "ollama":
            # First, enumerate existing models
            models = self._enumerate_ollama_models()
            
            # Get list of models to auto-download
            auto_download = self.config.get('models.ollama.auto_download_models', [])
            
            if auto_download:
                logger.info(f"Auto-download enabled for models: {auto_download}")
                
                # Check which models need to be downloaded
                existing_model_names = [m.model_name for m in models]
                
                for model_name in auto_download:
                    if model_name not in existing_model_names:
                        logger.info(f"Downloading model: {model_name}")
                        if self._download_ollama_model(model_name):
                            # Re-enumerate to get the newly downloaded model
                            models = self._enumerate_ollama_models()
                        else:
                            logger.warning(f"Failed to download model: {model_name}")
            
            return models
        else:
            logger.error(f"Unsupported local provider: {self.local_provider}")
            return []
    
    def _enumerate_openai_models(self) -> List[AIModel]:
        """
        Enumerate models available from OpenAI API.
        
        Returns:
            List of AIModel objects from OpenAI
        """
        api_key_env = self.config.get('models.openai.api_key_env', 'OPENAI_API_KEY')
        api_key = os.getenv(api_key_env)
        
        if not api_key:
            logger.info(f"OpenAI API key not found ({api_key_env}), skipping OpenAI models")
            return []
        
        try:
            logger.info("Enumerating OpenAI models")
            base_url = self.config.get('models.openai.base_url', 'https://api.openai.com/v1')
            
            response = requests.get(
                f"{base_url}/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            models = []
            
            for model_info in data.get('data', []):
                model_id = model_info.get('id', '')
                
                # Only include relevant models (GPT-4, GPT-3.5, etc.)
                if not any(prefix in model_id for prefix in ['gpt-4', 'gpt-3.5', 'gpt-4o']):
                    continue
                
                model = self._create_openai_model(model_id)
                models.append(model)
                logger.info(f"Found OpenAI model: {model_id}")
            
            return models
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error enumerating OpenAI models: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error enumerating OpenAI models: {e}")
            return []
    
    def _create_openai_model(self, model_id: str) -> AIModel:
        """
        Create an AIModel object for an OpenAI model.
        
        Args:
            model_id: OpenAI model ID
            
        Returns:
            AIModel object
        """
        # Determine capabilities based on model name
        capabilities = ["text"]
        if "vision" in model_id or "gpt-4o" in model_id or "gpt-4-turbo" in model_id:
            capabilities.append("image")
        
        return AIModel(
            name=f"openai_{model_id.replace('-', '_').replace('.', '_')}",
            type="online",
            provider="openai",
            model_name=model_id,
            capabilities=capabilities,
            description=f"OpenAI model: {model_id}",
            api_key_env=self.config.get('models.openai.api_key_env', 'OPENAI_API_KEY')
        )
    
    def _enumerate_anthropic_models(self) -> List[AIModel]:
        """
        Enumerate models available from Anthropic.
        Note: Anthropic doesn't provide a models list endpoint,
        so we use a known list of available models.
        
        Returns:
            List of AIModel objects from Anthropic
        """
        api_key_env = self.config.get('models.anthropic.api_key_env', 'ANTHROPIC_API_KEY')
        api_key = os.getenv(api_key_env)
        
        if not api_key:
            logger.info(f"Anthropic API key not found ({api_key_env}), skipping Anthropic models")
            return []
        
        logger.info("Enumerating Anthropic models")
        
        # Anthropic's known models (as of 2024)
        known_models = [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]
        
        models = []
        for model_id in known_models:
            model = self._create_anthropic_model(model_id)
            models.append(model)
            logger.info(f"Added Anthropic model: {model_id}")
        
        return models
    
    def _create_anthropic_model(self, model_id: str) -> AIModel:
        """
        Create an AIModel object for an Anthropic model.
        
        Args:
            model_id: Anthropic model ID
            
        Returns:
            AIModel object
        """
        # All Claude 3 models support vision
        capabilities = ["text", "image"]
        
        return AIModel(
            name=f"anthropic_{model_id.replace('-', '_').replace('.', '_')}",
            type="online",
            provider="anthropic",
            model_name=model_id,
            capabilities=capabilities,
            description=f"Anthropic model: {model_id}",
            api_key_env=self.config.get('models.anthropic.api_key_env', 'ANTHROPIC_API_KEY')
        )
    
    def _create_ollama_model(self, model_name: str) -> AIModel:
        """
        Create an AIModel object for an Ollama model.
        
        Args:
            model_name: Ollama model name
            
        Returns:
            AIModel object
        """
        # Determine capabilities based on model name
        capabilities = ["text"]
        if any(x in model_name.lower() for x in ['llava', 'vision', 'bakllava']):
            capabilities.append("image")
        
        return AIModel(
            name=model_name.replace(':', '_'),
            type="local",
            provider="ollama",
            model_name=model_name,
            capabilities=capabilities,
            description=f"Local Ollama model: {model_name}"
        )
    
    def _enumerate_ollama_models(self) -> List[AIModel]:
        """
        Enumerate models available in Ollama.
        
        Returns:
            List of AIModel objects from Ollama
        """
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            response.raise_for_status()
            
            data = response.json()
            models = []
            
            for model_info in data.get('models', []):
                model_name = model_info.get('name', '')
                model = self._create_ollama_model(model_name)
                models.append(model)
                logger.info(f"Found local Ollama model: {model_name}")
            
            return models
            
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to Ollama at {self.ollama_base_url}. Is Ollama running?")
            return []
        except Exception as e:
            logger.error(f"Error enumerating Ollama models: {e}")
            return []
    
    def _check_ollama_model_exists(self, model_name: str) -> bool:
        """
        Check if a model exists in Ollama.
        
        Args:
            model_name: Name of the model to check
            
        Returns:
            True if model exists, False otherwise
        """
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            response.raise_for_status()
            
            data = response.json()
            existing_models = [m.get('name', '') for m in data.get('models', [])]
            
            return model_name in existing_models
            
        except Exception as e:
            logger.error(f"Error checking if Ollama model {model_name} exists: {e}")
            return False
    
    def _download_ollama_model(self, model_name: str) -> bool:
        """
        Download a model in Ollama.
        
        Args:
            model_name: Name of the model to download
            
        Returns:
            True if download succeeded, False otherwise
        """
        try:
            logger.info(f"Pulling Ollama model: {model_name}")
            
            # Ollama pull endpoint streams responses
            response = requests.post(
                f"{self.ollama_base_url}/api/pull",
                json={"name": model_name},
                stream=True,
                timeout=300  # 5 minute timeout for downloads
            )
            response.raise_for_status()
            
            # Stream the download progress
            for line in response.iter_lines():
                if line:
                    logger.debug(line.decode('utf-8'))
            
            logger.info(f"Successfully downloaded model: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading Ollama model {model_name}: {e}")
            return False
    
    def download_required_models(self, mime_to_model_mapping: Dict[str, str], available_models: List[AIModel]) -> bool:
        """
        Download required models based on MIME-to-model mapping.
        Only downloads local models when in local_download mode.
        
        Args:
            mime_to_model_mapping: Dictionary mapping MIME types to model names
            available_models: List of currently available models
            
        Returns:
            True if all required models are available/downloaded, False otherwise
        """
        if self.discovery_method != "local_download":
            logger.info("Not in local_download mode, skipping model download check")
            return True
        
        if self.local_provider != "ollama":
            logger.warning(f"Model downloading not supported for provider: {self.local_provider}")
            return True
        
        # Get unique model names from mapping
        required_model_names = set(mime_to_model_mapping.values())
        logger.info(f"Required models from mapping: {required_model_names}")
        
        # Get list of local model names that need the actual model_name (not the friendly name)
        model_name_map = {model.name: model.model_name for model in available_models if model.type == "local"}
        
        all_available = True
        for model_name in required_model_names:
            # Get the actual Ollama model name
            ollama_model_name = model_name_map.get(model_name)
            
            if not ollama_model_name:
                # Check if this might be an online model
                online_model = next((m for m in available_models if m.name == model_name and m.type == "online"), None)
                if online_model:
                    logger.debug(f"Model {model_name} is online, skipping download check")
                    continue
                
                logger.warning(f"Model {model_name} not found in available models")
                all_available = False
                continue
            
            # Check if model exists
            if self._check_ollama_model_exists(ollama_model_name):
                logger.info(f"Model {model_name} ({ollama_model_name}) already exists")
            else:
                logger.info(f"Model {model_name} ({ollama_model_name}) not found, downloading...")
                if self._download_ollama_model(ollama_model_name):
                    logger.info(f"Successfully downloaded {ollama_model_name}")
                else:
                    logger.error(f"Failed to download {ollama_model_name}")
                    all_available = False
        
        return all_available
    
    def get_mapping_model(self) -> Optional[AIModel]:
        """
        Get the AI model used for MIME-to-model mapping.
        
        Returns:
            AIModel object for the mapping model, or None if not available
        """
        mapping_config = self.config.get('models.mapping_model', {})
        
        if not mapping_config:
            logger.warning("No mapping model configured")
            return None
        
        model = AIModel(
            name=f"mapping_{mapping_config.get('provider')}",
            type=mapping_config.get('type', 'online'),
            provider=mapping_config.get('provider', 'openai'),
            model_name=mapping_config.get('model_name', 'gpt-4'),
            capabilities=["text"],
            description="Model used for MIME-to-model mapping decisions",
            api_key_env=mapping_config.get('api_key_env')
        )
        
        if not model.is_available():
            logger.error("Mapping model is not available (missing API key?)")
            return None
        
        return model
    
    def verify_model_connectivity(self, model: AIModel) -> bool:
        """
        Verify connectivity to a specific AI model.
        
        Args:
            model: AIModel to verify
            
        Returns:
            True if model is accessible, False otherwise
        """
        logger.info(f"Verifying connectivity to {model.name} ({model.type}/{model.provider})")
        
        try:
            if model.type == "local" and model.provider == "ollama":
                # Test Ollama connectivity
                response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
                response.raise_for_status()
                
                # Check if specific model exists
                data = response.json()
                existing_models = [m.get('name', '') for m in data.get('models', [])]
                
                if model.model_name in existing_models:
                    logger.info(f"✓ {model.name} is accessible")
                    return True
                else:
                    logger.error(f"✗ {model.name} model not found in Ollama")
                    return False
            
            elif model.type == "online" and model.provider == "openai":
                # Test OpenAI connectivity
                import openai
                
                api_key = os.getenv(model.api_key_env)
                if not api_key:
                    logger.error(f"✗ {model.name} missing API key: {model.api_key_env}")
                    return False
                
                client = openai.OpenAI(api_key=api_key)
                # Simple test request
                response = client.models.retrieve(model.model_name.split('-')[0])  # Use base model name
                logger.info(f"✓ {model.name} is accessible")
                return True
            
            elif model.type == "online" and model.provider == "anthropic":
                # Test Anthropic connectivity
                import anthropic
                
                api_key = os.getenv(model.api_key_env)
                if not api_key:
                    logger.error(f"✗ {model.name} missing API key: {model.api_key_env}")
                    return False
                
                client = anthropic.Anthropic(api_key=api_key)
                # Simple test by creating client (will fail if invalid key)
                logger.info(f"✓ {model.name} API key is configured")
                return True
            
            else:
                logger.warning(f"Connectivity check not implemented for {model.provider}")
                return True  # Assume available if we can't check
        
        except Exception as e:
            logger.error(f"✗ {model.name} connectivity check failed: {e}")
            return False
    
    def verify_all_models(self, models: List[AIModel]) -> Dict[str, bool]:
        """
        Verify connectivity to all models.
        
        Args:
            models: List of AIModel objects to verify
            
        Returns:
            Dictionary mapping model name to connectivity status
        """
        logger.info(f"Verifying connectivity to {len(models)} models...")
        logger.info("="*60)
        
        results = {}
        for model in models:
            results[model.name] = self.verify_model_connectivity(model)
        
        logger.info("="*60)
        
        # Summary
        accessible = sum(1 for status in results.values() if status)
        total = len(results)
        
        if accessible == total:
            logger.info(f"✓ All {total} models are accessible")
        else:
            logger.warning(f"⚠ {accessible}/{total} models are accessible")
            failed = [name for name, status in results.items() if not status]
            logger.warning(f"Failed models: {', '.join(failed)}")
        
        return results
