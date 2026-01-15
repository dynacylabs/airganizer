"""Structure proposer for AI-powered file organization."""

import json
from typing import List, Optional, Callable
from pathlib import Path

from .client import AIClient, create_ai_client
from .prompts import (
    SYSTEM_PROMPT,
    create_initial_prompt,
    create_update_prompt,
    extract_json_from_response
)
from ..core.models import FileItem, ProposedStructure, DirectoryNode


class StructureProposer:
    """Proposes organizational structures using AI."""
    
    def __init__(self, ai_client: AIClient, chunk_size: int = 50,
                 temperature: float = 0.3, max_tokens: int = 4000):
        """
        Initialize the StructureProposer.
        
        Args:
            ai_client: AI client to use for proposals
            chunk_size: Number of files to process per AI call
            temperature: AI temperature (lower = more deterministic)
            max_tokens: Maximum tokens per AI response
        """
        self.ai_client = ai_client
        self.chunk_size = chunk_size
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.current_structure: Optional[ProposedStructure] = None
    
    def propose_structure(self, files: List[FileItem],
                         progress_callback: Optional[Callable[[int, int, str], None]] = None
                         ) -> ProposedStructure:
        """
        Propose an organizational structure for the given files.
        
        Args:
            files: List of files to organize
            progress_callback: Optional callback(chunk_num, total_chunks, message)
        
        Returns:
            ProposedStructure with AI-generated organization
        """
        if not files:
            raise ValueError("No files provided")
        
        # Split files into chunks
        chunks = self._chunk_files(files)
        total_chunks = len(chunks)
        
        if progress_callback:
            progress_callback(0, total_chunks, "Starting structure proposal...")
        
        # Process first chunk to create initial structure
        if progress_callback:
            progress_callback(1, total_chunks, f"Processing chunk 1/{total_chunks}...")
        
        self.current_structure = self._process_initial_chunk(chunks[0], 1, total_chunks)
        
        # Process remaining chunks to update structure
        for i, chunk in enumerate(chunks[1:], start=2):
            if progress_callback:
                progress_callback(i, total_chunks, f"Processing chunk {i}/{total_chunks}...")
            
            self.current_structure = self._process_update_chunk(
                chunk, self.current_structure, i, total_chunks
            )
        
        # Update final metadata
        self.current_structure.metadata['total_files_analyzed'] = len(files)
        self.current_structure.metadata['chunks_processed'] = total_chunks
        self.current_structure.processing_stats = {
            'chunk_size': self.chunk_size,
            'total_chunks': total_chunks,
            'temperature': self.temperature
        }
        
        if progress_callback:
            progress_callback(total_chunks, total_chunks, "Structure proposal complete!")
        
        return self.current_structure
    
    def _chunk_files(self, files: List[FileItem]) -> List[List[FileItem]]:
        """Split files into chunks for processing."""
        chunks = []
        for i in range(0, len(files), self.chunk_size):
            chunks.append(files[i:i + self.chunk_size])
        return chunks
    
    def _process_initial_chunk(self, files: List[FileItem], 
                               chunk_num: int, total_chunks: int) -> ProposedStructure:
        """Process the first chunk to create initial structure."""
        prompt = create_initial_prompt(files, chunk_num, total_chunks)
        
        response = self.ai_client.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        # Extract and parse JSON
        json_str = extract_json_from_response(response)
        
        try:
            structure = ProposedStructure.from_json(json_str)
            return structure
        except json.JSONDecodeError as e:
            # Create a fallback structure if AI response is invalid
            print(f"Warning: Failed to parse AI response: {e}")
            print(f"Response was: {json_str[:500]}...")
            return self._create_fallback_structure()
    
    def _process_update_chunk(self, files: List[FileItem],
                             current_structure: ProposedStructure,
                             chunk_num: int, total_chunks: int) -> ProposedStructure:
        """Process subsequent chunks to update structure."""
        prompt = create_update_prompt(files, current_structure, chunk_num, total_chunks)
        
        response = self.ai_client.generate(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        # Extract and parse JSON
        json_str = extract_json_from_response(response)
        
        try:
            structure = ProposedStructure.from_json(json_str)
            structure.update_timestamp()
            return structure
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse AI response: {e}")
            print(f"Keeping previous structure...")
            return current_structure
    
    def _create_fallback_structure(self) -> ProposedStructure:
        """Create a basic fallback structure if AI fails."""
        root = DirectoryNode(
            name="organized",
            description="Root directory for organized files",
            path="/organized",
            rationale="Fallback structure due to AI parsing error"
        )
        
        # Add some basic categories
        categories = [
            ("documents", "Document files (text, PDFs, etc.)"),
            ("media", "Images, videos, and audio files"),
            ("code", "Source code and scripts"),
            ("data", "Data files (JSON, CSV, databases)"),
            ("archives", "Compressed files and archives"),
            ("other", "Miscellaneous files")
        ]
        
        for name, desc in categories:
            root.add_subdirectory(DirectoryNode(
                name=name,
                description=desc,
                path=f"/organized/{name}"
            ))
        
        return ProposedStructure(root=root)
    
    def save_structure(self, output_path: str) -> None:
        """Save the current structure to a file."""
        if not self.current_structure:
            raise ValueError("No structure to save. Run propose_structure first.")
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(self.current_structure.to_json())
    
    @staticmethod
    def load_structure(input_path: str) -> ProposedStructure:
        """Load a structure from a file."""
        with open(input_path, 'r', encoding='utf-8') as f:
            json_str = f.read()
        return ProposedStructure.from_json(json_str)


def create_structure_proposer(provider: str = "openai", chunk_size: int = 50,
                              temperature: float = 0.3, **ai_kwargs) -> StructureProposer:
    """
    Factory function to create a StructureProposer.
    
    Args:
        provider: AI provider ('openai' or 'anthropic')
        chunk_size: Number of files per chunk
        temperature: AI temperature
        **ai_kwargs: Additional arguments for AI client
    
    Returns:
        StructureProposer instance
    """
    ai_client = create_ai_client(provider, **ai_kwargs)
    return StructureProposer(
        ai_client=ai_client,
        chunk_size=chunk_size,
        temperature=temperature
    )
