"""
Base class and types for tools
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel

class ToolArguments(BaseModel):
    """Base class for tool arguments"""
    pass

class ToolResult(BaseModel):
    """Base class for tool results"""
    success: bool
    message: str
    data: Optional[Any] = None

class BaseTool(ABC):
    """Base class for all tools"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, args: Dict[str, Any]) -> ToolResult:
        """
        Execute the tool with the given arguments
        
        Args:
            args: Dictionary of arguments for the tool
            
        Returns:
            ToolResult containing the execution result
        """
        pass

    def requires_approval(self, args: Dict[str, Any]) -> bool:
        """
        Check if this tool execution requires user approval
        
        Args:
            args: Tool arguments to check
            
        Returns:
            True if approval is required, False otherwise
        """
        return True  # Default to requiring approval

    def validate_args(self, args: Dict[str, Any]) -> None:
        """
        Validate the provided arguments
        
        Args:
            args: Arguments to validate
            
        Raises:
            ValueError: If arguments are invalid
        """
        pass
