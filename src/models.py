"""Data models for the AI File Organizer."""

from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class FileInfo:
    """Information about a single file with metadata."""
    
    file_name: str
    file_path: str
    mime_type: str
    file_size: int
    exif_data: Dict[str, Any] = field(default_factory=dict)
    binwalk_output: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert FileInfo to dictionary."""
        return asdict(self)


@dataclass
class ExcludedFile:
    """Information about an excluded file."""
    
    file_path: str
    file_name: str
    reason: str  # Why it was excluded
    rule: str    # Which rule caused exclusion (e.g., "hidden_file", "extension:.tmp", "size_limit")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ExcludedFile to dictionary."""
        return asdict(self)


@dataclass
class ErrorFile:
    """Information about a file that encountered an error."""
    
    file_path: str
    file_name: str
    error: str      # Error message
    stage: str      # Which stage encountered the error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ErrorFile to dictionary."""
        return asdict(self)


@dataclass
class ModelInfo:
    """Information about an available AI model."""
    
    name: str
    type: str
    provider: str
    model_name: str
    capabilities: List[str]
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ModelInfo to dictionary."""
        return asdict(self)


@dataclass
class Stage1Result:
    """Results from Stage 1: File enumeration and metadata collection."""
    
    source_directory: str
    total_files: int
    files: List[FileInfo]
    errors: List[Dict[str, str]]
    excluded_files: List[ExcludedFile] = field(default_factory=list)
    unique_mime_types: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Stage1Result to dictionary."""
        return {
            'source_directory': self.source_directory,
            'total_files': self.total_files,
            'files': [f.to_dict() for f in self.files],
            'errors': self.errors,
            'excluded_files': [e.to_dict() for e in self.excluded_files],
            'unique_mime_types': self.unique_mime_types
        }
    
    def add_file(self, file_info: FileInfo) -> None:
        """Add a file to the results."""
        self.files.append(file_info)
        self.total_files = len(self.files)
    
    def add_excluded_file(self, excluded_file: ExcludedFile) -> None:
        """Add an excluded file to the results."""
        self.excluded_files.append(excluded_file)
    
    def add_error(self, file_path: str, error_message: str) -> None:
        """Add an error to the results."""
        self.errors.append({
            'file_path': file_path,
            'error': error_message
        })
    
    def extract_unique_mime_types(self) -> None:
        """Extract unique MIME types from all files."""
        mime_types = set()
        for file_info in self.files:
            mime_types.add(file_info.mime_type)
        self.unique_mime_types = sorted(list(mime_types))


@dataclass
class Stage2Result:
    """Results from Stage 2: AI model discovery and mapping."""
    
    stage1_result: Stage1Result
    available_models: List[ModelInfo] = field(default_factory=list)
    mime_to_model_mapping: Dict[str, str] = field(default_factory=dict)
    model_connectivity: Dict[str, bool] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Stage2Result to dictionary."""
        return {
            'stage1_result': self.stage1_result.to_dict(),
            'available_models': [m.to_dict() for m in self.available_models],
            'mime_to_model_mapping': self.mime_to_model_mapping,
            'model_connectivity': self.model_connectivity
        }
    
    def set_models(self, models: List[Any]) -> None:
        """
        Set available models.
        
        Args:
            models: List of AIModel objects
        """
        self.available_models = [
            ModelInfo(
                name=m.name,
                type=m.type,
                provider=m.provider,
                model_name=m.model_name,
                capabilities=m.capabilities,
                description=m.description
            )
            for m in models
        ]
    
    def set_mime_mapping(self, mapping: Dict[str, str]) -> None:
        """
        Set the MIME type to model mapping.
        
        Args:
            mapping: Dictionary mapping MIME type to model name
        """
        self.mime_to_model_mapping = mapping
    
    def set_model_connectivity(self, connectivity: Dict[str, bool]) -> None:
        """
        Set the model connectivity status.
        
        Args:
            connectivity: Dictionary mapping model name to connectivity status
        """
        self.model_connectivity = connectivity
    
    def get_model_for_file(self, file_info: FileInfo) -> Optional[str]:
        """
        Get the recommended model for a file based on its MIME type.
        
        Args:
            file_info: FileInfo object
            
        Returns:
            Model name or None if no mapping exists
        """
        return self.mime_to_model_mapping.get(file_info.mime_type)

@dataclass
class FileAnalysis:
    """AI analysis results for a single file."""
    
    file_path: str
    assigned_model: str
    proposed_filename: str
    description: str
    tags: List[str]
    analysis_timestamp: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert FileAnalysis to dictionary."""
        return asdict(self)


@dataclass
class Stage3Result:
    """Results from Stage 3: AI-powered file analysis."""
    
    stage2_result: Stage2Result
    file_analyses: List[FileAnalysis] = field(default_factory=list)
    total_analyzed: int = 0
    total_errors: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Stage3Result to dictionary."""
        return {
            'stage2_result': self.stage2_result.to_dict(),
            'file_analyses': [a.to_dict() for a in self.file_analyses],
            'total_analyzed': self.total_analyzed,
            'total_errors': self.total_errors
        }
    
    def add_analysis(self, analysis: FileAnalysis) -> None:
        """Add a file analysis to the results."""
        self.file_analyses.append(analysis)
        if analysis.error:
            self.total_errors += 1
        else:
            self.total_analyzed += 1
    
    def get_analysis_for_file(self, file_path: str) -> Optional[FileAnalysis]:
        """
        Get the analysis for a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            FileAnalysis object or None if not found
        """
        for analysis in self.file_analyses:
            if analysis.file_path == file_path:
                return analysis
        return None
    
    def get_unified_file_data(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get unified data for a file combining all stages.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with stage1 metadata, stage2 mapping, and stage3 analysis
        """
        # Find file info from Stage 1
        file_info = None
        for f in self.stage2_result.stage1_result.files:
            if f.file_path == file_path:
                file_info = f
                break
        
        if not file_info:
            return None
        
        # Get Stage 2 mapping
        assigned_model = self.stage2_result.get_model_for_file(file_info)
        
        # Get Stage 3 analysis
        analysis = self.get_analysis_for_file(file_path)
        
        # Combine all data
        unified = {
            'file_info': file_info.to_dict(),
            'assigned_model': assigned_model,
            'analysis': analysis.to_dict() if analysis else None
        }
        
        return unified
    
    def get_all_unified_data(self) -> List[Dict[str, Any]]:
        """
        Get unified data for all files combining all stages.
        
        Returns:
            List of dictionaries, each containing complete file data from all stages
        """
        unified_data = []
        
        for file_info in self.stage2_result.stage1_result.files:
            data = self.get_unified_file_data(file_info.file_path)
            if data:
                unified_data.append(data)
        
        return unified_data


@dataclass
class TaxonomyNode:
    """Represents a node in the taxonomic directory structure."""
    
    path: str                           # Full path (e.g., "Photos/Nature/Wildlife")
    category: str                       # Node name (e.g., "Wildlife")
    description: str                    # What belongs here
    file_count: int = 0                 # Number of files assigned here
    subcategories: List[str] = field(default_factory=list)  # Child paths
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert TaxonomyNode to dictionary."""
        return asdict(self)


@dataclass
class FileAssignment:
    """Assignment of a file to a target location in the taxonomy."""
    
    file_path: str                      # Original file path
    target_path: str                    # Target directory path in taxonomy
    proposed_filename: str              # Filename from Stage 3
    reasoning: str                      # Why assigned to this location
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert FileAssignment to dictionary."""
        return asdict(self)


@dataclass
class Stage4Result:
    """Results from Stage 4: Taxonomic structure planning."""
    
    stage3_result: Stage3Result
    taxonomy: List[TaxonomyNode] = field(default_factory=list)
    file_assignments: List[FileAssignment] = field(default_factory=list)
    total_categories: int = 0
    total_assigned: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Stage4Result to dictionary."""
        return {
            'stage3_result': self.stage3_result.to_dict(),
            'taxonomy': [t.to_dict() for t in self.taxonomy],
            'file_assignments': [a.to_dict() for a in self.file_assignments],
            'total_categories': self.total_categories,
            'total_assigned': self.total_assigned
        }
    
    def add_taxonomy_node(self, node: TaxonomyNode) -> None:
        """Add a taxonomy node."""
        self.taxonomy.append(node)
        self.total_categories = len(self.taxonomy)
    
    def add_file_assignment(self, assignment: FileAssignment) -> None:
        """Add a file assignment."""
        self.file_assignments.append(assignment)
        self.total_assigned = len(self.file_assignments)
        
        # Update file count in taxonomy
        for node in self.taxonomy:
            if node.path == assignment.target_path:
                node.file_count += 1
                break
    
    def get_assignment_for_file(self, file_path: str) -> Optional[FileAssignment]:
        """Get the assignment for a specific file."""
        for assignment in self.file_assignments:
            if assignment.file_path == file_path:
                return assignment
        return None
    
    def get_taxonomy_tree(self) -> Dict[str, Any]:
        """Get hierarchical taxonomy tree structure."""
        tree = {}
        
        for node in self.taxonomy:
            parts = node.path.split('/')
            current = tree
            
            for i, part in enumerate(parts):
                if part not in current:
                    current[part] = {
                        '_info': {
                            'path': '/'.join(parts[:i+1]),
                            'description': node.description if i == len(parts)-1 else '',
                            'file_count': node.file_count if i == len(parts)-1 else 0
                        },
                        '_children': {}
                    }
                current = current[part]['_children']
        
        return tree
    
    def get_unified_file_data(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get complete unified data for a file including Stage 4 assignment.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with all stage data plus target_path
        """
        # Get Stage 3 unified data
        unified = self.stage3_result.get_unified_file_data(file_path)
        if not unified:
            return None
        
        # Add Stage 4 assignment
        assignment = self.get_assignment_for_file(file_path)
        if assignment:
            unified['assignment'] = assignment.to_dict()
        else:
            unified['assignment'] = None
        
        return unified
    
    def get_all_unified_data(self) -> List[Dict[str, Any]]:
        """
        Get complete unified data for all files including Stage 4 assignments.
        
        Returns:
            List of dictionaries with complete data from all stages
        """
        unified_data = []
        
        for file_info in self.stage3_result.stage2_result.stage1_result.files:
            data = self.get_unified_file_data(file_info.file_path)
            if data:
                unified_data.append(data)
        
        return unified_data


@dataclass
class MoveOperation:
    """Records a file move operation."""
    
    source_path: str
    target_path: str
    target_filename: str
    full_target: str  # Complete destination path
    category: str = "organized"  # organized, excluded, error
    success: bool = False
    error: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'source_path': self.source_path,
            'target_path': self.target_path,
            'target_filename': self.target_filename,
            'full_target': self.full_target,
            'category': self.category,
            'success': self.success,
            'error': self.error
        }


@dataclass
class Stage5Result:
    """Results from Stage 5: Physical file organization."""
    
    stage4_result: Stage4Result
    destination_root: str
    operations: List[MoveOperation] = field(default_factory=list)
    total_files: int = 0
    successful_moves: int = 0
    failed_moves: int = 0
    skipped_moves: int = 0
    excluded_moves: int = 0
    error_moves: int = 0
    dry_run: bool = False
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'destination_root': self.destination_root,
            'total_files': self.total_files,
            'successful_moves': self.successful_moves,
            'failed_moves': self.failed_moves,
            'skipped_moves': self.skipped_moves,
            'excluded_moves': self.excluded_moves,
            'error_moves': self.error_moves,
            'dry_run': self.dry_run,
            'operations': [op.to_dict() for op in self.operations]
        }
    
    def add_operation(self, operation: MoveOperation) -> None:
        """Add a move operation and update statistics."""
        self.operations.append(operation)
        self.total_files += 1
        
        if operation.success:
            if operation.category == "excluded":
                self.excluded_moves += 1
            elif operation.category == "error":
                self.error_moves += 1
            else:
                self.successful_moves += 1
        elif operation.error:
            self.failed_moves += 1
        else:
            self.skipped_moves += 1
