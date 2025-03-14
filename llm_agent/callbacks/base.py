"""
Base callback system for LLM Agent
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class ApprovalCallback(ABC):
    """Base class for handling user approvals"""

    @abstractmethod
    async def get_approval(self, tool_name: str, args: Dict[str, Any], description: Optional[str] = None) -> bool:
        """
        Get user approval for a tool execution

        Args:
            tool_name: Name of the tool to be executed
            args: Arguments to be passed to the tool
            description: Optional description of what the tool will do

        Returns:
            bool: True if approved, False if rejected
        """
        pass


class ConsoleApprovalCallback(ApprovalCallback):
    """Default console-based approval callback"""

    async def get_approval(self, tool_name: str, args: Dict[str, Any], description: Optional[str] = None) -> bool:
        """
        Get user approval via console input

        Args:
            tool_name: Name of the tool to be executed
            args: Arguments to be passed to the tool
            description: Optional description of what the tool will do

        Returns:
            bool: True if approved, False if rejected
        """
        print(f"\nTool Execution Request:")
        print(f"Tool: {tool_name}")
        print(f"Arguments: {args}")
        if description:
            print(f"Description: {description}")
        
        while True:
            response = input("\nDo you approve this tool execution? (y/n): ").lower()
            if response in ('y', 'yes'):
                return True
            if response in ('n', 'no'):
                return False
            print("Please enter 'y' or 'n'") 