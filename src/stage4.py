"""Stage 4: Taxonomic structure planning using AI."""

import json
import logging
from typing import List, Dict, Any, Optional

from .config import Config
from .models import Stage3Result, Stage4Result, TaxonomyNode, FileAssignment
from .model_discovery import ModelDiscovery
from .ai_interface import AIModelInterface
from .cache import CacheManager


logger = logging.getLogger(__name__)


class Stage4Processor:
    """Stage 4: Creates taxonomic directory structure based on file analysis."""
    
    def __init__(self, config: Config, cache_manager: Optional[CacheManager] = None, progress_manager=None):
        """
        Initialize the Stage 4 processor.
        
        Args:
            config: Configuration object
            cache_manager: Optional CacheManager for caching results
            progress_manager: Optional ProgressManager for progress tracking
        """
        self.config = config
        self.model_discovery = ModelDiscovery(config)
        self.ai_interface = AIModelInterface(config)
        self.cache_manager = cache_manager or CacheManager(
            cache_dir=config.cache_directory,
            enabled=config.cache_enabled
        )
        self.progress_manager = progress_manager
        logger.debug("Stage4Processor initialized")
        logger.debug(f"  - Taxonomic structure planning enabled")
    
    def _build_taxonomy_prompt(
        self,
        files_data: List[Dict[str, Any]],
        existing_taxonomy: Optional[List[TaxonomyNode]] = None
    ) -> str:
        """
        Build prompt for AI to create/update taxonomic structure.
        
        Args:
            files_data: List of file data (analysis + metadata)
            existing_taxonomy: Optional existing taxonomy to build upon
            
        Returns:
            Prompt string
        """
        prompt = """You are an expert at creating taxonomic organizational systems for files.

Your task is to analyze the provided files and create a hierarchical directory structure that logically organizes them using taxonomic principles.

Guidelines:
1. Create a multi-level hierarchy (not just category/subcategory)
2. Use clear, descriptive category names
3. Group related items together
4. The structure should be intuitive and scalable
5. Use standard taxonomy practices (broader categories contain narrower ones)
6. Each category should have a clear purpose

"""
        
        if existing_taxonomy:
            prompt += f"""Existing Taxonomy:
You have an existing taxonomy with {len(existing_taxonomy)} categories. Build upon this structure, adding new categories as needed.

Current categories:
"""
            for node in existing_taxonomy[:20]:  # Show first 20
                prompt += f"- {node.path}: {node.description} ({node.file_count} files)\n"
            
            if len(existing_taxonomy) > 20:
                prompt += f"... and {len(existing_taxonomy) - 20} more categories\n"
            
            prompt += "\n"
        
        prompt += f"""Files to Organize ({len(files_data)} files):

"""
        
        # Include file summaries
        for i, file_data in enumerate(files_data[:100], 1):  # Limit to 100 for context
            file_info = file_data.get('file_info', {})
            analysis = file_data.get('analysis', {})
            
            if not analysis:
                continue
            
            prompt += f"""{i}. File: {file_info.get('file_name', 'unknown')}
   MIME: {file_info.get('mime_type', 'unknown')}
   Description: {analysis.get('description', 'N/A')}
   Tags: {', '.join(analysis.get('tags', []))}

"""
        
        if len(files_data) > 100:
            prompt += f"\n... and {len(files_data) - 100} more files to organize\n\n"
        
        prompt += """
Please respond with a JSON object containing:
1. "taxonomy": Array of category objects with:
   - "path": Full path (e.g., "Documents/Work/Reports")
   - "category": Last segment of path (e.g., "Reports")
   - "description": What files belong here
   - "subcategories": Array of child category paths

2. "assignments": Array of file assignments with:
   - "file_index": Index of the file (1-based from above list)
   - "target_path": The category path where it belongs
   - "reasoning": Brief explanation why it goes there

Example response:
{
  "taxonomy": [
    {
      "path": "Photos",
      "category": "Photos",
      "description": "All photographic images",
      "subcategories": ["Photos/Nature", "Photos/People", "Photos/Architecture"]
    },
    {
      "path": "Photos/Nature",
      "category": "Nature",
      "description": "Natural landscapes, wildlife, and outdoor scenes",
      "subcategories": ["Photos/Nature/Wildlife", "Photos/Nature/Landscapes"]
    },
    {
      "path": "Photos/Nature/Wildlife",
      "category": "Wildlife",
      "description": "Animals in their natural habitats",
      "subcategories": []
    }
  ],
  "assignments": [
    {
      "file_index": 1,
      "target_path": "Photos/Nature/Wildlife",
      "reasoning": "Contains image of golden eagle, fits wildlife category"
    }
  ]
}

Important:
- Create as many levels as needed (not limited to 2-3 levels)
- Be specific with categories (e.g., "Wildlife/Birds/Raptors" not just "Animals")
- Each file must be assigned to exactly one category
- Categories should form a proper tree (each has one parent except root)
- Use descriptive, professional category names
"""
        
        return prompt
    
    def _parse_taxonomy_response(
        self,
        response_text: str,
        files_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Parse AI response into taxonomy and assignments.
        
        Args:
            response_text: Raw AI response
            files_data: Original files data for reference
            
        Returns:
            Dictionary with taxonomy and assignments
        """
        try:
            # Extract JSON from response
            logger.debug(f"Parsing taxonomy response (length: {len(response_text)} chars)")
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
            
            result = json.loads(json_text)
            logger.debug(f"Successfully parsed JSON with keys: {list(result.keys())}")
            
            # Validate structure
            if 'taxonomy' not in result or 'assignments' not in result:
                raise ValueError("Missing required fields in response")
            
            logger.debug(f"Taxonomy contains {len(result['taxonomy'])} nodes")
            logger.debug(f"Assignments contains {len(result['assignments'])} files")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse taxonomy response: {e}")
            logger.debug(f"Raw response: {response_text[:500]}")
            
            # Return minimal fallback structure
            return {
                'taxonomy': [
                    {
                        'path': 'Uncategorized',
                        'category': 'Uncategorized',
                        'description': 'Files that could not be categorized',
                        'subcategories': []
                    }
                ],
                'assignments': [
                    {
                        'file_index': i + 1,
                        'target_path': 'Uncategorized',
                        'reasoning': 'Automatic fallback'
                    }
                    for i in range(len(files_data))
                ]
            }
    
    def _call_taxonomy_ai(
        self,
        prompt: str,
        model: Any
    ) -> str:
        """
        Call AI model for taxonomy generation.
        
        Args:
            prompt: The taxonomy prompt
            model: AIModel object
            
        Returns:
            AI response text
        """
        import requests
        import os
        
        logger.debug(f"[Taxonomy AI] Calling {model.provider}/{model.name}")
        logger.debug(f"[Taxonomy AI] Prompt length: {len(prompt)} chars")
        
        if model.provider == "openai":
            api_key = os.getenv(model.api_key_env)
            base_url = self.config.get('models.openai.base_url', 'https://api.openai.com/v1')
            logger.debug(f"[OpenAI] Endpoint: {base_url}/chat/completions")
            logger.debug(f"[OpenAI] Model: {model.model_name}")
            
            response = requests.post(
                f'{base_url}/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': model.model_name,
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': self.config.stage4_max_tokens,
                    'temperature': self.config.stage4_temperature
                },
                timeout=self.config.stage4_timeout
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
            
        elif model.provider == "anthropic":
            api_key = os.getenv(model.api_key_env)
            base_url = self.config.get('models.anthropic.base_url', 'https://api.anthropic.com')
            
            response = requests.post(
                f'{base_url}/v1/messages',
                headers={
                    'x-api-key': api_key,
                    'anthropic-version': '2023-06-01',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': model.model_name,
                    'max_tokens': self.config.stage4_max_tokens,
                    'messages': [{
                        'role': 'user',
                        'content': prompt
                    }]
                },
                timeout=self.config.stage4_timeout
            )
            response.raise_for_status()
            return response.json()['content'][0]['text']
            
        elif model.provider == "ollama":
            base_url = self.config.get('models.ollama.base_url', 'http://localhost:11434')
            
            response = requests.post(
                f'{base_url}/api/generate',
                json={
                    'model': model.model_name,
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': self.config.stage4_temperature,
                        'num_predict': self.config.stage4_max_tokens
                    }
                },
                timeout=self.config.stage4_timeout
            )
            response.raise_for_status()
            return response.json()['response']
        
        else:
            raise ValueError(f"Unsupported provider: {model.provider}")
    
    def process(
        self,
        stage3_result: Stage3Result,
        batch_size: int = 100,
        use_cache: bool = True
    ) -> Stage4Result:
        """
        Process Stage 3 results to create taxonomic organization structure.
        
        Args:
            stage3_result: Results from Stage 3
            batch_size: Number of files to process in each batch
            use_cache: Whether to use cached results if available
            
        Returns:
            Stage4Result with taxonomy and file assignments
        """
        logger.info("=" * 60)
        logger.info("Starting Stage 4: Taxonomic Structure Planning")
        logger.debug(f"Stage4Processor configuration:")
        logger.debug(f"  - batch_size: {batch_size}")
        logger.debug(f"  - cache_enabled: {self.cache_manager.enabled}")
        logger.debug(f"  - cache_dir: {self.cache_manager.cache_dir}")
        if use_cache:
            logger.info("Cache enabled: Will use cached results if available")
        logger.info("=" * 60)
        
        # Try to load from cache first
        if use_cache and self.cache_manager.enabled:
            cached_result = self.cache_manager.get_stage4_result_cache(
                stage3_result.stage2_result.stage1_result.source_directory
            )
            if cached_result:
                logger.info("✓ Loaded Stage 4 results from cache")
                logger.info(f"  Total categories: {cached_result.total_categories}")
                logger.info(f"  Files assigned: {cached_result.total_assigned}")
                logger.info(f"  Max depth: {max(len(n.path.split('/')) for n in cached_result.taxonomy) if cached_result.taxonomy else 0}")
                logger.info("=" * 60)
                return cached_result
        
        # Initialize result
        result = Stage4Result(stage3_result=stage3_result)
        
        # Get unified file data from Stage 3
        logger.debug("Retrieving unified file data from Stage 3...")
        files_data = stage3_result.get_all_unified_data()
        
        # Check if garbage detection is enabled
        garbage_detection_enabled = self.config.get('general.enable_garbage_detection', True)
        garbage_folder = self.config.get('general.garbage_folder', '_garbage')
        process_garbage = garbage_detection_enabled and garbage_folder
        
        # Filter out files without analysis and optionally garbage files
        if process_garbage:
            files_with_analysis = [
                f for f in files_data
                if f.get('analysis') and not f['analysis'].get('error') and not f['analysis'].get('is_garbage', False)
            ]
            
            # Track garbage files separately
            garbage_files = [
                f for f in files_data
                if f.get('analysis') and f['analysis'].get('is_garbage', False)
            ]
        else:
            # If garbage detection disabled, treat all files normally
            files_with_analysis = [
                f for f in files_data
                if f.get('analysis') and not f['analysis'].get('error')
            ]
            garbage_files = []
        
        logger.debug(f"Filtered files: {len(files_data)} total -> {len(files_with_analysis)} with analysis, {len(garbage_files)} garbage")
        
        logger.info(f"Total files: {len(files_data)}")
        logger.info(f"Files with analysis: {len(files_with_analysis)}")
        if process_garbage:
            logger.info(f"Garbage files: {len(garbage_files)}")
        
        # Assign garbage files to garbage folder
        if process_garbage and garbage_files:
            logger.info(f"Assigning {len(garbage_files)} garbage files to '{garbage_folder}' folder")
            for file_data in garbage_files:
                analysis = file_data.get('analysis', {})
                assignment = FileAssignment(
                    file_path=file_data['file_info']['file_path'],
                    target_path=garbage_folder,
                    proposed_filename=analysis.get('proposed_filename', file_data['file_info']['file_name']),
                    reasoning=f"Identified as garbage: {analysis.get('description', 'No description')}"
                )
                result.add_file_assignment(assignment)
        
        if not files_with_analysis:
            logger.warning("No files with successful analysis (excluding garbage). Cannot create taxonomy.")
            return result
        
        # Get the mapping model for taxonomy creation
        mapping_model = self.model_discovery.get_mapping_model()
        logger.info(f"Using model for taxonomy: {mapping_model.name}")
        
        # Process files in batches to build taxonomy incrementally
        total_batches = (len(files_with_analysis) + batch_size - 1) // batch_size
        logger.info(f"Processing in {total_batches} batch(es) of {batch_size} files")
        
        # Start progress tracking
        if self.progress_manager:
            self.progress_manager.start_stage(4, "Taxonomy Planning", total_batches)
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(files_with_analysis))
            batch = files_with_analysis[start_idx:end_idx]
            
            # Update progress
            if self.progress_manager:
                self.progress_manager.update_file_info(
                    f"[Batch {batch_num + 1}/{total_batches}] Planning taxonomy for files {start_idx + 1}-{end_idx}\n"
                    f"Batch size: {len(batch)} files\n"
                    f"Total categories so far: {len(result.taxonomy)}"
                )
                self.progress_manager.update_stage_progress(batch_num + 1)
            
            logger.info("-" * 60)
            logger.info(f"Batch {batch_num + 1}/{total_batches}: Processing files {start_idx + 1}-{end_idx}")
            logger.debug(f"  Batch contains {len(batch)} files")
            
            # Build prompt with existing taxonomy
            existing_taxonomy = result.taxonomy if batch_num > 0 else None
            if existing_taxonomy:
                logger.debug(f"  Using existing taxonomy with {len(existing_taxonomy)} nodes")
            else:
                logger.debug("  Creating initial taxonomy (no existing structure)")
            
            prompt = self._build_taxonomy_prompt(batch, existing_taxonomy)
            logger.debug(f"  Generated prompt: {len(prompt)} chars")
            
            # Call AI
            logger.info("Calling AI to generate/update taxonomy...")
            try:
                response_text = self._call_taxonomy_ai(prompt, mapping_model)
                
                # Parse response
                parsed = self._parse_taxonomy_response(response_text, batch)
                
                # Update taxonomy (merge with existing)
                existing_paths = {node.path for node in result.taxonomy}
                new_nodes = 0
                
                for tax_data in parsed['taxonomy']:
                    if tax_data['path'] not in existing_paths:
                        node = TaxonomyNode(
                            path=tax_data['path'],
                            category=tax_data['category'],
                            description=tax_data['description'],
                            subcategories=tax_data.get('subcategories', [])
                        )
                        result.add_taxonomy_node(node)
                        existing_paths.add(tax_data['path'])
                        new_nodes += 1
                
                logger.info(f"  Added {new_nodes} new taxonomy nodes")
                logger.info(f"  Total taxonomy nodes: {len(result.taxonomy)}")
                
                # Create file assignments
                for assign_data in parsed['assignments']:
                    file_idx = assign_data['file_index'] - 1  # Convert to 0-based
                    if 0 <= file_idx < len(batch):
                        file_data = batch[file_idx]
                        analysis = file_data.get('analysis', {})
                        
                        assignment = FileAssignment(
                            file_path=file_data['file_info']['file_path'],
                            target_path=assign_data['target_path'],
                            proposed_filename=analysis.get('proposed_filename', file_data['file_info']['file_name']),
                            reasoning=assign_data.get('reasoning', '')
                        )
                        result.add_file_assignment(assignment)
                
                logger.info(f"  Assigned {len(parsed['assignments'])} files")
                
            except Exception as e:
                logger.error(f"Error processing batch {batch_num + 1}: {e}")
                # Assign to Uncategorized as fallback
                for file_data in batch:
                    assignment = FileAssignment(
                        file_path=file_data['file_info']['file_path'],
                        target_path='Uncategorized',
                        proposed_filename=file_data.get('analysis', {}).get('proposed_filename', file_data['file_info']['file_name']),
                        reasoning='Batch processing error'
                    )
                    result.add_file_assignment(assignment)
        
        # Save complete Stage 4 result to cache
        if use_cache and self.cache_manager.enabled:
            self.cache_manager.save_stage4_result_cache(result)
        
        # Complete stage progress
        if self.progress_manager:
            self.progress_manager.complete_stage()
        
        logger.info("=" * 60)
        logger.info("Stage 4 complete!")
        logger.info(f"  Total categories: {result.total_categories}")
        logger.info(f"  Files assigned: {result.total_assigned}")
        logger.info(f"  Max depth: {max(len(n.path.split('/')) for n in result.taxonomy) if result.taxonomy else 0}")
        logger.info("=" * 60)
        
        return result
