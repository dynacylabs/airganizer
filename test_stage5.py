#!/usr/bin/env python3
"""
Quick test for Stage 5 file organization.
Creates a minimal test scenario to verify Stage 5 works correctly.
"""

import json
import logging
from pathlib import Path
from src.stage5 import Stage5Processor, MoveOperation
from src.config import Config
from src.models import (
    FileInfo, Stage1Result, 
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

def create_test_scenario():
    """Create a minimal test scenario."""
    
    # Create Stage 1 result
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
    
    stage1_result = Stage1Result(source_directory="/tmp/test_src")
    stage1_result.add_file(file1)
    stage1_result.add_file(file2)
    
    # Create Stage 2 result
    stage2_result = Stage2Result(stage1_result=stage1_result)
    stage2_result.set_mime_mapping({
        "image/jpeg": "gpt-4o",
        "application/pdf": "gpt-4o"
    })
    
    # Create Stage 3 result
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
    
    stage3_result = Stage3Result(stage2_result=stage2_result)
    stage3_result.add_analysis(analysis1)
    stage3_result.add_analysis(analysis2)
    
    # Create Stage 4 result with taxonomy
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
    
    # Add file assignments
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
    """Run the test."""
    logger.info("=" * 60)
    logger.info("Stage 5 Test - Dry Run Mode")
    logger.info("=" * 60)
    
    # Create test scenario
    stage4_result = create_test_scenario()
    
    logger.info(f"Created test scenario:")
    logger.info(f"  - {len(stage4_result.file_assignments)} files to organize")
    logger.info(f"  - {len(stage4_result.taxonomy)} categories")
    
    # Create minimal config
    config = Config.__new__(Config)
    config.log_level = "INFO"
    
    # Run Stage 5 in dry-run mode
    processor = Stage5Processor(config)
    result = processor.process(
        stage4_result=stage4_result,
        destination_root="/tmp/test_dst",
        dry_run=True,
        overwrite=False
    )
    
    # Display results
    logger.info("")
    logger.info("Test Results:")
    logger.info(f"  Total operations: {result.total_files}")
    logger.info(f"  Successful: {result.successful_moves}")
    logger.info(f"  Failed: {result.failed_moves}")
    logger.info(f"  Skipped: {result.skipped_moves}")
    
    # Show what would happen
    logger.info("")
    logger.info("Operations:")
    for op in result.operations:
        if op.success:
            logger.info(f"  ✓ {Path(op.source_path).name}")
            logger.info(f"    → {op.target_path}/{op.target_filename}")
        else:
            logger.warning(f"  ✗ {Path(op.source_path).name}")
            logger.warning(f"    Error: {op.error}")
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("Test complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
