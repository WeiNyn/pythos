# Cline - LLM Agent Framework

A powerful Python framework for building and integrating LLM-powered agent systems with debugging capabilities and state management.

## Project Information

**Cline** is a sophisticated LLM Agent framework designed to facilitate the creation, execution, and management of LLM-powered tasks. It provides a structured approach to agent development with robust features for debugging, state management, and tool execution.

### Key Features

- **Agent-Based Architecture**: Core agent implementation for executing complex tasks
- **LLM Provider Integration**: Support for OpenAI and extensible for other providers
- **Tool-Based Execution**: Pluggable tool system for agent capabilities
- **State Management**: Comprehensive state tracking and persistence
- **Debug Capabilities**: Breakpoints, step-by-step execution, and rich debugging
- **Logging**: Configurable logging system for tracking agent activities
- **Checkpoint System**: Create and manage system checkpoints for task progress
- **YAML Configuration**: Easy-to-use YAML-based configuration system
- **Environment Variables**: Secure handling of sensitive data
- **User Approval System**: Flexible callback system for tool execution approval

## Architecture

### Core Components

```
llm_agent/
├── agent.py              # Main Agent class implementation
├── config.py             # Configuration models and validation
├── __init__.py           # Package exports
├── callbacks/            # User approval callback system
│   ├── base.py           # Base callback interface
│   └── __init__.py       # Callback exports
├── debug/                # Debugging functionality
├── llm/                  # LLM provider implementations
│   ├── base.py           # Base LLM provider interface
│   ├── openai.py         # OpenAI implementation
│   ├── prompts.py        # System prompts and templates
│   └── rate_limiter.py   # Rate limiting for API calls
├── logging/              # Logging configuration
├── state/                # State management
│   ├── config.py         # State storage configuration
│   ├── storage.py        # State persistence implementations
│   └── task_state.py     # Task state models and management
└── tools/                # Tool implementations
    ├── base.py           # Base tool interface
    ├── file_operations.py# File system tools
    └── __init__.py       # Tool registration
```

### Data Flow

1. **Initialization**: Agent is configured with LLM provider, tools, and debug settings
2. **Task Execution**: 
   - User provides task description
   - Agent processes task through LLM
   - LLM determines next action (tool execution or completion)
   - Tools execute with user approval if required
   - Results feed back to LLM for next action determination
3. **State Management**:
   - Messages, tool executions, and context are tracked in TaskState
   - State is persisted via JSON or SQLite storage
   - Checkpoints are created at key moments
4. **Debugging**:
   - Debug breakpoints can interrupt execution
   - Step-by-step mode for detailed analysis
   - Rich logging for troubleshooting

### Component Interactions

- **Agent**: Central coordination of task execution flow
- **LLM Providers**: Generate actions based on task and state
- **Tools**: Implement specific capabilities (file operations, etc.)
- **State Management**: Track and persist task progress
- **Debug**: Provide visibility and control during execution

## Development Guidelines

### Setting Up the Development Environment

1. **Prerequisites**:
   - Python 3.8+ installed
   - API keys for LLM providers (OpenAI, etc.)

2. **Installation**:
   ```bash
   # Clone the repository
   git clone https://github.com/your-org/cline.git
   cd cline
   
   # Create a virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   
   # Install dependencies
   pip install -e .
   ```

3. **Environment Configuration**:
   - Copy `.env.example` to `.env` and fill in your API keys:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` with your actual API keys and settings:
     ```
     OPENAI_API_KEY=your-api-key-here
     OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
     ```

4. **Configuration**:
   - The project uses YAML-based configuration
   - Default configuration is in `config.yaml`
   - Environment variables can be referenced using `${VAR_NAME}` syntax
   - Example configuration:
     ```yaml
     llm_provider: "openai"
     api_key: ${OPENAI_API_KEY}
     base_url: ${OPENAI_BASE_URL}
     working_directory: "."
     ```

### Creating New Components

#### Adding a New Tool

1. Extend the `BaseTool` class in a new file under `llm_agent/tools/`
2. Implement the required abstract methods
3. Register the tool in `llm_agent/tools/__init__.py`

Example:
```python
from .base import BaseTool, ToolResult

class MyNewTool(BaseTool):
    """My new tool description"""
    
    async def _execute(self, args: Dict[str, Any]) -> ToolResult:
        # Implement tool logic
        return ToolResult(
            success=True,
            message="Operation successful",
            data={"result": "value"}
        )
```

#### Adding a New LLM Provider

1. Extend the `BaseLLMProvider` class in a new file under `llm_agent/llm/`
2. Implement the required abstract methods
3. Register the provider in `llm_agent/llm/__init__.py`

### Code Style and Best Practices

1. **Use Type Hints**: All code should use proper typing
2. **Documentation**: Add docstrings to classes and methods
3. **Error Handling**: Implement proper error handling and reporting
4. **Testing**: Write tests for all new functionality
5. **Logging**: Use the logging system appropriately for debugging
6. **Async Programming**: Use async/await consistently throughout the codebase

### Testing

Run tests with pytest:
```bash
python -m pytest
```

### Example Usage

```python
import asyncio
from pathlib import Path
from llm_agent.agent import Agent
from llm_agent.config import AgentConfig
from llm_agent.callbacks import ConsoleApprovalCallback

async def run_task():
    # Load configuration from YAML
    config = AgentConfig.from_yaml("config.yaml")
    
    # Create approval callback (optional)
    approval_callback = ConsoleApprovalCallback()
    
    # Create agent instance with callback
    agent = Agent(config, approval_callback=approval_callback)
    
    # Execute task
    result = await agent.execute_task(
        "Create a Python script that calculates prime numbers"
    )
    print(f"Task completed: {result}")

if __name__ == "__main__":
    asyncio.run(run_task())
```

### User Approval System

The framework includes a flexible callback system for handling user approvals of tool executions:

1. **Base Callback Interface**:
   ```python
   from llm_agent.callbacks import ApprovalCallback
   
   class MyCustomCallback(ApprovalCallback):
       async def get_approval(self, tool_name: str, args: Dict[str, Any], description: Optional[str] = None) -> bool:
           # Implement custom approval logic
           return True  # or False
   ```

2. **Default Console Callback**:
   - Built-in `ConsoleApprovalCallback` for command-line interaction
   - Displays tool details and gets user input
   - Handles yes/no responses with validation

3. **Configuration**:
   ```yaml
   auto_approve_tools: false  # Require approval for all tools
   max_consecutive_auto_approvals: 5  # Auto-approve after 5 consecutive approvals
   ```

4. **Usage**:
   - Pass callback to Agent constructor
   - System automatically requests approval when needed
   - Tracks consecutive approvals for auto-approval feature

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see the LICENSE file for details. 