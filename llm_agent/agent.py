"""
Core Agent implementation
"""

import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from .callbacks import ApprovalCallback, ConsoleApprovalCallback
from .config import AgentConfig
from .debug import BreakpointType, DebugCallback, DebugInfo, DebugSession
from .llm.base import BaseLLMProvider
from .logging import AgentLogger, TyperLogger
from .state import TaskState
from .state.storage import JsonStateStorage, SqliteStateStorage, StateStorage
from .tools.base import BaseTool


class Agent:
    """Main Agent class that handles task execution and memory management"""

    def __init__(self, config: AgentConfig, approval_callback: Optional[ApprovalCallback] = None):
        """Initialize the agent with the given configuration"""
        self.task_id = str(uuid.uuid4())
        self.checkpoint_count = 0
        self.config = config
        self.tools: Dict[str, BaseTool] = {}
        self.state = TaskState()
        self.llm: Optional[BaseLLMProvider] = None
        self.approval_callback = approval_callback or ConsoleApprovalCallback()

        # Debug session
        self.debug_session = DebugSession()
        self.debug_callback: Optional[DebugCallback] = None

        # Initialize logger based on mode
        log_path = self.config.working_directory / ".llm_agent" / "logs" / "agent.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self.config.logging.file_path = log_path

        # Use TyperLogger in CLI mode, otherwise use default logger
        is_cli_mode = sys.stdin.isatty() and sys.stdout.isatty()
        if is_cli_mode:
            self.logger = TyperLogger("agent", self.config.logging)
            self.logger.show_panel("Agent Initialization", "Setting up agent with CLI mode", style="cyan")
        else:
            self.logger = AgentLogger("agent", self.config.logging)

        # Initialize state storage
        storage_config = self.config.state_storage
        storage_path = storage_config.path or (self.config.working_directory / ".llm_agent" / "state")
        storage_path.mkdir(parents=True, exist_ok=True)

        self.storage: StateStorage = (
            SqliteStateStorage(storage_path / "state.db")
            if storage_config.type == "sqlite"
            else JsonStateStorage(storage_path)
        )

        # Initialize tools and LLM provider
        self._initialize_components()

    def _initialize_components(self) -> None:
        """Initialize the agent's components"""
        # Initialize debug session if enabled
        if self.config.debug.enabled:
            self.debug_session.start()
            self.debug_session.step_by_step = self.config.debug.step_by_step

            for name, bp_config in self.config.debug.breakpoints.items():
                self.debug_session.add_breakpoint(name=name, config=bp_config)

        # Import and initialize tools and LLM provider
        from .llm import create_llm_provider
        from .tools import get_default_tools

        default_tools = get_default_tools(self.config)
        self.llm = create_llm_provider(self.config)

        for tool in default_tools:
            self.register_tool(tool)
            if hasattr(self.llm, "register_tool"):
                self.llm.register_tool(tool)

    def register_tool(self, tool: BaseTool) -> None:
        """Register a new tool with the agent"""
        self.tools[tool.name] = tool
        self.logger.debug(f"Registered tool: {tool.name}", task_id=self.task_id, tool_name=tool.name)

    async def save_user_input(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Save user input to memory"""
        self.state.add_user_input(content, metadata)
        self.storage.save_state(self.task_id, self.state.dict())

    async def save_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Save a conversation message"""
        self.state.add_message(role, content, metadata)
        self.storage.save_state(self.task_id, self.state.dict())

    async def update_context(self, updates: Dict[str, Any]) -> None:
        """Update persistent context"""
        self.state.update_context(updates)
        self.storage.save_state(self.task_id, self.state.dict())

    async def get_related_tasks(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get tasks related to current task"""
        return self.storage.get_related_tasks(self.task_id, limit)

    async def search_task_history(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search through task history"""
        results = self.storage.search_task_history(query, limit)

        tasks = []
        for task_id, relevance in results:
            state = self.storage.load_state(task_id)
            if state:
                tasks.append(
                    {
                        "task_id": task_id,
                        "task": state.get("task", ""),
                        "relevance": relevance,
                        "completed": state.get("is_complete", False),
                        "summary": state.get("conversation_summary", {}),
                    }
                )
        return tasks

    async def execute_task(self, task: str, debug_callback: Optional[DebugCallback] = None) -> Any:
        """Execute a task using the LLM for guidance and tools for actions"""
        if not self.llm:
            raise RuntimeError("LLM provider not initialized")

        self.logger.info(
            f"Starting task execution: {task}",
            task_id=self.task_id,
            context={"state": "initializing"},
        )

        # Generate new task ID and start task
        self.task_id = str(uuid.uuid4())
        self.state.start_new_task(task, self.task_id)

        try:
            self.debug_callback = debug_callback

            # Store initial task message
            await self.save_message("system", f"Starting task: {task}")

            # Find related tasks for context
            related_tasks = await self.get_related_tasks()
            if related_tasks:
                context_update = {"related_tasks": related_tasks}
                await self.update_context(context_update)

            # Begin task execution loop
            max_iterations = 50  # Prevent infinite loops
            iteration = 0

            while not self.state.is_complete and iteration < max_iterations:
                iteration += 1
                self.logger.info(
                    "Starting iteration",
                    task_id=self.task_id,
                    context={"iteration": iteration, "max_iterations": max_iterations},
                )

                # Debug: Check for LLM breakpoint
                await self._handle_debug_break(BreakpointType.LLM, {"task": task, "state": self.state.dict()})

                # Get next action from LLM
                action = await self.llm.get_next_action(
                    task=task, state=self.state, available_tools=list(self.tools.keys())
                )

                # Store assistant's thoughts
                await self.save_message("assistant", action.thoughts)

                # Check for task completion first
                if action.is_complete:
                    self.state.mark_complete()

                    # Store completion message
                    await self.save_message(
                        "system",
                        f"Task completed: {action.result}",
                        {"result": action.result},
                    )

                    self.logger.info(
                        "Task completed successfully",
                        task_id=self.task_id,
                        context={
                            "result": action.result,
                            "duration": self.state.get_task_duration(),
                            "iterations": iteration,
                        },
                    )
                    return action.result or action.thoughts

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
                            "state": self.state.dict(),
                        },
                    )

                    # Get tool approval if needed
                    if (
                        not self.config.auto_approve_tools
                        or self.state.consecutive_auto_approvals >= self.config.max_consecutive_auto_approvals
                    ):
                        approved = await self.approval_callback.get_approval(
                            tool_name=action.tool_name, args=action.tool_args, description=action.thoughts
                        )

                        if not approved:
                            self.logger.info(
                                f"Tool execution rejected: {action.tool_name}",
                                task_id=self.task_id,
                                tool_name=action.tool_name,
                            )
                            continue

                        self.state.reset_auto_approvals()
                    else:
                        self.state.increment_auto_approvals()

                    result = await tool.execute(action.tool_args)

                    # Store tool execution
                    self.state.add_tool_result(action.tool_name, result, action.tool_args)
                    self.storage.save_state(self.task_id, self.state.dict())

                    # Create checkpoint if enabled
                    if self.config.state_storage.auto_checkpoint:
                        self._create_checkpoint(f"After executing tool: {action.tool_name}")

                    # Log tool execution
                    self.logger.info(
                        f"Tool execution complete: {action.tool_name}",
                        task_id=self.task_id,
                        tool_name=action.tool_name,
                        context={
                            "args": action.tool_args,
                            "result": result,
                            "iteration": iteration,
                        },
                    )

            if iteration >= max_iterations:
                self.state.mark_failed("Maximum iterations reached")
                raise RuntimeError("Task execution exceeded maximum iterations")

        except Exception as e:
            self.state.mark_failed(str(e))
            self.logger.error(
                f"Task execution failed: {str(e)}",
                task_id=self.task_id,
                context={"error": str(e)},
            )
            raise

        finally:
            # Save final state
            self.storage.save_state(self.task_id, self.state.dict())

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
                context={"state": self.state.dict()},
            )

            self.debug_callback.on_break(info)

            if self.debug_session.step_by_step:
                self.debug_callback.on_step(info)

    def _create_checkpoint(self, description: str) -> None:
        """Create a state checkpoint"""
        if self.checkpoint_count >= self.config.state_storage.max_checkpoints:
            return

        try:
            self.storage.create_checkpoint(self.task_id, description)
            self.checkpoint_count += 1
        except Exception as e:
            self.logger.warning(
                f"Failed to create checkpoint: {e}",
                task_id=self.task_id,
                context={"error": str(e)},
            )
