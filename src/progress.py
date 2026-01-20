"""Progress tracking with dual progress bars."""

import logging
from typing import Optional, List
from collections import deque
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    MofNCompleteColumn
)
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.logging import RichHandler


logger = logging.getLogger(__name__)


class ProgressManager:
    """Manages dual progress bars for stage and overall progress."""
    
    def __init__(self, total_stages: int = 5, enabled: bool = True, max_log_lines: int = 10):
        """
        Initialize progress manager.
        
        Args:
            total_stages: Total number of stages in the pipeline
            enabled: Whether to display progress bars
            max_log_lines: Maximum number of recent log lines to display (default: 10)
        """
        self.total_stages = total_stages
        self.enabled = enabled
        self.max_log_lines = max_log_lines
        self.console = Console()
        
        # Recent logs buffer (circular buffer)
        self.recent_logs: deque = deque(maxlen=max_log_lines)
        
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
        """Get the display with file info, logs, and progress bars."""
        components = []
        
        # Recent logs panel
        if self.recent_logs:
            log_text = Text()
            for log_line in list(self.recent_logs):
                log_text.append(log_line)
                log_text.append("\n")
            
            log_panel = Panel(
                log_text,
                title="[bold yellow]Recent Activity",
                border_style="yellow",
                padding=(0, 1),
                height=self.max_log_lines + 2
            )
            components.append(log_panel)
            components.append(Text(""))  # Spacing
        
        # File info panel (optional, can be disabled if logs show enough)
        # components.append(Text(""))  # Spacing
        
        # Progress bars
        components.append(self.progress)
        
        return Group(*components)
    
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
    
    def add_log(self, message: str, style: str = "white"):
        """
        Add a log message to the display.
        
        Args:
            message: Log message
            style: Rich style for the message
        """
        if not self.enabled:
            return
        
        self.recent_logs.append(Text(message, style=style))
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


class ProgressLoggingHandler(logging.Handler):
    """Custom logging handler that routes logs to ProgressManager."""
    
    def __init__(self, progress_manager: ProgressManager):
        """
        Initialize the handler.
        
        Args:
            progress_manager: ProgressManager instance to send logs to
        """
        super().__init__()
        self.progress_manager = progress_manager
        self.level_styles = {
            logging.DEBUG: "dim",
            logging.INFO: "white",
            logging.WARNING: "yellow",
            logging.ERROR: "red",
            logging.CRITICAL: "bold red"
        }
    
    def emit(self, record: logging.LogRecord):
        """Emit a log record to the progress manager."""
        try:
            msg = self.format(record)
            style = self.level_styles.get(record.levelno, "white")
            self.progress_manager.add_log(msg, style)
        except Exception:
            self.handleError(record)
