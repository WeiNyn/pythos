"""
OpenAI LLM provider implementation
"""
import json
from typing import Dict, List, Optional, Any

from .base import BaseLLMProvider, LLMAction
from ..state import TaskState

class OpenAIProvider(BaseLLMProvider):
    """OpenAI-based LLM provider implementation"""
    
    def __init__(self, api_key: str):
        """Initialize with API key"""
        self.api_key = api_key
        
    async def get_next_action(
        self,
        task: str,
        state: TaskState,
        available_tools: List[str]
    ) -> LLMAction:
        """Get next action from OpenAI"""
        prompt = await self.format_prompt(task, state, available_tools)
        
        # TODO: Implement actual OpenAI API call
        response = "No action taken"  # Placeholder
        
        return await self.parse_response(response if response else "")
        
    async def format_prompt(
        self,
        task: str,
        state: TaskState,
        available_tools: List[str]
    ) -> str:
        """Format prompt for OpenAI"""
        return f"""
        Task: {task}
        Available tools: {', '.join(available_tools)}
        Current state: {state.dict()}
        """
        
    async def parse_response(self, response: str) -> LLMAction:
        """Parse OpenAI's response into an action"""
        if not response:
            return LLMAction(thoughts="No response from OpenAI")
        
        try:
            # Attempt to parse JSON response
            data = json.loads(response)
            return LLMAction(**data)
        except Exception:
            # Fallback to basic text response
            return LLMAction(
                thoughts=response,
                is_complete=False
            )
