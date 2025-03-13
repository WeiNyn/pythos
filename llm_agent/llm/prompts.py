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

You have access to tools that are executed upon approval.
Use one tool per message and wait for its result before proceeding.
Tool usage must follow XML format:

<tool_name>
<param1>value1</param1>
<param2>value2</param2>
</tool_name>"""

    # Response format - this is now a general format, specific tools may override
    response_format = """
# Response Format

For tool execution:
<response>
<thoughts>Explain your analysis and next steps</thoughts>
<tool>tool_name</tool>
<args>
    <param1>value1</param1>
    <param2>value2</param2>
</args>
<is_complete>false</is_complete>
</response>

For task completion:
<response>
<thoughts>Final analysis and summary</thoughts>
<is_complete>true</is_complete>
<r>Detailed result description</r>
</response>"""

    # Generate tool documentation
    tools_doc = """
# Available Tools"""

    # Generate documentation for each tool
    tools_detail = []
    for tool in tools:
        # First add the tool description
        doc = f"""
## {tool.name}
{tool.description}
"""
        # Add parameter descriptions if available
        params = tool.get_parameters_description()
        if params:
            doc += "\nParameters:\n"
            for param_name, param_desc in params:
                doc += f"- `{param_name}`: {param_desc}\n"

        # Add example from the tool itself
        doc += f"\nExample:\n{tool.get_example()}\n"

        tools_detail.append(doc)

    # Combine all sections
    return f"""
{role}

{tool_use}

{response_format}

{tools_doc}
{"".join(tools_detail)}"""
