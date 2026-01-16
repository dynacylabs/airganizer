"""
Plan management for Airganizer
Tracks all file operations to be executed
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class FileOperation:
    """Represents a single file operation"""
    
    def __init__(self, operation_type: str, source_path: str, 
                 destination_path: str = None, reason: str = None, 
                 metadata: Dict[str, Any] = None):
        """
        Initialize a file operation
        
        Args:
            operation_type: Type of operation (move, copy, delete, error)
            source_path: Original file path
            destination_path: Target file path (if applicable)
            reason: Reason for the operation
            metadata: Additional metadata
        """
        self.operation_type = operation_type
        self.source_path = source_path
        self.destination_path = destination_path
        self.reason = reason
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'operation_type': self.operation_type,
            'source_path': self.source_path,
            'destination_path': self.destination_path,
            'reason': self.reason,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileOperation':
        """Create from dictionary"""
        op = cls(
            operation_type=data['operation_type'],
            source_path=data['source_path'],
            destination_path=data.get('destination_path'),
            reason=data.get('reason'),
            metadata=data.get('metadata', {})
        )
        op.timestamp = data.get('timestamp', datetime.now().isoformat())
        return op


class AirganizerPlan:
    """Manages the overall plan for file operations"""
    
    def __init__(self):
        """Initialize an empty plan"""
        self.operations: List[FileOperation] = []
        self.metadata = {
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'stages_completed': []
        }
    
    def add_operation(self, operation: FileOperation):
        """Add an operation to the plan"""
        self.operations.append(operation)
        self.metadata['updated_at'] = datetime.now().isoformat()
    
    def add_error_file(self, source_path: str, destination_path: str, 
                      error_message: str, file_metadata: Dict[str, Any] = None):
        """
        Add an error file operation to the plan
        
        Args:
            source_path: Original file path
            destination_path: Error files directory path
            error_message: The error that occurred
            file_metadata: Additional file metadata
        """
        operation = FileOperation(
            operation_type='error',
            source_path=source_path,
            destination_path=destination_path,
            reason=f"Processing error: {error_message}",
            metadata=file_metadata or {}
        )
        self.add_operation(operation)
    
    def add_move_operation(self, source_path: str, destination_path: str, 
                          reason: str = None, file_metadata: Dict[str, Any] = None):
        """
        Add a move operation to the plan
        
        Args:
            source_path: Original file path
            destination_path: Target path
            reason: Reason for the move
            file_metadata: Additional file metadata
        """
        operation = FileOperation(
            operation_type='move',
            source_path=source_path,
            destination_path=destination_path,
            reason=reason,
            metadata=file_metadata or {}
        )
        self.add_operation(operation)
    
    def mark_stage_complete(self, stage_name: str):
        """Mark a stage as completed"""
        if stage_name not in self.metadata['stages_completed']:
            self.metadata['stages_completed'].append(stage_name)
        self.metadata['updated_at'] = datetime.now().isoformat()
    
    def get_operations_by_type(self, operation_type: str) -> List[FileOperation]:
        """Get all operations of a specific type"""
        return [op for op in self.operations if op.operation_type == operation_type]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the plan"""
        summary = {
            'total_operations': len(self.operations),
            'by_type': {}
        }
        
        for op in self.operations:
            op_type = op.operation_type
            summary['by_type'][op_type] = summary['by_type'].get(op_type, 0) + 1
        
        return summary
    
    def get_error_operations_summary(self) -> List[Dict[str, str]]:
        """Get a list of error operations with key details"""
        error_ops = self.get_operations_by_type('error')
        return [
            {
                'source': op.source_path,
                'destination': op.destination_path,
                'reason': op.reason
            }
            for op in error_ops
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert plan to dictionary"""
        return {
            'metadata': self.metadata,
            'summary': self.get_summary(),
            'operations': [op.to_dict() for op in self.operations]
        }
    
    def to_json(self) -> str:
        """Convert plan to JSON string"""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    def save(self, file_path: Path):
        """
        Save plan to file
        
        Args:
            file_path: Path to save the plan
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
    
    @classmethod
    def load(cls, file_path: Path) -> Optional['AirganizerPlan']:
        """
        Load plan from file
        
        Args:
            file_path: Path to load the plan from
        
        Returns:
            AirganizerPlan instance or None if file doesn't exist
        """
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            plan = cls()
            plan.metadata = data.get('metadata', {})
            
            for op_data in data.get('operations', []):
                plan.operations.append(FileOperation.from_dict(op_data))
            
            return plan
        
        except Exception as e:
            print(f"Warning: Could not load plan from {file_path}: {e}")
            return None
    
    @classmethod
    def load_or_create(cls, file_path: Path) -> 'AirganizerPlan':
        """
        Load existing plan or create new one
        
        Args:
            file_path: Path to the plan file
        
        Returns:
            AirganizerPlan instance
        """
        plan = cls.load(file_path)
        if plan is None:
            plan = cls()
        return plan
