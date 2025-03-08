"""
OpenAI LLM provider implementation
"""
import json
from typing import List, Optional
import openai
from openai import AsyncClient

from .base import BaseLLMProvider, LLMAction
from ..state.task_state import TaskState

class OpenAIProvider(BaseLLMProvider):
    """OpenAI implementation of LLM provider"""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-pro-exp-02-05"):
        """
        Initialize OpenAI provider
        
        Args:
            api_key: OpenAI API key
            model: Model to use (defaults to GPT-4 Turbo)
        """
        self.client = AsyncClient(api_key=api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
        self.model = model

    async def get_next_action(
        self,
        task: str,
        state: TaskState,
        available_tools: List[str]
    ) -> LLMAction:
        """Get the next action from OpenAI"""
        
        # Format prompt with task and state context
        prompt = await self.format_prompt(task, state, available_tools)
        
        # Make API request
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt(available_tools)},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        # Parse response into action
        return await self.parse_response(response.choices[0].message.content)

    async def format_prompt(
        self,
        task: str,
        state: TaskState,
        available_tools: List[str]
    ) -> str:
        """Format the prompt for OpenAI"""
        
        # Build context from state
        context = []
        if state.tool_executions:
            context.append("Previous actions:")
            for execution in state.tool_executions[-5:]:  # Last 5 executions
                context.append(f"- Tool: {execution.tool_name}")
                context.append(f"  Args: {json.dumps(execution.args)}")
                context.append(f"  Result: {execution.result}")
                context.append("")
        
        # Format prompt
        prompt = f"""Task: {task}

Current Progress:
{chr(10).join(context) if context else "No actions taken yet"}

What should be done next? If the task is complete, set is_complete to true and provide a summary in the result field.
"""
        return prompt

    async def parse_response(self, response: str) -> LLMAction:
        """Parse OpenAI's response into an action"""
        try:
            # Try to parse as JSON first
            try:
                data = json.loads(response)
                return LLMAction(**data)
            except json.JSONDecodeError:
                pass
                
            # If not JSON, try to parse the response format:
            # Tool: tool_name
            # Args: {...}
            # Complete: true/false
            # Result: ...
            # Thoughts: ...
            lines = response.strip().split('\n')
            action = LLMAction()
            
            for line in lines:
                if not line.strip():
                    continue
                    
                key, value = [x.strip() for x in line.split(':', 1)]
                
                if key.lower() == 'tool':
                    action.tool_name = value
                elif key.lower() == 'args':
                    action.tool_args = json.loads(value)
                elif key.lower() == 'complete':
                    action.is_complete = value.lower() == 'true'
                elif key.lower() == 'result':
                    action.result = value
                elif key.lower() == 'thoughts':
                    action.thoughts = value
            
            return action
            
        except Exception as e:
            # If parsing fails, return completion action with error
            return LLMAction(
                is_complete=True,
                result=f"Failed to parse LLM response: {str(e)}",
                thoughts=f"Error parsing response: {response}"
            )

    def _get_system_prompt(self, available_tools: List[str]) -> str:
        """Get the system prompt that defines the agent's behavior"""
        return f"""You are an AI assistant that helps with Python development tasks. You operate by selecting appropriate tools from the following list:

Available tools: {', '.join(available_tools)}

For each step, you should respond in one of these formats:

1. To use a tool:
Tool: tool_name
Args: {{"arg1": "value1", "arg2": "value2"}}
Complete: false
Thoughts: Your reasoning for this action

2. To complete the task:
Complete: true
Result: Final result or summary
Thoughts: Your concluding thoughts

Keep responses focused and actionable. Explain your thinking in the Thoughts field."""
