"""
Task state management
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel

class ToolExecution(BaseModel):
    """Record of a tool execution"""
    tool_name: str
    args: Dict[str, Any]
    result: Any
    timestamp: datetime

class TaskState(BaseModel):
    """Represents the current state of a task"""
    task: Optional[str] = None
    tool_executions: List[ToolExecution] = []
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_complete: bool = False
    is_failed: bool = False
    error_message: Optional[str] = None
    consecutive_auto_approvals: int = 0

    def start_new_task(self, task: str) -> None:
        """Start a new task"""
        self.task = task
        self.tool_executions = []
        self.start_time = datetime.utcnow()
        self.end_time = None
        self.is_complete = False
        self.is_failed = False
        self.error_message = None
        self.consecutive_auto_approvals = 0

    def add_tool_result(self, tool_name: str, result: Any, args: Dict[str, Any] = None) -> None:
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
                args=args or {},
                result=result,
                timestamp=datetime.utcnow()
            )
        )

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

    def reset_auto_approvals(self) -> None:
        """Reset the consecutive auto-approvals counter"""
        self.consecutive_auto_approvals = 0

    def increment_auto_approvals(self) -> None:
        """Increment the consecutive auto-approvals counter"""
        self.consecutive_auto_approvals += 1

    class Config:
        """Pydantic config"""
        arbitrary_types_allowed = True
