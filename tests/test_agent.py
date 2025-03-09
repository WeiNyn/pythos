"""
Tests for the LLM Agent
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from llm_agent import Agent, AgentConfig
from llm_agent.llm.base import LLMAction
from llm_agent.tools.base import ToolResult


@pytest.fixture
def mock_config():
    return AgentConfig(
        llm_provider="openai",
        api_key="test-key",
        working_directory=Path.cwd(),
        auto_approve_tools=True,
    )


@pytest.fixture
async def mock_agent(mock_config):
    agent = Agent(mock_config)
    # Mock the LLM provider
    agent.llm = AsyncMock()
    yield agent


@pytest.mark.asyncio
async def test_agent_initialization(mock_agent):
    """Test that agent initializes correctly"""
    assert mock_agent.config is not None
    assert mock_agent.tools is not None
    assert mock_agent.state is not None
    assert mock_agent.llm is not None


@pytest.mark.asyncio
async def test_tool_registration(mock_agent):
    """Test tool registration"""
    mock_tool = MagicMock()
    mock_tool.name = "test_tool"
    mock_tool.execute = AsyncMock(
        return_value=ToolResult(success=True, message="Test successful", data=None)
    )

    mock_agent.register_tool(mock_tool)
    assert "test_tool" in mock_agent.tools


@pytest.mark.asyncio
async def test_task_execution_success(mock_agent):
    """Test successful task execution"""
    # Mock LLM to return a completion action
    mock_agent.llm.get_next_action = AsyncMock(
        return_value=LLMAction(
            is_complete=True, result="Task completed successfully", thoughts="All done"
        )
    )

    result = await mock_agent.execute_task("Test task")
    assert result == "Task completed successfully"
    assert mock_agent.state.is_complete


@pytest.mark.asyncio
async def test_task_execution_with_tool(mock_agent):
    """Test task execution with tool use"""
    # Mock tool
    mock_tool = MagicMock()
    mock_tool.name = "test_tool"
    mock_tool.execute = AsyncMock(
        return_value=ToolResult(
            success=True, message="Tool executed", data="tool result"
        )
    )
    mock_agent.register_tool(mock_tool)

    # Mock LLM to first request tool, then complete
    mock_agent.llm.get_next_action = AsyncMock()
    mock_agent.llm.get_next_action.side_effect = [
        LLMAction(
            tool_name="test_tool",
            tool_args={"arg": "value"},
            is_complete=False,
            thoughts="Using tool",
        ),
        LLMAction(
            is_complete=True, result="Task completed with tool", thoughts="All done"
        ),
    ]

    result = await mock_agent.execute_task("Test task with tool")
    assert result == "Task completed with tool"
    assert mock_agent.state.is_complete
    assert len(mock_agent.state.tool_executions) == 1
    assert mock_tool.execute.called


@pytest.mark.asyncio
async def test_task_execution_failure(mock_agent):
    """Test task execution failure handling"""
    # Mock LLM to raise an exception
    mock_agent.llm.get_next_action = AsyncMock(side_effect=Exception("Test error"))

    with pytest.raises(Exception):
        await mock_agent.execute_task("Test task")

    assert mock_agent.state.is_failed
    assert mock_agent.state.error_message == "Test error"
