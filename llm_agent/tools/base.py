"""
Base tool implementation
"""

import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel


class ToolResult(BaseModel):
    """Result from tool execution"""

    success: bool
    message: str
    data: Any = None


class BaseTool(ABC):
    """Base class for all tools"""

    def __init__(self) -> None:
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
                data={"error": str(e)},
            )
        finally:
            self.last_execution_duration = time.time() - start_time

        return result

    def get_example(self) -> str:
        """
        Get example usage for this tool in XML format.
        Should be overridden by subclasses to provide a custom example.

        Returns:
            Example usage formatted as XML
        """
        return f"""
<{self.name}>
<args>
    <param>value</param>
</args>
</{self.name}>"""

    def get_parameters_description(self) -> List[Tuple[str, str]]:
        """
        Get a list of parameter descriptions for this tool.
        Should be overridden by subclasses to provide parameter documentation.

        Returns:
            List of (parameter_name, description) tuples
        """
        return [
            (
                "param",
                "Generic parameter (override this method to provide specific descriptions)",
            )
        ]

    def get_response_format(self) -> str:
        """
        Get expected response format for the tool.
        Can be overridden by subclasses that need custom response handling.

        Returns:
            Expected response format as a string
        """
        return """<response>
<thoughts>Explanation of what you're trying to do with this tool</thoughts>
<tool>{tool_name}</tool>
<args>
    {parameters}
</args>
<is_complete>false</is_complete>
</response>"""
