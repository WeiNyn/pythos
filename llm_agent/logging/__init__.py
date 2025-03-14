"""
Logging system for LLM Agent
"""

import json
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import termcolor
from pydantic import BaseModel

from llm_agent.tools.base import ToolResult

# Constants for visual formatting
SECTION_SEPARATOR = "=" * 80
SUBSECTION_SEPARATOR = "-" * 60
INDENT = "  "


class LogConfig(BaseModel):
    """Configuration for logging system"""

    level: str = "DEBUG"
    file_path: Optional[Path] = None
    rotation_size_mb: int = 10
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s\n%(message)s"
    console_logging: bool = True
    file_logging: bool = True
    use_colors: bool = True
    show_separators: bool = True


class DebugConfig(BaseModel):
    """Debug-specific logging configuration"""

    enable_tool_logging: bool = True
    enable_rate_limiter_logging: bool = True
    enable_memory_logging: bool = True
    enable_separators: bool = True
    log_level: str = "DEBUG"


class StructuredLogRecord:
    """Structured log record with additional context"""

    def __init__(
        self,
        level: int,
        msg: str,
        task_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        context: Optional[Dict] = None,
    ):
        self.level = level
        self.msg = msg
        self.task_id = task_id
        self.tool_name = tool_name
        self.context = context or {}
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict:
        """Convert record to dictionary"""
        data_dict = {
            "timestamp": self.timestamp.isoformat(),
            "level": logging.getLevelName(self.level),
            "message": self.msg,
            "task_id": self.task_id,
            "tool_name": self.tool_name,
            **self.context,
        }
        for key, value in data_dict.items():
            if isinstance(value, ToolResult):
                data_dict[key] = value.model_dump()
        return data_dict


class DebugFormatter(logging.Formatter):
    """Enhanced formatter with visual separators and colors"""

    COLORS = {
        "DEBUG": "grey",
        "INFO": "white",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red",
    }

    def __init__(self, fmt: str, use_colors: bool = True, show_separators: bool = True):
        super().__init__(fmt)
        self.use_colors = use_colors
        self.show_separators = show_separators

    def format(self, record: logging.LogRecord) -> str:
        """Format the record with visual enhancements"""
        # Get basic formatted message
        formatted = super().format(record)

        # Add colors if enabled
        if self.use_colors:
            color = self.COLORS.get(record.levelname, "white")
            formatted = termcolor.colored(formatted, color)

        # Add structured data with indentation if available
        if hasattr(record, "structured_data"):
            data = record.structured_data.to_dict()
            if "context" in data and data["context"]:
                formatted += f"\n{INDENT}Context:"
                for key, value in data["context"].items():
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value, indent=2)
                        lines = value.split("\n")
                        value = "\n".join(f"{INDENT}{INDENT}{line}" for line in lines)
                    formatted += f"\n{INDENT}{INDENT}{key}: {value}"

        # Add visual separators if enabled
        if self.show_separators:
            formatted = f"\n{SECTION_SEPARATOR}\n{formatted}\n{SECTION_SEPARATOR}\n"

        return formatted


class JsonFormatter(logging.Formatter):
    """Format logs as JSON with proper indentation"""

    def format(self, record: logging.LogRecord) -> str:
        """Format the record as JSON"""
        # Extract structured data if available
        if hasattr(record, "structured_data"):
            data = record.structured_data.to_dict()
        else:
            data = {
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }

            # Add exception info if present
            if record.exc_info:
                data["exception"] = self.formatException(record.exc_info)

        return json.dumps(data, indent=2)


class AgentLogger:
    """Logger for the LLM Agent with enhanced debug support"""

    def __init__(self, name: str, config: LogConfig):
        """Initialize the logger with given configuration"""
        self.name = name
        self.config = config
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, config.level.upper()))

        # Remove any existing handlers
        self.logger.handlers.clear()

        # Add console handler if enabled
        if config.console_logging:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(
                DebugFormatter(
                    config.format,
                    use_colors=config.use_colors,
                    show_separators=config.show_separators,
                )
            )
            self.logger.addHandler(console_handler)

        # Add file handler if enabled
        if config.file_logging and config.file_path:
            # Create directory if needed
            os.makedirs(config.file_path.parent, exist_ok=True)

            # Set up rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                filename=str(config.file_path),
                maxBytes=config.rotation_size_mb * 1024 * 1024,
                backupCount=config.backup_count,
            )
            file_handler.setFormatter(JsonFormatter())
            self.logger.addHandler(file_handler)

    def log(
        self,
        level: int,
        msg: str,
        task_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        context: Optional[Dict] = None,
    ) -> None:
        """
        Log a structured message with visual enhancements

        Args:
            level: Log level (e.g. logging.INFO)
            msg: Log message
            task_id: Optional task identifier
            tool_name: Optional tool name
            context: Optional additional context
        """
        record = StructuredLogRecord(level=level, msg=msg, task_id=task_id, tool_name=tool_name, context=context)

        log_record = logging.LogRecord(
            name=self.name,
            level=level,
            pathname=__file__,
            lineno=0,
            msg=msg,
            args=(),
            exc_info=None,
        )
        log_record.structured_data = record

        for handler in self.logger.handlers:
            handler.handle(log_record)

    def format_section(self, title: str, content: str) -> str:
        """Format a section with separators and title"""
        if self.config.show_separators:
            return f"\n{SUBSECTION_SEPARATOR}\n{title}\n{content}\n{SUBSECTION_SEPARATOR}\n"
        return f"\n{title}\n{content}"

    def debug(self, msg: str, **kwargs) -> None:
        """Log debug message"""
        self.log(logging.DEBUG, msg, **kwargs)

    def info(self, msg: str, **kwargs) -> None:
        """Log info message"""
        self.log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs) -> None:
        """Log warning message"""
        self.log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs) -> None:
        """Log error message"""
        self.log(logging.ERROR, msg, **kwargs)

    def critical(self, msg: str, **kwargs) -> None:
        """Log critical message"""
        self.log(logging.CRITICAL, msg, **kwargs)
