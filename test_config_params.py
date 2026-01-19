#!/usr/bin/env python3
"""
Test script to verify all configurable parameters are properly loaded from config.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config


def test_config_parameters():
    """Test all configurable parameters."""
    
    print("=" * 70)
    print("Testing Configurable Parameters")
    print("=" * 70)
    
    # Load config
    config = Config('config.example.yaml')
    
    print("\n" + "=" * 70)
    print("GENERAL SETTINGS")
    print("=" * 70)
    print(f"  log_level: {config.log_level}")
    print(f"  max_file_size: {config.max_file_size} bytes")
    print(f"  exclude_extensions: {config.exclude_extensions}")
    print(f"  exclude_dirs: {config.exclude_dirs}")
    
    print("\n" + "=" * 70)
    print("STAGE 1 SETTINGS")
    print("=" * 70)
    print(f"  recursive: {config.recursive}")
    print(f"  follow_symlinks: {config.follow_symlinks}")
    print(f"  include_hidden: {config.include_hidden}")
    
    print("\n" + "=" * 70)
    print("CACHE SETTINGS")
    print("=" * 70)
    print(f"  enabled: {config.cache_enabled}")
    print(f"  directory: {config.cache_directory}")
    print(f"  ttl_hours: {config.cache_ttl_hours}")
    
    print("\n" + "=" * 70)
    print("MODEL SETTINGS")
    print("=" * 70)
    print(f"  model_mode: {config.model_mode}")
    print(f"  discovery_method: {config.discovery_method}")
    
    print("\n" + "=" * 70)
    print("STAGE 3 SETTINGS (AI File Analysis)")
    print("=" * 70)
    print(f"  max_files: {config.stage3_max_files}")
    print(f"  ai.temperature: {config.stage3_temperature}")
    print(f"  ai.max_tokens: {config.stage3_max_tokens}")
    print(f"  ai.timeout: {config.stage3_timeout} seconds")
    
    print("\n" + "=" * 70)
    print("STAGE 4 SETTINGS (Taxonomic Structure Planning)")
    print("=" * 70)
    print(f"  batch_size: {config.stage4_batch_size}")
    print(f"  ai.temperature: {config.stage4_temperature}")
    print(f"  ai.max_tokens: {config.stage4_max_tokens}")
    print(f"  ai.timeout: {config.stage4_timeout} seconds")
    
    print("\n" + "=" * 70)
    print("STAGE 5 SETTINGS (Physical File Organization)")
    print("=" * 70)
    print(f"  overwrite: {config.stage5_overwrite}")
    print(f"  dry_run: {config.stage5_dry_run}")
    
    print("\n" + "=" * 70)
    print("MAPPING AI SETTINGS (MIME to Model Mapping)")
    print("=" * 70)
    print(f"  ai.temperature: {config.mapping_temperature}")
    print(f"  ai.max_tokens: {config.mapping_max_tokens}")
    print(f"  ai.timeout: {config.mapping_timeout} seconds")
    
    print("\n" + "=" * 70)
    print("All parameters loaded successfully!")
    print("=" * 70)
    
    # Verify all parameters have reasonable values
    assert config.log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    assert config.stage3_temperature >= 0.0 and config.stage3_temperature <= 2.0
    assert config.stage4_temperature >= 0.0 and config.stage4_temperature <= 2.0
    assert config.mapping_temperature >= 0.0 and config.mapping_temperature <= 2.0
    assert config.stage3_max_tokens > 0
    assert config.stage4_max_tokens > 0
    assert config.mapping_max_tokens > 0
    assert config.stage3_timeout > 0
    assert config.stage4_timeout > 0
    assert config.mapping_timeout > 0
    assert config.stage4_batch_size > 0
    
    print("\n✅ All validation checks passed!")
    print("\nParameter Summary:")
    print(f"  - Total configurable parameters: 25+")
    print(f"  - Stage 3 parameters: 4")
    print(f"  - Stage 4 parameters: 4")
    print(f"  - Stage 5 parameters: 2")
    print(f"  - Mapping parameters: 3")
    print(f"  - General/Cache/Model parameters: 12+")


if __name__ == "__main__":
    try:
        test_config_parameters()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
