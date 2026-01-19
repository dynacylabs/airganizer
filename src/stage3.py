"""Stage 3: AI-powered file analysis and metadata generation."""

import logging
from datetime import datetime
from typing import Optional

from .config import Config
from .models import Stage2Result, Stage3Result, FileAnalysis, FileInfo
from .model_discovery import ModelDiscovery
from .ai_interface import AIModelInterface
from .cache import CacheManager


logger = logging.getLogger(__name__)


class Stage3Processor:
    """Stage 3: Analyzes each file with AI to generate descriptions and tags."""
    
    def __init__(self, config: Config, cache_manager: Optional[CacheManager] = None):
        """
        Initialize the Stage 3 processor.
        
        Args:
            config: Configuration object
            cache_manager: Optional CacheManager for caching results
        """
        self.config = config
        self.model_discovery = ModelDiscovery(config)
        self.ai_interface = AIModelInterface(config)
        self.cache_manager = cache_manager or CacheManager(
            cache_dir=config.cache_directory,
            enabled=config.cache_enabled,
            ttl_hours=config.cache_ttl_hours
        )
    
    def _analyze_single_file(
        self,
        file_info: FileInfo,
        model_name: str,
        available_models: list
    ) -> FileAnalysis:
        """
        Analyze a single file with its assigned model.
        
        Args:
            file_info: FileInfo object from Stage 1
            model_name: Name of the model to use
            available_models: List of available AIModel objects
            
        Returns:
            FileAnalysis object with results or error
        """
        try:
            # Find the model object
            logger.debug(f"Looking for model '{model_name}' for file: {file_info.file_path}")
            model = None
            for m in available_models:
                if m.name == model_name:
                    model = m
                    break
            
            if not model:
                logger.error(f"Model not found: {model_name}")
                logger.debug(f"Available models: {[m.name for m in available_models]}")
                return FileAnalysis(
                    file_path=file_info.file_path,
                    assigned_model=model_name,
                    proposed_filename=file_info.file_name,
                    description="Model not available",
                    tags=['error'],
                    error=f"Model not found: {model_name}"
                )
            
            # Prepare metadata for analysis
            metadata = {
                'file_size': file_info.file_size,
                'exif_data': file_info.exif_data,
                'metadata': file_info.metadata
            }
            
            # Call AI model
            logger.info(f"Analyzing: {file_info.file_name} with {model_name}")
            analysis_result = self.ai_interface.analyze_file(
                file_info.file_path,
                file_info.mime_type,
                metadata,
                model
            )
            
            # Create FileAnalysis object
            return FileAnalysis(
                file_path=file_info.file_path,
                assigned_model=model_name,
                proposed_filename=analysis_result['proposed_filename'],
                description=analysis_result['description'],
                tags=analysis_result['tags'],
                analysis_timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error analyzing {file_info.file_path}: {e}")
            return FileAnalysis(
                file_path=file_info.file_path,
                assigned_model=model_name,
                proposed_filename=file_info.file_name,
                description="Analysis failed",
                tags=['error'],
                error=str(e)
            )
    
    def process(
        self,
        stage2_result: Stage2Result,
        use_cache: bool = True,
        max_files: Optional[int] = None
    ) -> Stage3Result:
        """
        Process Stage 2 results to analyze files with AI.
        
        Args:
            stage2_result: Results from Stage 2
            use_cache: Whether to use cached results if available
            max_files: Optional limit on number of files to process (for testing)
            
        Returns:
            Stage3Result object with AI analysis for each file
        """
        logger.info("=" * 60)
        logger.info("Starting Stage 3: AI-powered file analysis")
        logger.debug(f"Stage3Processor configuration:")
        logger.debug(f"  - cache_enabled: {self.cache_manager.enabled}")
        logger.debug(f"  - cache_dir: {self.cache_manager.cache_dir}")
        if max_files:
            logger.info(f"Limited to {max_files} files for this run")
        if use_cache:
            logger.info("Cache enabled: Will save results for future use")
        logger.info("=" * 60)
        
        # Initialize Stage 3 result
        result = Stage3Result(stage2_result=stage2_result)
        
        # Get available models as AIModel objects (not ModelInfo)
        logger.debug("Discovering available AI models...")
        available_models = self.model_discovery.discover_models()
        logger.debug(f"Found {len(available_models)} available models")
        
        # Get files to process
        files_to_process = stage2_result.stage1_result.files
        if max_files:
            files_to_process = files_to_process[:max_files]
        
        total_files = len(files_to_process)
        logger.info(f"Processing {total_files} files")
        
        # Process each file
        for idx, file_info in enumerate(files_to_process, 1):
            logger.info("-" * 60)
            logger.info(f"File {idx}/{total_files}: {file_info.file_name}")
            logger.info(f"  Path: {file_info.file_path}")
            logger.info(f"  MIME: {file_info.mime_type}")
            logger.info(f"  Size: {file_info.file_size} bytes")
            
            # Get assigned model
            model_name = stage2_result.get_model_for_file(file_info)
            
            if not model_name:
                logger.warning(f"  No model assigned for MIME type: {file_info.mime_type}")
                analysis = FileAnalysis(
                    file_path=file_info.file_path,
                    assigned_model="none",
                    proposed_filename=file_info.file_name,
                    description="No model assigned",
                    tags=['unassigned'],
                    error="No model mapping for this MIME type"
                )
                result.add_analysis(analysis)
                continue
            
            logger.info(f"  Assigned model: {model_name}")
            
            # Check if model is connected
            if not stage2_result.model_connectivity.get(model_name, False):
                logger.warning(f"  Model not connected: {model_name}")
                analysis = FileAnalysis(
                    file_path=file_info.file_path,
                    assigned_model=model_name,
                    proposed_filename=file_info.file_name,
                    description="Model not available",
                    tags=['unavailable'],
                    error=f"Model not connected: {model_name}"
                )
                result.add_analysis(analysis)
                continue
            
            # Analyze the file
            analysis = self._analyze_single_file(file_info, model_name, available_models)
            
            # Log results
            if analysis.error:
                logger.error(f"  ✗ Analysis failed: {analysis.error}")
            else:
                logger.info(f"  ✓ Analysis complete")
                logger.info(f"    Proposed name: {analysis.proposed_filename}")
                logger.info(f"    Description: {analysis.description[:100]}...")
                logger.info(f"    Tags: {', '.join(analysis.tags)}")
            
            result.add_analysis(analysis)
        
        logger.info("=" * 60)
        logger.info("Stage 3 complete!")
        logger.info(f"  Total files: {total_files}")
        logger.info(f"  Successfully analyzed: {result.total_analyzed}")
        logger.info(f"  Errors: {result.total_errors}")
        logger.info("=" * 60)
        
        return result
