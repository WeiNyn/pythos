"""
Agent configuration
"""
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, validator

from .state.config import StateStorageConfig
from .logging import LogConfig, DebugConfig
from .debug import BreakpointConfig

class DebugSettings(BaseModel):
    """Debug settings configuration"""
    enabled: bool = False
    step_by_step: bool = False
    breakpoints: Dict[str, BreakpointConfig] = {}
    logging: DebugConfig = DebugConfig()

class AgentConfig(BaseModel):
    """Configuration for LLM Agent"""
    llm_provider: str
    api_key: str
    working_directory: Path
    state_storage: StateStorageConfig = StateStorageConfig()
    rate_limit: int = 60
    auto_approve_tools: bool = False
    max_consecutive_auto_approvals: int = 3
    debug: DebugSettings = DebugSettings()
    logging: LogConfig = LogConfig()

    @validator("working_directory")
    def validate_working_directory(cls, v: Path) -> Path:
        """Ensure working directory exists"""
        if not v.exists():
            raise ValueError(f"Working directory does not exist: {v}")
        return v

    @validator("api_key")
    def validate_api_key(cls, v: str) -> str:
        """Ensure API key is provided"""
        if not v.strip():
            raise ValueError("API key cannot be empty")
        return v

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """Convert to dictionary with proper Path handling"""
        d = super().dict(*args, **kwargs)
        # Convert Path objects to strings
        d["working_directory"] = str(d["working_directory"])
        if "file_path" in d.get("logging", {}):
            if d["logging"]["file_path"]:
                d["logging"]["file_path"] = str(d["logging"]["file_path"])
        if "path" in d.get("state_storage", {}):
            if d["state_storage"]["path"]:
                d["state_storage"]["path"] = str(d["state_storage"]["path"])
        return d

    def enable_debug(
        self, 
        step_by_step: bool = False,
        breakpoints: Optional[Dict[str, BreakpointConfig]] = None
    ) -> None:
        """Enable debug mode with optional settings"""
        self.debug.enabled = True
        self.debug.step_by_step = step_by_step
        if breakpoints:
            self.debug.breakpoints = breakpoints
        # Set debug logging level
        self.logging.level = "DEBUG"
        self.logging.use_colors = True
        self.logging.show_separators = True
        # Enable all debug features
        self.debug.logging.enable_tool_logging = True
        self.debug.logging.enable_rate_limiter_logging = True
        self.debug.logging.enable_memory_logging = True
        self.debug.logging.enable_separators = True
        self.debug.logging.log_level = "DEBUG"
