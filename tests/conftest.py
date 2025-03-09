"""
Shared test fixtures and configuration
"""

import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock

import pytest

from llm_agent import Agent, AgentConfig
from llm_agent.state import TaskState
from llm_agent.tools.base import BaseTool, ToolResult


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def config(temp_dir: Path) -> AgentConfig:
    """Create a test configuration"""
    return AgentConfig(
        llm_provider="openai",
        api_key="test-key",
        working_directory=temp_dir,
        auto_approve_tools=True,
    )


@pytest.fixture
async def mock_tool() -> BaseTool:
    """Create a mock tool"""

    class MockTool(BaseTool):
        def __init__(self):
            super().__init__("mock_tool", "A mock tool for testing")

        async def execute(self, args: dict) -> ToolResult:
            return ToolResult(
                success=True, message="Mock tool executed successfully", data=args
            )

    return MockTool()


@pytest.fixture
async def agent(
    config: AgentConfig, mock_tool: BaseTool
) -> AsyncGenerator[Agent, None]:
    """Create an agent with mock tools and LLM"""
    agent = Agent(config)

    # Register mock tool
    agent.register_tool(mock_tool)

    # Mock LLM provider
    agent.llm = AsyncMock()

    yield agent


@pytest.fixture
def task_state() -> TaskState:
    """Create a clean task state"""
    return TaskState()
