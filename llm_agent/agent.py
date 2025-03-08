"""
Core Agent implementation
"""
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime
import asyncio
import uuid

from .config import AgentConfig
from .logging import AgentLogger
from .tools.base import BaseTool
from .state import TaskState
from .llm.base import BaseLLMProvider
from .debug import (
    DebugSession,
    DebugInfo,
    DebugCallback,
    BreakpointType
)


class Agent:
    """
    Main Agent class that handles task execution and tool coordination
    """
    
    def __init__(self, config: AgentConfig):
        """Initialize the agent with the given configuration"""
        self.task_id = str(uuid.uuid4())
        self.config = config
        self.tools: Dict[str, BaseTool] = {}
        self.state = TaskState()
        self.llm: Optional[BaseLLMProvider] = None
        
        # Debug session
        self.debug_session = DebugSession()
        self.debug_callback: Optional[DebugCallback] = None
        
        # Initialize logger
        log_path = self.config.working_directory / ".llm_agent" / "logs" / "agent.log"
        self.config.logging.file_path = log_path
        self.logger = AgentLogger("agent", self.config.logging)
        
        # Initialize tools and LLM provider
        self._initialize_components()

    def _initialize_components(self) -> None:
        """Initialize the agent's components (tools and LLM provider)"""
        # Initialize debug session if enabled
        if self.config.debug.enabled:
            self.debug_session.start()
            self.debug_session.step_by_step = self.config.debug.step_by_step
            
            # Set up breakpoints from config
            for name, bp_config in self.config.debug.breakpoints.items():
                self.debug_session.add_breakpoint(name=name, config=bp_config)
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
        self.logger.debug(
            f"Registered tool: {tool.name}",
            task_id=self.task_id,
            tool_name=tool.name
        )

    async def execute_task(self, task: str, debug_callback: Optional[DebugCallback] = None) -> Any:
        """
        Execute a task using the LLM for guidance and tools for actions
        
        Args:
            task: The task description to execute
            
        Returns:
            The result of the task execution
        """
        if not self.llm:
            raise RuntimeError("LLM provider not initialized")
            
        # Generate new task ID and start task
        self.task_id = str(uuid.uuid4())
        self.state.start_new_task(task)
        
        self.logger.info(
            f"Starting task execution: {task}",
            task_id=self.task_id,
            context={"state": "starting"}
        )
        
        try:
            self.debug_callback = debug_callback
            
            # Begin task execution loop
            while not self.state.is_complete:
                # Debug: Check for LLM breakpoint
                await self._handle_debug_break(
                    BreakpointType.LLM,
                    {"task": task, "state": self.state.dict()}
                )
                
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
                    
                    # Debug: Check for tool breakpoint
                    await self._handle_debug_break(
                        BreakpointType.TOOL,
                        {
                            "tool": action.tool_name,
                            "args": action.tool_args,
                            "state": self.state.dict()
                        }
                    )
                        
                    # Execute tool with approval if needed
                    if not self.config.auto_approve_tools or self.state.consecutive_auto_approvals >= self.config.max_consecutive_auto_approvals:
                        # TODO: Implement approval mechanism
                        pass
                        
                    result = await tool.execute(action.tool_args)
                    
                    # Log tool execution
                    self.logger.info(
                        f"Tool execution complete: {action.tool_name}",
                        task_id=self.task_id,
                        tool_name=action.tool_name,
                        context={
                            "args": action.tool_args,
                            "result": result
                        }
                    )
                    
                    self.state.add_tool_result(action.tool_name, result)
                    
                    # Debug: Check state change
                    await self._handle_debug_break(
                        BreakpointType.STATE,
                        {"state": self.state.dict()}
                    )
                    
                    # Check if task is complete
                    if action.is_complete:
                        self.state.mark_complete()
                        self.logger.info(
                            "Task completed successfully",
                            task_id=self.task_id,
                            context={
                                "result": action.result,
                                "duration": self.state.get_task_duration()
                            }
                        )
                        return action.result
                    
        except Exception as e:
            self.logger.error(
                f"Task execution failed: {e}",
                task_id=self.task_id,
                context={"error": str(e), "traceback": str(e.__traceback__)}
            )
            self.state.mark_failed(str(e))
            
            # Debug: Handle error in debug callback
            if self.debug_callback and self.config.debug.enabled:
                self.debug_callback.on_error(
                    e,
                    DebugInfo(
                        timestamp=datetime.utcnow(),
                        action="error",
                        details={"error": str(e)},
                        context={"state": self.state.dict()}
                    )
                )
            raise
            
        finally:
            # Save task history
            self._save_task_history()
            
            # Stop debug session if active
            if self.debug_session.active:
                self.debug_session.stop()
                self.debug_callback = None
    async def _handle_debug_break(self, bp_type: BreakpointType, context: Dict) -> None:
        """Handle potential debug breakpoints"""
        if not self.config.debug.enabled or not self.debug_callback:
            return
            
        if self.debug_session.should_break(bp_type, context):
            info = DebugInfo(
                timestamp=datetime.utcnow(),
                action=bp_type.value,
                details=context,
                context={"state": self.state.dict()}
            )
            
            # Notify callback of break
            self.debug_callback.on_break(info)
            
            if self.debug_session.step_by_step:
                self.debug_callback.on_step(info)

    def _save_task_history(self) -> None:
        """Save the current task history"""
        history_path = self.config.get_task_history_path()
        history_path.parent.mkdir(parents=True, exist_ok=True)
        
        # TODO: Implement task history saving
        pass
