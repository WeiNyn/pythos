"""
Base logger implementation
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import BaseModel


class LogConfig(BaseModel):
    """Logging configuration"""

    level: str = "INFO"
    file_path: Optional[str] = None
    console_logging: bool = True
    file_logging: bool = False
    use_colors: bool = True
    show_separators: bool = False
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class AgentLogger(ABC):
    """Base logger class for the agent"""

    def __init__(self, name: str, config: LogConfig):
        """Initialize the logger"""
        self.name = name
        self.config = config

    @abstractmethod
    def debug(self, message: str, **context: Any) -> None:
        """Log debug message"""
        pass

    @abstractmethod
    def info(self, message: str, **context: Any) -> None:
        """Log info message"""
        pass

    @abstractmethod
    def warning(self, message: str, **context: Any) -> None:
        """Log warning message"""
        pass

    @abstractmethod
    def error(self, message: str, **context: Any) -> None:
        """Log error message"""
        pass

    @abstractmethod
    def critical(self, message: str, **context: Any) -> None:
        """Log critical message"""
        pass

    @abstractmethod
    def start_task(self, message: str) -> None:
        """Start a new task with spinner"""
        pass

    @abstractmethod
    def end_task(self, message: str, success: bool = True) -> None:
        """End the current task"""
        pass

    @abstractmethod
    def show_table(self, title: str, data: Dict[str, Any]) -> None:
        """Show data in a formatted table"""
        pass

    @abstractmethod
    def show_panel(self, title: str, content: str, style: str = "white") -> None:
        """Show content in a panel"""
        pass

    @abstractmethod
    def show_progress(self, total: int, description: str = "Processing...") -> None:
        """Show a progress bar"""
        pass 