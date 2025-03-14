"""
Typer-based logger implementation for enhanced CLI experience
"""

import time
from datetime import datetime
from typing import Any, Dict, Optional

import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from .base import AgentLogger, LogConfig


class TyperLogger(AgentLogger):
    """Typer-based logger with rich formatting and spinners"""

    def __init__(self, name: str, config: LogConfig):
        """Initialize the Typer logger"""
        super().__init__(name, config)
        self.console = Console()
        self._current_spinner: Optional[Progress] = None
        self._spinner_task_id: Optional[int] = None
        self._spinner_text: Optional[str] = None

    def _format_message(self, message: str, level: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Format message with rich text"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level_color = {
            "DEBUG": "dim",
            "INFO": "blue",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red bold",
        }.get(level, "white")

        text = Text()
        text.append(f"[{timestamp}] ", style="dim")
        text.append(f"[{level}] ", style=level_color)
        text.append(message)

        if context:
            text.append("\nContext:", style="dim")
            for key, value in context.items():
                text.append(f"\n  {key}: {value}", style="dim")

        return text

    def _create_spinner(self, message: str) -> Progress:
        """Create a new spinner progress bar"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        )

    def _start_spinner(self, message: str) -> None:
        """Start a new spinner"""
        if self._current_spinner:
            self._stop_spinner()

        self._current_spinner = self._create_spinner(message)
        self._spinner_text = message
        self._spinner_task_id = self._current_spinner.add_task(message, total=None)
        self._current_spinner.start()

    def _stop_spinner(self) -> None:
        """Stop the current spinner"""
        if self._current_spinner:
            self._current_spinner.stop()
            self._current_spinner = None
            self._spinner_task_id = None
            self._spinner_text = None

    def debug(self, message: str, **context: Any) -> None:
        """Log debug message"""
        if self.config.level == "DEBUG":
            self._stop_spinner()
            self.console.print(self._format_message(message, "DEBUG", context))

    def info(self, message: str, **context: Any) -> None:
        """Log info message"""
        self._stop_spinner()
        self.console.print(self._format_message(message, "INFO", context))

    def warning(self, message: str, **context: Any) -> None:
        """Log warning message"""
        self._stop_spinner()
        self.console.print(self._format_message(message, "WARNING", context))

    def error(self, message: str, **context: Any) -> None:
        """Log error message"""
        self._stop_spinner()
        self.console.print(self._format_message(message, "ERROR", context))

    def critical(self, message: str, **context: Any) -> None:
        """Log critical message"""
        self._stop_spinner()
        self.console.print(self._format_message(message, "CRITICAL", context))

    def start_task(self, message: str) -> None:
        """Start a new task with spinner"""
        self._start_spinner(message)

    def end_task(self, message: str, success: bool = True) -> None:
        """End the current task"""
        if self._current_spinner:
            self._stop_spinner()
            status = "✓" if success else "✗"
            color = "green" if success else "red"
            self.console.print(f"{status} {message}", style=color)

    def show_table(self, title: str, data: Dict[str, Any]) -> None:
        """Show data in a formatted table"""
        table = Table(title=title, show_header=True, header_style="bold magenta")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")

        for key, value in data.items():
            table.add_row(str(key), str(value))

        self.console.print(table)

    def show_panel(self, title: str, content: str, style: str = "white") -> None:
        """Show content in a panel"""
        panel = Panel(content, title=title, style=style)
        self.console.print(panel)

    def show_progress(self, total: int, description: str = "Processing...") -> None:
        """Show a progress bar"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task(description, total=total)
            for i in range(total):
                progress.update(task, advance=1)
                time.sleep(0.1)  # Simulate work 