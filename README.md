# LLM Agent

A Python library for LLM-powered development assistance, inspired by the Cline project.

## Features

- Python-focused development assistance
- File operations and code analysis
- Terminal command execution
- Task state management
- Support for multiple LLM providers

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/llm-agent.git
cd llm-agent
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install the package in development mode:
```bash
pip install -e .
```

4. Set up environment variables:
```bash
cp .env.example .env
```
Then edit `.env` to add your API keys.

## Usage

Here's a simple example of using the agent:

```python
import asyncio
from pathlib import Path
import os
from dotenv import load_dotenv

from llm_agent import Agent, AgentConfig

async def main():
    # Load environment variables
    load_dotenv()
    
    # Configure the agent
    config = AgentConfig(
        llm_provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        working_directory=Path.cwd()
    )

    # Create agent instance
    agent = Agent(config)

    # Execute a task
    result = await agent.execute_task(
        "Create a simple Python function that calculates the factorial of a number"
    )
    
    print("Task completed!")
    print("Result:", result)

if __name__ == "__main__":
    asyncio.run(main())
```

See the `examples` directory for more usage examples.

## Development

1. Install development dependencies:
```bash
pip install -e ".[dev]"
```

2. Run tests:
```bash
pytest
```

## Configuration

The `AgentConfig` class supports the following options:

```python
config = AgentConfig(
    # Required
    llm_provider="openai",  # Currently supported: "openai"
    api_key="your-api-key",
    
    # Optional
    working_directory=Path.cwd(),  # Default: current directory
    auto_approve_tools=False,      # Default: False
    task_history_path=None,        # Default: .llm_agent/task_history
)
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
