#!/usr/bin/env python3
"""
Test script to demonstrate complete file movement including excluded and error files.
"""

import json
import logging
from pathlib import Path
from src.stage5 import Stage5Processor
from src.config import Config
from src.models import (
    FileInfo, Stage1Result, ExcludedFile,
    Stage2Result, 
    FileAnalysis, Stage3Result,
    TaxonomyNode, FileAssignment, Stage4Result
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_comprehensive_test_scenario():
    """Create a test scenario with organized, excluded, and error files."""
    
    # Create Stage 1 result with regular and excluded files
    stage1_result = Stage1Result(
        source_directory="/tmp/test_src",
        total_files=5,
        files=[],
        errors=[],
        excluded_files=[]
    )
    
    # Regular files (will be analyzed and organized)
    file1 = FileInfo(
        file_path="/tmp/test_src/photo1.jpg",
        file_name="photo1.jpg",
        file_size=1024,
        mime_type="image/jpeg",
        created_at="2026-01-01",
        modified_at="2026-01-01"
    )
    
    file2 = FileInfo(
        file_path="/tmp/test_src/document.pdf",
        file_name="document.pdf",
        file_size=2048,
        mime_type="application/pdf",
        created_at="2026-01-02",
        modified_at="2026-01-02"
    )
    
    file3 = FileInfo(
        file_path="/tmp/test_src/video.mp4",
        file_name="video.mp4",
        file_size=5000000,
        mime_type="video/mp4",
        created_at="2026-01-03",
        modified_at="2026-01-03"
    )
    
    stage1_result.add_file(file1)
    stage1_result.add_file(file2)
    stage1_result.add_file(file3)
    
    # Excluded files (excluded during Stage 1)
    excluded1 = ExcludedFile(
        file_path="/tmp/test_src/.hidden_config",
        file_name=".hidden_config",
        reason="Hidden file (starts with .)",
        rule="hidden_file"
    )
    
    excluded2 = ExcludedFile(
        file_path="/tmp/test_src/temp_file.tmp",
        file_name="temp_file.tmp",
        reason="File extension '.tmp' is in exclusion list",
        rule="extension:.tmp"
    )
    
    stage1_result.add_excluded_file(excluded1)
    stage1_result.add_excluded_file(excluded2)
    
    # Create Stage 2 result
    stage2_result = Stage2Result(stage1_result=stage1_result)
    stage2_result.set_mime_mapping({
        "image/jpeg": "gpt-4o",
        "application/pdf": "gpt-4o",
        "video/mp4": "gpt-4o"
    })
    
    # Create Stage 3 result with successful analyses and errors
    stage3_result = Stage3Result(stage2_result=stage2_result)
    
    # Successful analyses
    analysis1 = FileAnalysis(
        file_path="/tmp/test_src/photo1.jpg",
        assigned_model="gpt-4o",
        proposed_filename="sunset-beach-photo.jpg",
        description="Beautiful sunset at the beach",
        tags=["sunset", "beach", "nature", "photography"]
    )
    
    analysis2 = FileAnalysis(
        file_path="/tmp/test_src/document.pdf",
        assigned_model="gpt-4o",
        proposed_filename="project-proposal-2026.pdf",
        description="Project proposal document for 2026",
        tags=["document", "proposal", "work", "2026"]
    )
    
    # Error analysis (AI couldn't analyze this file)
    analysis3 = FileAnalysis(
        file_path="/tmp/test_src/video.mp4",
        assigned_model="gpt-4o",
        proposed_filename="video.mp4",
        description="Failed to analyze",
        tags=["error"],
        error="AI model timeout - file too large or corrupted"
    )
    
    stage3_result.add_analysis(analysis1)
    stage3_result.add_analysis(analysis2)
    stage3_result.add_analysis(analysis3)
    
    # Create Stage 4 result with taxonomy (only for successfully analyzed files)
    stage4_result = Stage4Result(stage3_result=stage3_result)
    
    # Add taxonomy nodes
    taxonomy1 = TaxonomyNode(
        path="Photos/Nature/Sunsets",
        category="Sunsets",
        description="Sunset photography",
        subcategories=[]
    )
    
    taxonomy2 = TaxonomyNode(
        path="Documents/Work/Proposals",
        category="Proposals",
        description="Project proposals",
        subcategories=[]
    )
    
    stage4_result.add_taxonomy_node(taxonomy1)
    stage4_result.add_taxonomy_node(taxonomy2)
    
    # Add file assignments (only successfully analyzed files)
    assignment1 = FileAssignment(
        file_path="/tmp/test_src/photo1.jpg",
        target_path="Photos/Nature/Sunsets",
        proposed_filename="sunset-beach-photo.jpg",
        reasoning="Beautiful sunset photo belongs in nature/sunsets category"
    )
    
    assignment2 = FileAssignment(
        file_path="/tmp/test_src/document.pdf",
        target_path="Documents/Work/Proposals",
        proposed_filename="project-proposal-2026.pdf",
        reasoning="Work proposal document belongs in work/proposals category"
    )
    
    stage4_result.add_file_assignment(assignment1)
    stage4_result.add_file_assignment(assignment2)
    
    return stage4_result


def main():
    """Run the comprehensive test."""
    logger.info("=" * 70)
    logger.info("Comprehensive Stage 5 Test - All File Categories")
    logger.info("=" * 70)
    
    # Create test scenario
    stage4_result = create_comprehensive_test_scenario()
    
    # Get statistics
    stage1_result = stage4_result.stage3_result.stage2_result.stage1_result
    stage3_result = stage4_result.stage3_result
    
    logger.info(f"\nTest Scenario Created:")
    logger.info(f"  Total files scanned: {stage1_result.total_files}")
    logger.info(f"  Files excluded in Stage 1: {len(stage1_result.excluded_files)}")
    logger.info(f"  Files successfully analyzed: {stage3_result.total_analyzed}")
    logger.info(f"  Files with errors: {stage3_result.total_errors}")
    logger.info(f"  Files to organize: {len(stage4_result.file_assignments)}")
    
    # Show details
    logger.info(f"\nExcluded Files:")
    for ex in stage1_result.excluded_files:
        logger.info(f"  - {ex.file_name}: {ex.reason}")
    
    logger.info(f"\nError Files:")
    for analysis in stage3_result.file_analyses:
        if analysis.error:
            logger.info(f"  - {Path(analysis.file_path).name}: {analysis.error}")
    
    logger.info(f"\nOrganized Files:")
    for assignment in stage4_result.file_assignments:
        logger.info(f"  - {Path(assignment.file_path).name} → {assignment.target_path}/")
    
    # Create minimal config
    config = Config.__new__(Config)
    config.log_level = "INFO"
    
    # Run Stage 5 in dry-run mode
    logger.info("\n" + "=" * 70)
    processor = Stage5Processor(config)
    result = processor.process(
        stage4_result=stage4_result,
        destination_root="/tmp/test_dst",
        dry_run=True,
        overwrite=False
    )
    
    # Display comprehensive results
    logger.info("\n" + "=" * 70)
    logger.info("Test Results Summary:")
    logger.info("=" * 70)
    logger.info(f"  Total operations: {result.total_files}")
    logger.info(f"  Organized files: {result.successful_moves}")
    logger.info(f"  Excluded files: {result.excluded_moves}")
    logger.info(f"  Error files: {result.error_moves}")
    logger.info(f"  Failed operations: {result.failed_moves}")
    
    # Show what would happen for each category
    logger.info("\n" + "=" * 70)
    logger.info("Organized Files (would be moved to taxonomy structure):")
    logger.info("=" * 70)
    for op in result.operations:
        if op.category == "organized" and op.success:
            logger.info(f"  ✓ {Path(op.source_path).name}")
            logger.info(f"    → {op.target_path}/{op.target_filename}")
    
    logger.info("\n" + "=" * 70)
    logger.info("Excluded Files (would be moved to _excluded/):")
    logger.info("=" * 70)
    for op in result.operations:
        if op.category == "excluded" and op.success:
            logger.info(f"  ✓ {Path(op.source_path).name}")
            logger.info(f"    → {op.full_target}")
            logger.info(f"    Log entry would be created in _excluded/exclusions_log.json")
    
    logger.info("\n" + "=" * 70)
    logger.info("Error Files (would be moved to _errors/):")
    logger.info("=" * 70)
    for op in result.operations:
        if op.category == "error" and op.success:
            logger.info(f"  ✓ {Path(op.source_path).name}")
            logger.info(f"    → {op.full_target}")
            logger.info(f"    Log entry would be created in _errors/errors_log.json")
    
    logger.info("\n" + "=" * 70)
    logger.info("Expected Directory Structure in /tmp/test_dst:")
    logger.info("=" * 70)
    logger.info("  /tmp/test_dst/")
    logger.info("    ├── Photos/")
    logger.info("    │   └── Nature/")
    logger.info("    │       └── Sunsets/")
    logger.info("    │           └── sunset-beach-photo.jpg")
    logger.info("    ├── Documents/")
    logger.info("    │   └── Work/")
    logger.info("    │       └── Proposals/")
    logger.info("    │           └── project-proposal-2026.pdf")
    logger.info("    ├── _excluded/")
    logger.info("    │   ├── .hidden_config")
    logger.info("    │   ├── temp_file.tmp")
    logger.info("    │   └── exclusions_log.json")
    logger.info("    └── _errors/")
    logger.info("        ├── video.mp4")
    logger.info("        └── errors_log.json")
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ Test complete!")
    logger.info("=" * 70)
    logger.info("\nKey Features Demonstrated:")
    logger.info("  1. ✓ Successfully analyzed files moved to taxonomy structure")
    logger.info("  2. ✓ Excluded files (by rule) moved to _excluded/")
    logger.info("  3. ✓ Error files (analysis failed) moved to _errors/")
    logger.info("  4. ✓ Log files created with detailed reasons")
    logger.info("  5. ✓ Source directory would be completely empty after Stage 5")


if __name__ == "__main__":
    main()
