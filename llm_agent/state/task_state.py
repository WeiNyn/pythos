"""
Task state management
"""
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel

class Message(BaseModel):
    """Represents a single message in the conversation"""
    role: str  # 'user', 'assistant', or 'system'
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}

class UserInput(BaseModel):
    """Represents user input with metadata"""
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}
    response: Optional[str] = None

class RelatedTask(BaseModel):
    """Represents a related task reference"""
    task_id: str
    description: str
    relevance_score: float
    completed: bool
    timestamp: datetime

class ToolExecution(BaseModel):
    """Record of a tool execution"""
    tool_name: str
    args: Dict[str, Any]
    result: Any
    timestamp: datetime

class TaskState(BaseModel):
    """Represents the current state of a task"""
    task: Optional[str] = None
    task_id: Optional[str] = None
    
    # Basic state tracking
    tool_executions: List[ToolExecution] = []
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_complete: bool = False
    is_failed: bool = False
    error_message: Optional[str] = None
    consecutive_auto_approvals: int = 0
    
    # Memory components
    messages: List[Message] = []  # Conversation history
    user_inputs: List[UserInput] = []  # User inputs with metadata
    related_tasks: List[RelatedTask] = []  # Connected tasks
    context: Dict[str, Any] = {}  # Persistent context storage
    
    def start_new_task(self, task: str, task_id: str) -> None:
        """Start a new task"""
        self.task = task
        self.task_id = task_id
        self.tool_executions = []
        self.start_time = datetime.utcnow()
        self.end_time = None
        self.is_complete = False
        self.is_failed = False
        self.error_message = None
        self.consecutive_auto_approvals = 0
        self.messages = []
        self.user_inputs = []
        # Keep context and related_tasks for continuity

    def add_tool_result(self, tool_name: str, result: Any, args: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a tool execution result
        
        Args:
            tool_name: Name of the executed tool
            result: Result from the tool execution
            args: Arguments used in the tool execution
        """
        self.tool_executions.append(
            ToolExecution(
                tool_name=tool_name,
                args=args if args is not None else {},
                result=result,
                timestamp=datetime.utcnow()
            )
        )

    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a message to the conversation history"""
        self.messages.append(
            Message(
                role=role,
                content=content,
                timestamp=datetime.utcnow(),
                metadata=metadata or {}
            )
        )

    def add_user_input(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record user input with optional metadata"""
        self.user_inputs.append(
            UserInput(
                content=content,
                timestamp=datetime.utcnow(),
                metadata=metadata or {}
            )
        )

    def add_related_task(
        self, task_id: str, description: str, relevance_score: float, completed: bool
    ) -> None:
        """Add a related task reference"""
        self.related_tasks.append(
            RelatedTask(
                task_id=task_id,
                description=description,
                relevance_score=relevance_score,
                completed=completed,
                timestamp=datetime.utcnow()
            )
        )

    def update_context(self, updates: Dict[str, Any]) -> None:
        """Update the persistent context"""
        self.context.update(updates)

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a value from the context"""
        return self.context.get(key, default)

    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """Get most recent messages"""
        return self.messages[-limit:]

    def get_recent_tools(self, limit: int = 5) -> List[ToolExecution]:
        """Get most recent tool executions"""
        return self.tool_executions[-limit:]

    def mark_complete(self) -> None:
        """Mark the task as complete"""
        self.is_complete = True
        self.end_time = datetime.utcnow()

    def mark_failed(self, error_message: str) -> None:
        """
        Mark the task as failed
        
        Args:
            error_message: Description of what went wrong
        """
        self.is_failed = True
        self.is_complete = True
        self.error_message = error_message
        self.end_time = datetime.utcnow()

    def get_last_tool_result(self) -> Optional[ToolExecution]:
        """Get the most recent tool execution"""
        return self.tool_executions[-1] if self.tool_executions else None

    def get_task_duration(self) -> Optional[float]:
        """
        Get the task duration in seconds
        
        Returns:
            Duration in seconds or None if task hasn't ended
        """
        if not self.start_time:
            return None
            
        end = self.end_time or datetime.utcnow()
        return (end - self.start_time).total_seconds()

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the conversation"""
        return {
            "message_count": len(self.messages),
            "user_input_count": len(self.user_inputs),
            "tool_execution_count": len(self.tool_executions),
            "duration": self.get_task_duration(),
            "last_interaction": self.messages[-1].timestamp if self.messages else None,
        }

    def reset_auto_approvals(self) -> None:
        """Reset the consecutive auto-approvals counter"""
        self.consecutive_auto_approvals = 0

    def increment_auto_approvals(self) -> None:
        """Increment the consecutive auto-approvals counter"""
        self.consecutive_auto_approvals += 1

    class Config:
        """Pydantic config"""
        arbitrary_types_allowed = True
