"""
Base tool implementation
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
from datetime import datetime
from pydantic import BaseModel

class ToolResult(BaseModel):
    """Result from tool execution"""
    success: bool
    message: str
    data: Any = None

class BaseTool(ABC):
    """Base class for all tools"""
    
    def __init__(self):
        """Initialize tool"""
        self.name = self.__class__.__name__
        self.description = self.__doc__ or "No description available"
        self.last_execution_time: Optional[float] = None
        self.last_execution_duration: Optional[float] = None

    @abstractmethod
    async def _execute(self, args: Dict[str, Any]) -> ToolResult:
        """Internal execute method to be implemented by subclasses"""
        pass

    async def execute(self, args: Dict[str, Any]) -> ToolResult:
        """
        Execute the tool with timing and result tracking
        
        Args:
            args: Tool arguments
            
        Returns:
            ToolResult containing execution outcome
        """
        start_time = time.time()
        self.last_execution_time = datetime.utcnow().timestamp()

        try:
            result = await self._execute(args)
        except Exception as e:
            result = ToolResult(
                success=False,
                message=f"Tool execution failed: {str(e)}",
                data={"error": str(e)}
            )
        finally:
            self.last_execution_duration = time.time() - start_time

        return result
