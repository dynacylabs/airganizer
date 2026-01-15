"""Prompt templates for AI-powered file organization."""

from typing import List, Optional
from ..core.models import FileItem, ProposedStructure


SYSTEM_PROMPT = """You are an expert file organization assistant. Your task is to analyze files and propose a logical, hierarchical directory structure for organizing them.

Guidelines:
1. Create intuitive category-based directories
2. Consider file types, purposes, and relationships
3. Keep the structure balanced (not too deep, not too flat)
4. Use clear, descriptive directory names
5. Provide rationale for organizational decisions
6. Update the structure iteratively as you see more files

CRITICAL: You must respond with ONLY valid JSON. No explanatory text before or after. No markdown code blocks. Just pure JSON starting with { and ending with }."""


def create_initial_prompt(files: List[FileItem], chunk_number: int = 1, 
                          total_chunks: int = 1) -> str:
    """
    Create initial prompt for AI to propose structure.
    
    Args:
        files: List of files to organize
        chunk_number: Current chunk number
        total_chunks: Total number of chunks
    
    Returns:
        Formatted prompt string
    """
    file_list = "\n".join([f"- {f.to_simple_string()}" for f in files[:50]])  # Limit to first 50 for brevity
    if len(files) > 50:
        file_list += f"\n... and {len(files) - 50} more files"
    
    prompt = f"""Analyze these files and create an organizational directory structure.

Files (chunk {chunk_number}/{total_chunks}):
{file_list}

You MUST respond with EXACTLY this JSON structure format:

{{
  "root": {{
    "name": "organized",
    "description": "Root directory for all organized files",
    "path": "/organized",
    "subdirectories": [
      {{
        "name": "Documents",
        "description": "Text documents and PDFs",
        "path": "/organized/Documents",
        "subdirectories": [],
        "files": [],
        "rationale": "Group all document-type files together"
      }},
      {{
        "name": "Media",
        "description": "Images, videos, and audio files",
        "path": "/organized/Media",
        "subdirectories": [
          {{
            "name": "Images",
            "description": "All image files",
            "path": "/organized/Media/Images",
            "subdirectories": [],
            "files": [],
            "rationale": "Separate images from other media"
          }}
        ],
        "files": [],
        "rationale": "Central location for all media files"
      }}
    ],
    "files": [],
    "rationale": "Organize by file type and purpose"
  }}
}}

CRITICAL REQUIREMENTS:
- Every directory object MUST have: name, description, path, subdirectories (array), files (array), rationale
- Keep files arrays empty for now
- Create categories based on the file types you see (images, PDFs, videos, documents, etc.)
- Use simple, clear category names
- Return ONLY the JSON above, nothing else"""

    return prompt


def create_update_prompt(files: List[FileItem], current_structure: ProposedStructure,
                        chunk_number: int, total_chunks: int) -> str:
    """
    Create prompt for updating existing structure.
    
    Args:
        files: New batch of files to analyze
        current_structure: Current proposed structure
        chunk_number: Current chunk number
        total_chunks: Total number of chunks
    
    Returns:
        Formatted prompt string
    """
    file_list = "\n".join([f"- {f.to_simple_string()}" for f in files])
    current_json = current_structure.to_json(indent=2)
    
    prompt = f"""You are continuing to build an organizational structure for files. Here is the current structure you've proposed, followed by a new batch of files to analyze.

Chunk {chunk_number} of {total_chunks}

CURRENT STRUCTURE:
{current_json}

NEW FILES TO ANALYZE:
{file_list}

Please review the new files and update the structure as needed:

1. Add new categories if the new files don't fit existing ones
2. Refine existing categories if needed
3. Reorganize if you see better patterns emerging
4. Keep the structure balanced and logical
5. Update rationales as you refine your thinking

Respond with the COMPLETE UPDATED JSON structure in the same format as before. Include:
- All existing directories (modified or not)
- Any new directories needed for the new files
- Updated rationales where appropriate
- Keep "files" arrays empty (we're just building the structure)

Respond with ONLY the JSON structure, no additional text."""

    return prompt


def create_summary_prompt(structure: ProposedStructure, total_files: int) -> str:
    """
    Create prompt for generating a summary of the proposed structure.
    
    Args:
        structure: Final proposed structure
        total_files: Total number of files analyzed
    
    Returns:
        Formatted prompt string
    """
    structure_json = structure.to_json(indent=2)
    
    prompt = f"""You have completed analyzing {total_files} files and proposed this organizational structure:

{structure_json}

Please provide a brief summary (2-3 paragraphs) explaining:
1. The overall organizational strategy
2. The main categories and their purposes
3. How this structure will help organize the files effectively

Respond in plain text (not JSON)."""

    return prompt


def extract_json_from_response(response: str) -> str:
    """
    Extract JSON from AI response, handling cases where it might include extra text.
    
    Args:
        response: Raw AI response
    
    Returns:
        Cleaned JSON string
    """
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
    
    # Return as-is if no markers found
    return response.strip()
