"""
System prompts for LLM Providers
"""

from typing import List

from ..tools.base import BaseTool


def get_system_prompt(task: str, tools: List[BaseTool], working_dir: str) -> str:
    """Generate the system prompt for the LLM."""
    # Basic role and expertise
    role = """You are a Python software development specialist with expertise in:
- Python language features and best practices
- Common Python frameworks and libraries
- Testing frameworks (pytest, unittest)
- Code organization and design patterns
- Performance optimization and profiling
- Type hints and static type checking
- Package management and distribution"""

    # Tool use format
    tool_use = """
====

TOOL USE

You have access to tools that are executed upon approval. Use one tool per message and wait for its result before proceeding. Tool usage must follow XML format:

<tool_name>
<param1>value1</param1>
<param2>value2</param2>
</tool_name>"""

    # Response format
    response_format = """
# Response Format

For tool execution:
<response>
<thoughts>Explain your analysis and next steps</thoughts>
<tool>tool_name</tool>
<args>
{
    "param1": "value1",
    "param2": "value2"
}
</args>
<is_complete>false</is_complete>
</response>

For task completion:
<response>
<thoughts>Final analysis and summary</thoughts>
<is_complete>true</is_complete>
<result>Detailed result description</result>
</response>"""

    # Generate tool documentation
    tools_doc = """
# Available Tools"""

    # Generate documentation for each tool
    tools_detail = []
    for tool in tools:
        doc = f"""
## {tool.name}
{tool.description}

Example:
<{tool.name}>"""

        # Add example parameters based on tool
        if tool.name == "ReadFileTool":
            doc += f"""
<path>src/main.py</path>
</{tool.name}>"""
        elif tool.name == "WriteFileTool":
            doc += f"""
<path>src/output.txt</path>
<content>Hello, world!</content>
<create_dirs>true</create_dirs>
</{tool.name}>"""
        elif tool.name == "SearchFilesTool":
            doc += f"""
<directory>src</directory>
<pattern>*.py</pattern>
<recursive>true</recursive>
</{tool.name}>"""
        elif tool.name == "ListFilesTool":
            doc += f"""
<directory>src</directory>
<recursive>false</recursive>
</{tool.name}>"""

        tools_detail.append(doc)

    # Combine all sections
    return f"""
{role}

{tool_use}

{response_format}

{tools_doc}
{"".join(tools_detail)}"""
