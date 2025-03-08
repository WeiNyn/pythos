"""
Tool system for LLM Agent
"""
from typing import List
from .base import BaseTool
from .file_operations import (
    ReadFileTool,
    WriteFileTool,
    SearchFilesTool,
    ListFilesTool
)
from ..config import AgentConfig

def get_default_tools(config: AgentConfig) -> List[BaseTool]:
    """
    Get the default set of tools
    
    Args:
        config: Agent configuration
        
    Returns:
        List of initialized tool instances
    """
    return [
        ReadFileTool(),
        WriteFileTool(),
        SearchFilesTool(),
        ListFilesTool()
    ]

__all__ = [
    "BaseTool",
    "get_default_tools",
    "ReadFileTool",
    "WriteFileTool",
    "SearchFilesTool",
    "ListFilesTool"
]
