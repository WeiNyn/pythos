"""
Core Agent implementation
"""
from typing import Any, Dict, List, Optional
from pathlib import Path
import asyncio
import logging

from .config import AgentConfig
from .tools.base import BaseTool
from .state import TaskState
from .llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)

class Agent:
    """
    Main Agent class that handles task execution and tool coordination
    """
    
    def __init__(self, config: AgentConfig):
        """Initialize the agent with the given configuration"""
        self.config = config
        self.tools: Dict[str, BaseTool] = {}
        self.state = TaskState()
        self.llm: Optional[BaseLLMProvider] = None
        
        # Initialize tools and LLM provider
        self._initialize_components()

    def _initialize_components(self) -> None:
        """Initialize the agent's components (tools and LLM provider)"""
        from .tools import get_default_tools
        from .llm import create_llm_provider, BaseLLMProvider
        
        # Initialize tools
        default_tools = get_default_tools(self.config)
        for tool in default_tools:
            self.register_tool(tool)
            
        # Initialize LLM provider
        self.llm = create_llm_provider(self.config)

    def register_tool(self, tool: BaseTool) -> None:
        """Register a new tool with the agent"""
        self.tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    async def execute_task(self, task: str) -> Any:
        """
        Execute a task using the LLM for guidance and tools for actions
        
        Args:
            task: The task description to execute
            
        Returns:
            The result of the task execution
        """
        if not self.llm:
            raise RuntimeError("LLM provider not initialized")
            
        self.state.start_new_task(task)
        
        try:
            # Begin task execution loop
            while not self.state.is_complete:
                # Get next action from LLM
                action = await self.llm.get_next_action(
                    task=task,
                    state=self.state,
                    available_tools=list(self.tools.keys())
                )
                
                # Execute tool if specified
                if action.tool_name:
                    tool = self.tools.get(action.tool_name)
                    if not tool:
                        raise ValueError(f"Unknown tool: {action.tool_name}")
                        
                    # Execute tool with approval if needed
                    if not self.config.auto_approve_tools or self.state.consecutive_auto_approvals >= self.config.max_consecutive_auto_approvals:
                        # TODO: Implement approval mechanism
                        pass
                        
                    result = await tool.execute(action.tool_args)
                    self.state.add_tool_result(action.tool_name, result)
                    
                # Check if task is complete
                if action.is_complete:
                    self.state.mark_complete()
                    return action.result
                    
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            self.state.mark_failed(str(e))
            raise
            
        finally:
            # Save task history
            self._save_task_history()

    def _save_task_history(self) -> None:
        """Save the current task history"""
        history_path = self.config.get_task_history_path()
        history_path.parent.mkdir(parents=True, exist_ok=True)
        
        # TODO: Implement task history saving
        pass
