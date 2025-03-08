"""
Configuration module for LLM Agent
"""
from typing import Literal, Optional
from pathlib import Path

from pydantic import BaseModel, Field

LLMProvider = Literal["openai", "anthropic"]

class AgentConfig(BaseModel):
    """Configuration for the LLM Agent"""
    
    # LLM Provider settings
    llm_provider: LLMProvider = Field(
        description="The LLM provider to use",
        default="openai"
    )
    api_key: str = Field(
        description="API key for the LLM provider"
    )
    
    # Project settings
    working_directory: Path = Field(
        description="The working directory for the agent",
        default=Path.cwd()
    )
    
    # Tool settings
    auto_approve_tools: bool = Field(
        description="Whether to auto-approve tool executions",
        default=False
    )
    max_consecutive_auto_approvals: int = Field(
        description="Maximum number of consecutive auto-approved tool executions",
        default=3
    )
    
    # Task settings
    task_history_path: Optional[Path] = Field(
        description="Path to store task history",
        default=None
    )
    
    class Config:
        arbitrary_types_allowed = True

    def get_task_history_path(self) -> Path:
        """Get the task history path, creating default if none specified"""
        if self.task_history_path:
            return self.task_history_path
        return self.working_directory / ".llm_agent" / "task_history"
