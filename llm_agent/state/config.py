"""
State storage configuration
"""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class StateStorageConfig(BaseModel):
    """Configuration for state storage"""

    type: Literal["json", "sqlite"] = Field(default="json", description="Storage backend type")
    path: Path = Field(
        description="Path to storage directory or database file",
        default=Path.cwd() / ".llm_agent",
    )
    auto_checkpoint: bool = Field(
        default=True,
        description="Create checkpoints automatically after tool executions",
    )
    max_checkpoints: int = Field(default=10, description="Maximum number of checkpoints to keep per task")
