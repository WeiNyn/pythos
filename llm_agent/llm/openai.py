"""
OpenAI LLM provider implementation
"""

import json
from datetime import datetime
import openai
import re
from typing import Dict, List, Optional, Any, Tuple
from .base import BaseLLMProvider, LLMAction
from ..state import TaskState
from ..tools.base import BaseTool
from pydantic import BaseModel
from .rate_limiter import RateLimiter

class OpenAIProvider(BaseLLMProvider):
    """OpenAI-based LLM provider implementation"""

    def __init__(self, api_key: str, rpm: int = 60):
        """Initialize with API key and rate limit"""
        self.api_key = api_key
        openai.base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        openai.api_key = self.api_key
        self.tools: Dict[str, BaseTool] = {}
        self.rate_limiter = RateLimiter(rpm)

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool with the provider"""
        self.tools[tool.name] = tool

    def _get_tool_params_doc(self, tool: BaseTool) -> str:
        """Generate parameter documentation for a tool"""
        if tool.name == "read_file":
            return "- path: string (required) - Path to the file to read"
        elif tool.name == "write_file":
            return """- path: string (required) - Path to write the file to
- content: string (required) - Content to write to the file
- create_dirs: boolean (optional) - Create parent directories if needed (default: true)"""
        elif tool.name == "search_files":
            return """- directory: string (required) - Directory to search in
- pattern: string (required) - Pattern to match filenames against
- recursive: boolean (optional) - Search subdirectories (default: true)"""
        elif tool.name == "list_files":
            return """- directory: string (required) - Directory to list files from
- recursive: boolean (optional) - List files in subdirectories (default: false)"""
        return "No parameters documented"

    def _get_tool_example(self, tool: BaseTool) -> str:
        """Generate usage example for a tool"""
        if tool.name == "read_file":
            return """Input: {"path": "src/config.json"}
Output: {
    "success": true,
    "message": "File read successfully",
    "data": "{\\"name\\": \\"project\\"}"
}"""
        elif tool.name == "write_file":
            return """Input: {
    "path": "src/script.py",
    "content": "print('Hello')",
    "create_dirs": true
}
Output: {
    "success": true,
    "message": "Content written to src/script.py",
    "data": null
}"""
        elif tool.name == "search_files":
            return """Input: {
    "directory": "src",
    "pattern": "*.py",
    "recursive": true
}
Output: {
    "success": true,
    "message": "Found 3 matches",
    "data": ["src/main.py", "src/utils.py"]
}"""
        elif tool.name == "list_files":
            return """Input: {
    "directory": "src",
    "recursive": false
}
Output: {
    "success": true,
    "message": "Listed 5 files",
    "data": ["src/main.py", "src/config.json"]
}"""
        return "No example available"

    def _format_tool_history(self, state: TaskState) -> str:
        """Format the tool execution history"""
        if not state.tool_executions:
            return "No previous tool executions"
            
        history = []
        for te in state.tool_executions:
            history.append(f"""
Execution at {te.timestamp.strftime('%H:%M:%S')}:
Tool: {te.tool_name}
Arguments: {json.dumps(te.args, indent=2)}
Result: {json.dumps(te.result.dict() if isinstance(te.result, BaseModel) else te.result, indent=2)}
""")
        return "\n".join(history)

    async def get_next_action(
        self, task: str, state: TaskState, available_tools: List[str]
    ) -> LLMAction:
        """Get next action from OpenAI"""
        prompt = await self.format_prompt(task, state, available_tools)
        
        try:
            # Wait for rate limit slot
            await self.rate_limiter.acquire()
            
            api_response = openai.chat.completions.create(
                model="gemini-2.0-flash-thinking-exp-01-21",  # Or your preferred model
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            
            # Log rate limit metrics in debug
            if hasattr(self, 'logger'):
                self.logger.debug(
                    "Rate limit metrics",
                    extra={
                        "current_rpm": self.rate_limiter.get_current_rpm(),
                        "wait_time": self.rate_limiter.get_wait_time()
                    }
                )
            print("="*20 + "<Prompt>" + "="*20)
            print(prompt)
            print("="*20 + "<Response>" + "="*20)
            print(api_response.choices[0].message.content)
            print("="*50)
            action = await self.parse_response(api_response.choices[0].message.content)
            print(action)
            return action

        except Exception as e:
            print(e)
            return LLMAction(
                thoughts=f"Error in OpenAI API call: {str(e)}",
                is_complete=False
            )

    async def format_prompt(
        self, task: str, state: TaskState, available_tools: List[str]
    ) -> str:
        """Format prompt for OpenAI"""
        # Generate tool documentation
        tools_documentation = []
        for tool_name in available_tools:
            tool = self.tools.get(tool_name)
            if tool:
                doc = f"""
## {tool.name}
{tool.description}

Parameters:
{self._get_tool_params_doc(tool)}

Returns:
- success: boolean - Whether the operation succeeded
- message: string - Description of the result
- data: any - The operation's result data

Example:
{self._get_tool_example(tool)}
"""
                tools_documentation.append(doc)

        return f'''You are an expert software development AI assistant with access to powerful development tools. Your goal is to help users accomplish their tasks efficiently and effectively.

# Task Description
{task}

# Available Tools
{"\n".join(tools_documentation)}

# Current State
Task Duration: {state.get_task_duration() or 0:.2f} seconds
Status: {"Complete" if state.is_complete else "In Progress"}

# Tool Execution History
{self._format_tool_history(state)}

# Tool Usage Guidelines
1. Analyze the task requirements carefully
2. Use tools in a logical sequence
3. Remember tool execution results and use them in subsequent decisions
4. Handle tool failures gracefully
5. Each tool returns a ToolResult with:
   - success: Indicates if operation succeeded
   - message: Descriptive message
   - data: Operation result data

# Response Format

For tool execution, respond in EXACTLY this format:
```json
{{
    "thoughts": "Detailed explanation of your reasoning and approach",
    "tool_name": "<tool_name>",
    "tool_args": {{
        "param1": "value1",
        "param2": "value2"
    }},
    "is_complete": false
}}
```

For task completion, respond in EXACTLY this format:
```json
{{
    "thoughts": "Final analysis and summary of accomplishments",
    "is_complete": true,
    "result": "Detailed description of what was accomplished"
}}
```

# Example Tool Usage

1. Reading a file:
```json
{{
    "thoughts": "Need to read the content of config.json to check settings",
    "tool_name": "read_file",
    "tool_args": {{
        "path": "config.json"
    }},
    "is_complete": false
}}
```

2. Writing a file:
```json
{{
    "thoughts": "Creating a new Python script with the implementation",
    "tool_name": "write_file",
    "tool_args": {{
        "path": "script.py",
        "content": "print('Hello World')",
        "create_dirs": true
    }},
    "is_complete": false
}}
```

Remember:
- Analyze the task and break it into logical steps
- Use appropriate tools for each step
- Consider previous tool execution results
- Return valid JSON in the specified format
- Mark task as complete only when all objectives are achieved

Now, proceed with the task.'''

    def _clean_json_response(self, response: str) -> str:
        """
        Clean response text to extract JSON content.
        Handles markdown code blocks and other formatting.
        """
        # First try to find JSON in markdown code block
        code_block_match = re.search(r'```(?:json)?\s*({[\s\S]*?})\s*```', response)
        if code_block_match:
            return code_block_match.group(1).strip()
            
        # If no code block, try to find raw JSON
        json_match = re.search(r'\{[^{}]*\{[^{}]*\}[^{}]*\}|\{[^{}]+\}', response)
        if json_match:
            return json_match.group().strip()
            
        return response

    async def parse_response(self, response: str) -> LLMAction:
        """Parse OpenAI's response into an action"""
        try:
            # Clean and extract JSON from response
            cleaned_response = self._clean_json_response(response)
            
            try:
                # Attempt to parse the cleaned response
                data = json.loads(cleaned_response)
            except json.JSONDecodeError:
                # Log the raw and cleaned response for debugging
                print(f"Raw response: {response[:200]}...")
                print(f"Cleaned response: {cleaned_response[:200]}...")
                return LLMAction(
                    thoughts=f"Failed to parse response as JSON. Raw response: {response[:200]}...",
                    is_complete=False
                )
            
            # Validate required fields
            if "thoughts" not in data:
                data["thoughts"] = "No thoughts provided"
                
            if "is_complete" not in data:
                data["is_complete"] = False
                
            # Create LLMAction from parsed data
            return LLMAction(**data)
            
        except Exception as e:
            return LLMAction(
                thoughts=f"Error parsing response: {str(e)}",
                is_complete=False
            )
