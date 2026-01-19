"""Stage 2: AI model discovery, mapping, and verification."""

import logging
from typing import List, Optional

from .config import Config
from .models import Stage1Result, Stage2Result
from .model_discovery import ModelDiscovery
from .mime_mapper import MimeModelMapper
from .cache import CacheManager


logger = logging.getLogger(__name__)


class Stage2Processor:
    """Stage 2: Discovers AI models and creates MIME-to-model mappings."""
    
    def __init__(self, config: Config, cache_manager: Optional[CacheManager] = None, progress_manager=None):
        """
        Initialize the Stage 2 processor.
        
        Args:
            config: Configuration object
            cache_manager: Optional CacheManager for caching results
            progress_manager: Optional ProgressManager for progress tracking
        """
        self.config = config
        self.model_discovery = ModelDiscovery(config)
        self.cache_manager = cache_manager or CacheManager(
            cache_dir=config.cache_directory,
            enabled=config.cache_enabled
        )
        self.progress_manager = progress_manager
    
    def process(self, stage1_result: Stage1Result, use_cache: bool = True) -> Stage2Result:
        """
        Process Stage 1 results to discover models and create mappings.
        
        Args:
            stage1_result: Results from Stage 1 containing file information
            use_cache: Whether to use cached results if available
            
        Returns:
            Stage2Result object containing Stage 1 results plus AI model information
        """
        # Try to load complete result from cache first
        if use_cache:
            cached_result = self.cache_manager.get_stage2_result_cache(
                stage1_result.source_directory
            )
            if cached_result:
                logger.info(f"Loaded complete Stage 2 result from cache")
                logger.info(f"  Models: {len(cached_result.available_models)}")
                logger.info(f"  Mappings: {len(cached_result.mime_to_model_mapping)}")
                return cached_result
        
        logger.info("=" * 60)
        logger.info("Starting Stage 2: AI model discovery and mapping")
        if use_cache:
            logger.info(f"Cache enabled: Will save results for future use")
        logger.info("=" * 60)
        
        # Start progress tracking
        if self.progress_manager:
            self.progress_manager.start_stage(2, "Model Discovery", 3)  # 3 steps: discover, map, verify
            self.progress_manager.update_file_info("Discovering available AI models...")
        
        # Initialize Stage 2 result with Stage 1 data
        result = Stage2Result(stage1_result=stage1_result)
        
        # Discover available AI models
        logger.info("Discovering available AI models")
        available_models = self.model_discovery.discover_models()
        
        if self.progress_manager:
            self.progress_manager.update_stage_progress(1)
        
        if not available_models:
            logger.warning("No AI models available!")
            logger.warning("Stage 2 cannot proceed without models")
            if self.progress_manager:
                self.progress_manager.complete_stage()
            return result
        
        logger.info(f"Found {len(available_models)} available models:")
        for model in available_models:
            logger.info(f"  - {model.name} ({model.type}/{model.provider})")
            logger.info(f"    Capabilities: {', '.join(model.capabilities)}")
        
        result.set_models(available_models)
        
        # Create MIME type to model mapping using AI
        if stage1_result.unique_mime_types:
            if self.progress_manager:
                self.progress_manager.update_file_info(
                    f"Mapping {len(stage1_result.unique_mime_types)} MIME types to models..."
                )
            logger.info("=" * 60)
            logger.info("Creating AI-powered MIME-to-model mapping")
            logger.info("=" * 60)
            logger.info(f"MIME types to map: {stage1_result.unique_mime_types}")
            
            mapping_model = self.model_discovery.get_mapping_model()
            logger.info(f"Using mapping model: {mapping_model.name}")
            
            mapper = MimeModelMapper(mapping_model)
            mime_mapping = mapper.create_mapping(
                stage1_result.unique_mime_types,
                available_models
            )
            
            result.set_mime_mapping(mime_mapping)
            
            logger.info("MIME-to-model mapping created:")
            for mime_type, model_name in mime_mapping.items():
                logger.info(f"  {mime_type} -> {model_name}")
            
            # Download required models if in local_download mode
            logger.info("=" * 60)
            logger.info("Ensuring required models are available")
            logger.info("=" * 60)
            
            models_ready = self.model_discovery.download_required_models(
                mime_mapping,
                available_models
            )
            
            if not models_ready:
                logger.warning("Some required models could not be downloaded")
            else:
                logger.info("All required models are available")
            
            # Verify connectivity to all models
            if self.progress_manager:
                self.progress_manager.update_file_info(
                    f"Verifying connectivity to {len(available_models)} models..."
                )
                self.progress_manager.update_stage_progress(2)
            
            logger.info("=" * 60)
            logger.info("Verifying AI model connectivity")
            logger.info("=" * 60)
            
            connectivity_results = self.model_discovery.verify_all_models(available_models)
            result.set_model_connectivity(connectivity_results)
            
            if self.progress_manager:
                self.progress_manager.update_stage_progress(3)
            
            # Log connectivity results
            logger.info("Model connectivity status:")
            for model_name, is_connected in connectivity_results.items():
                status = "✓ Connected" if is_connected else "✗ Failed"
                logger.info(f"  {model_name}: {status}")
            
            # Check if all required models are accessible
            required_model_names = set(mime_mapping.values())
            required_accessible = all(
                connectivity_results.get(model_name, False)
                for model_name in required_model_names
            )
            
            if not required_accessible:
                failed_required = [
                    name for name in required_model_names
                    if not connectivity_results.get(name, False)
                ]
                logger.error(f"Required models not accessible: {', '.join(failed_required)}")
                logger.warning("Some files may not be processable")
            else:
                logger.info("✓ All required models verified and accessible")
        else:
            logger.warning("No MIME types to map")
        
        # Complete stage progress
        if self.progress_manager:
            self.progress_manager.complete_stage()
        
        # Save complete result to cache
        if use_cache:
            self.cache_manager.save_stage2_result_cache(result)
        
        logger.info("=" * 60)
        logger.info("Stage 2 complete!")
        logger.info(f"  Models discovered: {len(result.available_models)}")
        logger.info(f"  MIME mappings: {len(result.mime_to_model_mapping)}")
        logger.info(f"  Connected models: {sum(result.model_connectivity.values())}/{len(result.model_connectivity)}")
        logger.info("=" * 60)
        
        return result
