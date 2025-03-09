"""
OpenAI LLM provider implementation
"""
import json
from datetime import datetime
import openai
import re
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any, Tuple, Union
from .base import BaseLLMProvider, LLMAction
from ..state import TaskState
from ..tools.base import BaseTool
from pydantic import BaseModel
from .rate_limiter import RateLimiter
from .prompts import get_system_prompt

class OpenAIProvider(BaseLLMProvider):
    """OpenAI-based LLM provider implementation"""

    def __init__(self, api_key: str, rpm: int = 60):
        """Initialize with API key and rate limit"""
        self.api_key = api_key
        openai.base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        openai.api_key = self.api_key
        self.tools: Dict[str, BaseTool] = {}
        self.rate_limiter = RateLimiter(rpm)
        self.working_dir = Path.cwd()

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool with the provider"""
        self.tools[tool.name] = tool

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

    def _extract_response_xml(self, text: str) -> Union[str, None]:
        """Extract response XML from text"""
        # Look for XML response in the text
        pattern = r"<response>(.*?)</response>"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1) if match else None

    def _parse_args_json(self, args_text: str) -> Dict[str, Any]:
        """Parse JSON args from text"""
        # First try to find JSON object in the text
        pattern = r"\{.*\}"
        match = re.search(pattern, args_text, re.DOTALL)
        if not match:
            raise ValueError("No valid JSON found in args")
        return json.loads(match.group(0))

    async def parse_response(self, response: str) -> LLMAction:
        """Parse OpenAI's response into an action using XML format"""
        try:
            # Extract response XML
            xml_content = self._extract_response_xml(response)
            if not xml_content:
                return LLMAction(
                    thoughts="Could not find response XML",
                    is_complete=False
                )

            # Parse XML structure
            xml = f"<response>{xml_content}</response>"
            root = ET.fromstring(xml)

            # Get required elements
            thoughts = root.find("thoughts")
            thoughts_text = thoughts.text.strip() if thoughts is not None else "No thoughts provided"

            # Check if this is a completion response
            is_complete_elem = root.find("is_complete")
            is_complete = is_complete_elem is not None and is_complete_elem.text.strip().lower() == "true"

            if is_complete:
                result_elem = root.find("result")
                result = result_elem.text.strip() if result_elem is not None else None
                return LLMAction(thoughts=thoughts_text, is_complete=True, result=result)

            # Get tool execution details
            tool = root.find("tool")
            args = root.find("args")

            if tool is None or args is None:
                return LLMAction(
                    thoughts=thoughts_text,
                    is_complete=False
                )

            # Parse the tool args as JSON
            try:
                args_dict = self._parse_args_json(args.text)
            except json.JSONDecodeError:
                return LLMAction(
                    thoughts="Failed to parse tool arguments as JSON",
                    is_complete=False
                )

            return LLMAction(
                thoughts=thoughts_text,
                tool_name=tool.text.strip(),
                tool_args=args_dict,
                is_complete=False
            )

        except ET.ParseError:
            return LLMAction(
                thoughts=f"Failed to parse response as XML: {response[:200]}...",
                is_complete=False
            )
        except Exception as e:
            return LLMAction(
                thoughts=f"Error parsing response: {str(e)}",
                is_complete=False
            )

    async def format_prompt(
        self, task: str, state: TaskState, available_tools: List[str]
    ) -> str:
        """Format prompt for OpenAI"""
        return get_system_prompt(task, [self.tools[name] for name in available_tools], str(self.working_dir))
