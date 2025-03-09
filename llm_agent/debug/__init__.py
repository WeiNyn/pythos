"""
Debug system for LLM Agent
"""
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel

class BreakpointType(str, Enum):
    """Types of breakpoints that can be set"""
    TOOL = "tool"  # Break before tool execution
    STATE = "state"  # Break on state changes
    LLM = "llm"  # Break before LLM calls

class BreakpointConfig(BaseModel):
    """Represents a debug breakpoint"""
    type: BreakpointType
    condition: Optional[str] = None  # Python expression to evaluate
    enabled: bool = True

class Breakpoint(BreakpointConfig):
    """Runtime breakpoint instance"""
    pass

class DebugSession(BaseModel):
    """Manages a debug session"""
    active: bool = False
    step_by_step: bool = False
    breakpoints: Dict[str, Breakpoint] = {}
    start_time: Optional[datetime] = None
    
    def start(self) -> None:
        """Start debug session"""
        self.active = True
        self.start_time = datetime.utcnow()
    
    def stop(self) -> None:
        """Stop debug session"""
        self.active = False
        
    def add_breakpoint(self, name: str, config: BreakpointConfig) -> None:
        """Add a new breakpoint"""
        self.breakpoints[name] = Breakpoint(**config.model_dump())
        
    def remove_breakpoint(self, name: str) -> None:
        """Remove a breakpoint"""
        if name in self.breakpoints:
            del self.breakpoints[name]
            
    def should_break(self, bp_type: BreakpointType, context: Dict) -> bool:
        """
        Check if execution should break based on breakpoints
        
        Args:
            bp_type: Type of breakpoint to check
            context: Context variables for condition evaluation
            
        Returns:
            True if execution should break, False otherwise
        """
        if not self.active:
            return False
            
        # Always break in step-by-step mode
        if self.step_by_step:
            return True
            
        # Check matching breakpoints
        for bp in self.breakpoints.values():
            if not bp.enabled or bp.type != bp_type:
                continue
                
            if bp.condition:
                try:
                    if eval(bp.condition, {"context": context}):
                        return True
                except Exception:
                    # Skip invalid conditions
                    continue
            else:
                return True
                
        return False

class DebugInfo(BaseModel):
    """Debug information for current execution"""
    timestamp: datetime
    action: str
    details: Dict
    context: Dict

class DebugCallback:
    """Callback interface for debug events"""
    
    def on_break(self, info: DebugInfo) -> None:
        """Called when execution breaks"""
        pass
        
    def on_step(self, info: DebugInfo) -> None:
        """Called after each step in step-by-step mode"""
        pass
        
    def on_error(self, error: Exception, info: DebugInfo) -> None:
        """Called when an error occurs"""
        pass
