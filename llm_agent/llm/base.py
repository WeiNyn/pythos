"""
Base LLM provider interface
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from pydantic import BaseModel

from ..state.task_state import TaskState

class LLMAction(BaseModel):
    """Represents an action to be taken by the agent"""
    tool_name: Optional[str] = None
    tool_args: dict = {}
    is_complete: bool = False
    result: Optional[str] = None
    thoughts: Optional[str] = None

class BaseLLMProvider(ABC):
    """Base class for LLM providers"""
    
    @abstractmethod
    async def get_next_action(
        self,
        task: str,
        state: TaskState,
        available_tools: List[str]
    ) -> LLMAction:
        """
        Get the next action to take based on the current task and state
        
        Args:
            task: The current task description
            state: Current task state
            available_tools: List of available tool names
            
        Returns:
            LLMAction containing the next action to take
        """
        pass

    @abstractmethod
    async def format_prompt(
        self,
        task: str,
        state: TaskState,
        available_tools: List[str]
    ) -> str:
        """
        Format the prompt for the LLM
        
        Args:
            task: The current task description
            state: Current task state
            available_tools: List of available tool names
            
        Returns:
            Formatted prompt string
        """
        pass

    @abstractmethod
    async def parse_response(self, response: str) -> LLMAction:
        """
        Parse the LLM's response into an action
        
        Args:
            response: Raw response from the LLM
            
        Returns:
            Parsed LLMAction
        """
        pass
