"""
Stage 1: File Enumeration and Metadata Collection
Main orchestrator for Airganizer Stage 1
"""

import json
import sys
import pickle
from pathlib import Path
from typing import List, Dict, Any, Set
from tqdm import tqdm

from .config import Config
from .file_enumerator import FileEnumerator
from .metadata_extractor import MetadataExtractor


class Stage1Processor:
    """Process files for Stage 1: enumeration and metadata collection"""
    
    def __init__(self, config: Config):
        """
        Initialize Stage 1 processor
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.file_enumerator = None
        self.metadata_extractor = None
        self.results: List[Dict[str, Any]] = []
        self.processed_files: Set[str] = set()  # Track processed files for resumability
        self.cache_dir = None
        self.cache_file = None
    
    def initialize(self):
        """Initialize components"""
        # Validate configuration
        self.config.validate()
        
        # Setup cache directory
        self.cache_dir = Path(self.config.get_cache_directory())
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "stage1_progress.pkl"
        
        # Initialize file enumerator
        self.file_enumerator = FileEnumerator(
            source_directory=self.config.get_source_directory(),
            include_patterns=self.config.get_include_patterns(),
            exclude_patterns=self.config.get_exclude_patterns()
        )
        
        # Initialize metadata extractor
        self.metadata_extractor = MetadataExtractor(
            calculate_hash=self.config.should_calculate_hash()
        )
    
    def _load_cache(self) -> bool:
        """
        Load progress from cache if available
        
        Returns:
            True if cache was loaded successfully
        """
        if not self.cache_file.exists():
            return False
        
        try:
            with open(self.cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            self.results = cache_data.get('results', [])
            self.processed_files = cache_data.get('processed_files', set())
            
            print(f"Loaded cache: {len(self.results)} files already processed")
            return True
        
        except Exception as e:
            print(f"Warning: Could not load cache: {e}")
            return False
    
    def _save_cache(self):
        """Save current progress to cache"""
        try:
            cache_data = {
                'results': self.results,
                'processed_files': self.processed_files,
            }
            
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
        
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")
    
    def _clear_cache(self):
        """Clear cache file"""
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
        except Exception as e:
            print(f"Warning: Could not clear cache: {e}")
    
    def process(self) -> List[Dict[str, Any]]:
        """
        Process all files and collect metadata
        
        Returns:
            List of metadata dictionaries for all files
        """
        print("Stage 1: File Enumeration and Metadata Collection")
        print("=" * 60)
        print(f"Source directory: {self.config.get_source_directory()}")
        print(f"Destination directory: {self.config.get_destination_directory()}")
        print(f"Cache directory: {self.cache_dir.absolute()}")
        print()
        
        # Try to resume from cache
        resumed = False
        if self.config.should_resume_from_cache():
            resumed = self._load_cache()
            if resumed:
                print()
        
        # Get all files
        print("Enumerating files...")
        files = self.file_enumerator.get_files_list()
        total_files = len(files)
        
        print(f"Found {total_files} files to process")
        if resumed:
            remaining = total_files - len(self.processed_files)
            print(f"Resuming: {len(self.processed_files)} already processed, {remaining} remaining")
        print()
        
        # Process each file
        print("Extracting metadata...")
        
        max_file_size = self.config.get_max_file_size()
        cache_interval = self.config.get_cache_interval()
        skipped_count = 0
        error_count = 0
        files_since_cache = 0
        
        for file_path in tqdm(files, desc="Processing files", unit="file"):
            try:
                # Skip if already processed (from cache)
                file_path_str = str(file_path.absolute())
                if file_path_str in self.processed_files:
                    continue
                
                # Check file size limit
                if max_file_size > 0 and file_path.stat().st_size > max_file_size:
                    skipped_count += 1
                    self.processed_files.add(file_path_str)
                    continue
                
                # Extract metadata
                file_metadata = self.metadata_extractor.extract_all_metadata(
                    file_path=file_path,
                    extract_exif=self.config.should_extract_exif(),
                    extract_audio=self.config.should_extract_audio_metadata(),
                    extract_video=self.config.should_extract_video_metadata(),
                    extract_document=self.config.should_extract_document_metadata()
                )
                
                self.results.append(file_metadata.to_dict())
                self.processed_files.add(file_path_str)
                files_since_cache += 1
                
                # Save cache periodically
                if files_since_cache >= cache_interval:
                    self._save_cache()
                    files_since_cache = 0
            
            except Exception as e:
                error_count += 1
                print(f"\nError processing {file_path}: {e}", file=sys.stderr)
                self.processed_files.add(file_path_str)  # Mark as processed to avoid retrying
        
        # Final cache save
        if files_since_cache > 0:
            self._save_cache()
        
        print()
        print("=" * 60)
        print(f"Processing complete!")
        print(f"Total files found: {total_files}")
        print(f"Successfully processed: {len(self.results)}")
        if skipped_count > 0:
            print(f"Skipped (size limit): {skipped_count}")
        if error_count > 0:
            print(f"Errors: {error_count}")
        print()
        
        return self.results
    
    def save_results(self, output_file: str = None):
        """
        Save results to JSON file
        
        Args:
            output_file: Output file path (uses config if not specified)
        """
        if output_file is None:
            output_file = self.config.get_stage1_output_file()
        
        output_path = Path(output_file)
        
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare output data
        output_data = {
            'stage': 1,
            'description': 'File enumeration and metadata collection',
            'source_directory': self.config.get_source_directory(),
            'destination_directory': self.config.get_destination_directory(),
            'total_files': len(self.results),
            'files': self.results
        }
        
        # Save to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        print(f"Results saved to: {output_path.absolute()}")
        
        # Clear cache after successful completion
        self._clear_cache()
        
        # Print statistics
        total_size = sum(file['file_size'] for file in self.results)
        total_size_human = MetadataExtractor._human_readable_size(total_size)
        
        print()
        print("Statistics:")
        print(f"  Total files: {len(self.results)}")
        print(f"  Total size: {total_size_human}")
        
        # Count by media type
        media_types = {}
        for file in self.results:
            media_type = file.get('media_type', 'unknown')
            media_types[media_type] = media_types.get(media_type, 0) + 1
        
        if media_types:
            print()
            print("Files by media type:")
            for media_type, count in sorted(media_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  {media_type or 'unknown'}: {count}")
    
    def run(self):
        """Run the complete Stage 1 process"""
        try:
            self.initialize()
            self.process()
            self.save_results()
        except Exception as e:
            print(f"Error during Stage 1 processing: {e}", file=sys.stderr)
            raise


def main():
    """Main entry point for Stage 1"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Airganizer Stage 1: File Enumeration and Metadata Collection'
    )
    parser.add_argument(
        '--config',
        '-c',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    parser.add_argument(
        '--output',
        '-o',
        help='Output file path (overrides config)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = Config(args.config)
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {args.config}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Run Stage 1
    processor = Stage1Processor(config)
    
    try:
        processor.initialize()
        processor.process()
        processor.save_results(args.output)
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
