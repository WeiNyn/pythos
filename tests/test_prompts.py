"""
Tests for prompt generation and formatting
"""

from pathlib import Path
import pytest

from llm_agent.llm.prompts import get_system_prompt
from llm_agent.tools.base import BaseTool, ToolResult


class SimpleTestTool(BaseTool):
    """A simple tool for testing prompt generation"""

    def __init__(self):
        super().__init__()
        self.name = "test_tool"
        self.description = "A test tool for prompt testing"

    async def _execute(self, args: dict) -> ToolResult:
        """Execute the test tool"""
        return ToolResult(success=True, message="Test executed", data=args)
    
    def get_parameters_description(self):
        """Return test parameter descriptions"""
        return [
            ("param1", "First test parameter"),
            ("param2", "Second test parameter"),
        ]
    
    def get_example(self):
        """Return a usage example"""
        return """<test_tool>
<args>
    <param1>example1</param1>
    <param2>example2</param2>
</args>
</test_tool>"""


class ComplexTestTool(BaseTool):
    """A complex tool with custom response format"""
    
    def __init__(self):
        super().__init__()
        self.name = "complex_tool"
        self.description = "A complex test tool with custom format"
    
    async def _execute(self, args: dict) -> ToolResult:
        """Execute the complex tool"""
        return ToolResult(success=True, message="Complex tool executed", data=args)
    
    def get_parameters_description(self):
        """Return complex parameter descriptions"""
        return [
            ("complex_param", "A complex parameter"),
            ("format", "Output format specification"),
            ("options", "Additional options")
        ]
    
    def get_example(self):
        """Return a complex example"""
        return """<complex_tool>
<args>
    <complex_param>complex value</complex_param>
    <format>json</format>
    <options>{"verbose": true}</options>
</args>
</complex_tool>"""
    
    def get_response_format(self):
        """Return a custom response format"""
        return """<response>
<thoughts>Analysis for complex tool usage</thoughts>
<tool>complex_tool</tool>
<args>
    <complex_param>value</complex_param>
    <format>value</format>
    <options>value</options>
</args>
<is_complete>false</is_complete>
</response>"""


@pytest.fixture
def simple_tool():
    """Create a simple test tool"""
    return SimpleTestTool()


@pytest.fixture
def complex_tool():
    """Create a complex test tool"""
    return ComplexTestTool()


def test_get_system_prompt_basic(simple_tool):
    """Test basic system prompt generation"""
    task = "Test simple task"
    working_dir = str(Path.cwd())
    
    prompt = get_system_prompt(task, [simple_tool], working_dir)
    
    # Verify basic components exist
    assert "Python software development specialist" in prompt
    assert "You have access to tools" in prompt
    assert "Response Format" in prompt
    assert "Available Tools" in prompt
    
    # Verify task-specific components
    assert "test_tool" in prompt
    assert "A test tool for prompt testing" in prompt
    assert "First test parameter" in prompt
    assert "Second test parameter" in prompt
    assert "example1" in prompt
    assert "example2" in prompt


def test_get_system_prompt_multiple_tools(simple_tool, complex_tool):
    """Test system prompt with multiple tools"""
    task = "Test with multiple tools"
    working_dir = str(Path.cwd())
    
    prompt = get_system_prompt(task, [simple_tool, complex_tool], working_dir)
    
    # Verify both tools exist in the prompt
    assert "test_tool" in prompt
    assert "complex_tool" in prompt
    assert "A test tool for prompt testing" in prompt
    assert "A complex test tool with custom format" in prompt
    
    # Verify parameters for both exist
    assert "First test parameter" in prompt
    assert "A complex parameter" in prompt
    assert "Output format specification" in prompt
    
    # Verify examples for both exist
    assert "example1" in prompt
    assert "complex value" in prompt


def test_prompt_escaping_and_sanitization():
    """Test prompt escaping and sanitization of potentially problematic inputs"""
    class ProblematicTool(BaseTool):
        def __init__(self):
            super().__init__()
            self.name = "problem_tool"
            self.description = "Tool with <xml> & special chars' \" in description"
        
        async def _execute(self, args: dict) -> ToolResult:
            return ToolResult(success=True, message="OK", data={})
        
        def get_parameters_description(self):
            return [
                ("xml_param", "Parameter with <tags> & quotes'\""),
                ("normal", "Normal parameter")
            ]
        
        def get_example(self):
            return """<problem_tool>
<args>
    <xml_param>value with <xml> & quotes'\"</xml_param>
    <normal>normal value</normal>
</args>
</problem_tool>"""
    
    # Test with problematic inputs
    problem_tool = ProblematicTool()
    task = "Task with <special> & chars'"
    working_dir = "C:\\Path\\With\\Backslashes"
    
    # Should not raise exceptions
    prompt = get_system_prompt(task, [problem_tool], working_dir)
    
    # Verify content exists without breaking
    assert "Tool with <xml>" in prompt
    assert "Parameter with <tags>" in prompt
    assert "value with <xml>" in prompt


def test_get_system_prompt_empty_tools():
    """Test system prompt with no tools"""
    task = "Test with no tools"
    working_dir = str(Path.cwd())
    
    prompt = get_system_prompt(task, [], working_dir)
    
    # Verify basic structure still exists
    assert "Python software development specialist" in prompt
    assert "You have access to tools" in prompt
    assert "Response Format" in prompt
    assert "Available Tools" in prompt
    
    # Verify no tool-specific sections
    assert "# Available Tools\n\n" in prompt or "# Available Tools\n" in prompt 