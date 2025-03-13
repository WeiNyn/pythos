"""
Tests for the LLM module
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from llm_agent.llm.openai import OpenAIProvider
from llm_agent.tools.base import BaseTool, ToolResult


@pytest.fixture
def mock_openai_response_with_xml():
    """Mock response from OpenAI API with XML formatting"""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""I'll help you with that.

<response>
<thoughts>I need to test this tool</thoughts>
<tool>TestTool</tool>
<args>
<param1>value1</param1>
<param2>value2</param2>
</args>
</response>
"""
            )
        )
    ]
    return mock_response


@pytest.fixture
def mock_openai_response_with_completion():
    """Mock response from OpenAI API with completion result"""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""I've completed the task.

<response>
<thoughts>The task is complete now</thoughts>
<is_complete>true</is_complete>
<result>This is the final result of the task</result>
</response>
"""
            )
        )
    ]
    return mock_response


@pytest.fixture
def mock_openai_response_with_result_tag():
    """Mock response from OpenAI API with <r> result tag"""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""Task completed.

<response>
<thoughts>Task is done</thoughts>
<is_complete>true</is_complete>
<r>Final result with r tag</r>
</response>
"""
            )
        )
    ]
    return mock_response


@pytest.fixture
def mock_tool():
    """Create a mock tool"""
    mock = MagicMock(spec=BaseTool)
    mock.name = "TestTool"
    mock.get_parameters_description.return_value = [
        ("param1", "Parameter 1 description"),
        ("param2", "Parameter 2 description"),
    ]
    mock.get_example.return_value = """
<TestTool>
<args>
    <param1>example1</param1>
    <param2>example2</param2>
</args>
</TestTool>"""
    mock.get_response_format.return_value = """Custom response format for TestTool"""
    return mock


@pytest.fixture
def llm_provider(mock_tool):
    """Create OpenAI provider with mock tools"""
    provider = OpenAIProvider(api_key="test-key", model="test-model")
    provider.register_tool(mock_tool)
    return provider


@pytest.mark.asyncio
async def test_openai_xml_parsing(llm_provider, mock_openai_response_with_xml):
    """Test parsing of XML-formatted tool calls"""
    with patch("llm_agent.llm.openai.AsyncOpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=mock_openai_response_with_xml
        )
        mock_openai.return_value = mock_client

        action = await llm_provider.get_next_action("Test prompt", None)

        assert action.tool_name == "TestTool"
        assert action.tool_args == {"param1": "value1", "param2": "value2"}
        assert action.is_complete is False
        assert action.thoughts == "I need to test this tool"


@pytest.mark.asyncio
async def test_openai_completion_result(
    llm_provider, mock_openai_response_with_completion
):
    """Test parsing of completion results with XML format"""
    with patch("llm_agent.llm.openai.AsyncOpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=mock_openai_response_with_completion
        )
        mock_openai.return_value = mock_client

        action = await llm_provider.get_next_action("Test prompt", None)

        assert action.is_complete is True
        assert action.result == "This is the final result of the task"
        assert action.thoughts == "The task is complete now"


@pytest.mark.asyncio
async def test_openai_r_tag_result(llm_provider, mock_openai_response_with_result_tag):
    """Test parsing results with the <r> tag"""
    with patch("llm_agent.llm.openai.AsyncOpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=mock_openai_response_with_result_tag
        )
        mock_openai.return_value = mock_client

        action = await llm_provider.get_next_action("Test prompt", None)

        assert action.is_complete is True
        assert action.result == "Final result with r tag"
        assert action.thoughts == "Task is done"


@pytest.mark.asyncio
async def test_tool_execution_result_formatting(llm_provider):
    """Test formatting of tool execution results in XML"""
    tool_result = ToolResult(
        success=True,
        message="Tool executed successfully",
        data={"key1": "value1", "key2": [1, 2, 3]},
    )

    formatted = llm_provider.format_tool_result("TestTool", tool_result)

    assert "<tool_result>" in formatted
    assert "<success>true</success>" in formatted
    assert "<message>Tool executed successfully</message>" in formatted
    assert "<data>" in formatted
    assert "value1" in formatted
    assert "[1, 2, 3]" in formatted or "1, 2, 3" in formatted


@pytest.mark.asyncio
async def test_prompt_building_with_xml(llm_provider):
    """Test building prompts with XML formatting for tools"""
    tools = llm_provider.get_registered_tools()
    assert len(tools) == 1

    prompt = llm_provider.build_prompt("Test task")

    assert "Test task" in prompt
    assert "TestTool" in prompt
    assert "Parameter 1 description" in prompt
    assert "Parameter 2 description" in prompt
