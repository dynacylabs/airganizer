"""Progress tracking with dual progress bars."""

import logging
from typing import Optional
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    MofNCompleteColumn
)
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text


logger = logging.getLogger(__name__)


class ProgressManager:
    """Manages dual progress bars for stage and overall progress."""
    
    def __init__(self, total_stages: int = 5, enabled: bool = True):
        """
        Initialize progress manager.
        
        Args:
            total_stages: Total number of stages in the pipeline
            enabled: Whether to display progress bars
        """
        self.total_stages = total_stages
        self.enabled = enabled
        self.console = Console()
        
        # Progress bar setup
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(complete_style="green", finished_style="bold green"),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            console=self.console,
            expand=False
        )
        
        # Task IDs
        self.stage_task_id = None
        self.overall_task_id = None
        self.live = None
        
        # Current state
        self.current_stage = 0
        self.current_file_info = ""
        
    def start(self):
        """Start the progress display."""
        if not self.enabled:
            return
        
        # Create tasks
        self.overall_task_id = self.progress.add_task(
            "[cyan]Overall Progress",
            total=self.total_stages
        )
        self.stage_task_id = self.progress.add_task(
            "[yellow]Stage Progress",
            total=100,
            visible=False
        )
        
        # Start live display
        self.live = Live(
            self._get_display(),
            console=self.console,
            refresh_per_second=4
        )
        self.live.start()
        
    def stop(self):
        """Stop the progress display."""
        if not self.enabled or not self.live:
            return
        
        self.live.stop()
        
    def _get_display(self):
        """Get the display with file info and progress bars."""
        # File info panel
        if self.current_file_info:
            info_text = Text(self.current_file_info, style="white")
            info_panel = Panel(
                info_text,
                title="[bold cyan]Current Operation",
                border_style="cyan",
                padding=(0, 1)
            )
        else:
            info_panel = Panel(
                Text("Initializing...", style="dim"),
                title="[bold cyan]Current Operation",
                border_style="dim",
                padding=(0, 1)
            )
        
        # Combine with progress bars
        from rich.console import Group
        display_group = Group(
            info_panel,
            Text(""),  # Spacing
            self.progress
        )
        
        return display_group
    
    def update_file_info(self, info: str):
        """
        Update the current file information display.
        
        Args:
            info: Information about current file/operation
        """
        if not self.enabled:
            return
        
        self.current_file_info = info
        if self.live:
            self.live.update(self._get_display())
    
    def start_stage(self, stage_num: int, stage_name: str, total_items: int):
        """
        Start a new stage.
        
        Args:
            stage_num: Stage number (1-5)
            stage_name: Name of the stage
            total_items: Total items to process in this stage
        """
        if not self.enabled:
            return
        
        self.current_stage = stage_num
        
        # Update stage task
        if self.stage_task_id is not None:
            self.progress.update(
                self.stage_task_id,
                description=f"[yellow]Stage {stage_num}: {stage_name}",
                completed=0,
                total=total_items,
                visible=True
            )
        
        # Update file info
        self.update_file_info(f"Starting Stage {stage_num}: {stage_name}")
        
    def update_stage_progress(self, completed: int, total: Optional[int] = None):
        """
        Update stage progress.
        
        Args:
            completed: Number of items completed
            total: Total items (if changed)
        """
        if not self.enabled or self.stage_task_id is None:
            return
        
        if total is not None:
            self.progress.update(self.stage_task_id, completed=completed, total=total)
        else:
            self.progress.update(self.stage_task_id, completed=completed)
    
    def complete_stage(self):
        """Mark current stage as complete."""
        if not self.enabled:
            return
        
        # Complete stage task
        if self.stage_task_id is not None:
            self.progress.update(self.stage_task_id, visible=False)
        
        # Update overall progress
        if self.overall_task_id is not None:
            self.progress.update(self.overall_task_id, advance=1)
    
    def set_stage_description(self, description: str):
        """
        Update the stage progress bar description.
        
        Args:
            description: New description
        """
        if not self.enabled or self.stage_task_id is None:
            return
        
        self.progress.update(self.stage_task_id, description=description)
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
