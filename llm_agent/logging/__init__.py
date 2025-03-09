"""
Logging system for LLM Agent
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging
import logging.handlers
import os
from pathlib import Path

from pydantic import BaseModel

from llm_agent.tools.base import ToolResult

class LogConfig(BaseModel):
    """Configuration for logging system"""
    level: str = "INFO"
    file_path: Optional[Path] = None
    rotation_size_mb: int = 10
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    console_logging: bool = True
    file_logging: bool = True

class StructuredLogRecord:
    """Structured log record with additional context"""
    def __init__(self, 
                 level: int,
                 msg: str,
                 task_id: Optional[str] = None,
                 tool_name: Optional[str] = None,
                 context: Optional[Dict] = None):
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
            **self.context
        }
        for key, value in data_dict.items():
            if isinstance(value, ToolResult):
                data_dict[key] = value.model_dump()
        return data_dict

class JsonFormatter(logging.Formatter):
    """Format logs as JSON"""
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
                "message": record.getMessage()
            }
            
            # Add exception info if present
            if record.exc_info:
                data["exception"] = self.formatException(record.exc_info)
                
        return json.dumps(data)

class AgentLogger:
    """Logger for the LLM Agent with structured logging support"""
    
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
            console_handler.setFormatter(logging.Formatter(config.format))
            self.logger.addHandler(console_handler)
        
        # Add file handler if enabled
        if config.file_logging and config.file_path:
            # Create directory if needed
            os.makedirs(config.file_path.parent, exist_ok=True)
            
            # Set up rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                filename=str(config.file_path),
                maxBytes=config.rotation_size_mb * 1024 * 1024,
                backupCount=config.backup_count
            )
            file_handler.setFormatter(JsonFormatter())
            self.logger.addHandler(file_handler)
    
    def log(self, 
            level: int, 
            msg: str, 
            task_id: Optional[str] = None,
            tool_name: Optional[str] = None,
            context: Optional[Dict] = None) -> None:
        """
        Log a structured message
        
        Args:
            level: Log level (e.g. logging.INFO)
            msg: Log message
            task_id: Optional task identifier
            tool_name: Optional tool name
            context: Optional additional context
        """
        record = StructuredLogRecord(
            level=level,
            msg=msg,
            task_id=task_id,
            tool_name=tool_name,
            context=context
        )
        
        log_record = logging.LogRecord(
            name=self.name,
            level=level,
            pathname=__file__,
            lineno=0,
            msg=msg,
            args=(),
            exc_info=None
        )
        log_record.structured_data = record
        
        for handler in self.logger.handlers:
            handler.handle(log_record)
            
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
