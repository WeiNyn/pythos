# LLM Agent Developer Guide

## Overview

The `llm_agent` is a Python package designed to facilitate the creation of intelligent agents that can perform tasks using Language Models (LLMs) and a variety of tools. It provides a modular architecture that separates concerns into distinct components like agent orchestration, LLM provider integration, tool management, state management, and debugging.

This guide is intended for developers who want to understand the structure of the `llm_agent` package, extend its capabilities by adding new tools or LLM providers, or use it as a foundation for building custom agents.

For a high-level architectural overview, refer to [docs/agent-architecture.md](docs/agent-architecture.md).

## Core Modules

-   **`agent.py`**: Contains the `Agent` class, the central component responsible for orchestrating task execution. It manages the task loop, interacts with the LLM, executes tools, and handles state transitions.
-   **`config.py`**: Defines the `AgentConfig` class, which provides a structured way to configure all aspects of the agent, including debugging, logging, state storage, LLM provider, and tool settings.
-   **`llm/`**: This directory contains implementations for different Language Model Providers.
    -   **`base.py`**: Defines abstract base classes (`BaseLLMProvider`, `LLMAction`) that specify the interface for LLM providers and the structure of actions returned by the LLM.
    -   **`openai.py`**: Implements the `OpenAIProvider` class for interacting with the OpenAI API. (Note: Current implementation is a mock for testing purposes.)
-   **`tools/`**: This directory houses the implementations of various tools that the agent can utilize.
    -   **`base.py`**: Defines base classes (`BaseTool`, `ToolArguments`, `ToolResult`) for creating new tools.
    -   **`file_operations.py`**: Implements tools for performing file system operations such as reading, writing, searching, and listing files.
-   **`state/`**: This directory manages the agent's state and persistence.
    -   **`task_state.py`**: Defines the `TaskState` class for tracking the state of a task throughout its execution.
    -   **`storage/`**: Contains modules for state storage implementations (e.g., JSON, SQLite).
    -   **`config.py`**: Defines configuration classes for state storage.
-   **`debug/`**: Includes modules for debugging the agent's behavior.
    -   **`debug_session.py`**: Manages debug sessions, breakpoints, and step-by-step execution control.
    -   **`debug_callback.py`**: Defines interfaces for debug event callbacks.
-   **`logging/`**: Configures logging for the agent, allowing for detailed tracking of agent activities.

## Key Classes and Interfaces

-   **`Agent` (agent.py)**
    -   Central orchestrator for task execution.
    -   Manages task lifecycle, LLM interaction, and tool execution.
    -   Key methods:
        -   `execute_task(task: str, debug_callback: Optional[DebugCallback] = None)`: Executes a task.
        -   `register_tool(tool: BaseTool)`: Registers a new tool.
-   **`AgentConfig` (config.py)**
    -   Configuration container for the agent.
    -   Organizes settings for debugging, logging, LLM provider, tools, and state storage.
-   **`BaseLLMProvider` (llm/base.py)**
    -   Abstract base class for LLM provider implementations.
    -   Defines the interface for interacting with language models.
    -   Abstract methods:
        -   `get_next_action(...)`: Determines the next action for the agent.
        -   `format_prompt(...)`: Formats prompts for the LLM.
        -   `parse_response(...)`: Parses LLM responses into `LLMAction` objects.
-   **`OpenAIProvider` (llm/openai.py)**
    -   Example implementation of `BaseLLMProvider` for OpenAI. (Mock implementation)
-   **`BaseTool` (tools/base.py)**
    -   Abstract base class for tool implementations.
    -   Defines the interface for tools that the agent can use.
    -   Abstract methods:
        -   `execute(args: Dict[str, Any])`: Executes the tool's logic.
-   **`TaskState` (state/task_state.py)**
    -   Manages the state of a task, including current status, tool results, and history.

## Getting Started

1.  **Installation**:
    ```bash
    pip install -e .
    ```
2.  **Configuration**: 
    -   Create an instance of `AgentConfig` in your application code.
    -   Provide necessary configurations such as API keys, debugging preferences, and state storage settings.
3.  **Agent Instantiation**:
    -   Initialize the `Agent` with your `AgentConfig` instance.
4.  **Task Execution**:
    -   Use `agent.execute_task(task_description)` to start the agent on a given task.

## Extending the Agent

### Adding New Tools

1.  Create a new Python file in the `tools/` directory (e.g., `my_tool.py`).
2.  Define a new tool class that inherits from `BaseTool`.
3.  Implement the `execute(self, args: Dict[str, Any])` method to define the tool's functionality.
4.  Optionally, define argument validation and user approval logic.
5.  Register your new tool with the `Agent` instance, either directly or by including it in the default tools list in `tools/__init__.py`.

### Adding New LLM Providers

1.  Create a new Python file in the `llm/` directory (e.g., `my_llm_provider.py`).
2.  Define a new LLM provider class that inherits from `BaseLLMProvider`.
3.  Implement the abstract methods (`get_next_action`, `format_prompt`, `parse_response`) to integrate with your chosen LLM API.
4.  Update the `create_llm_provider` function in `llm/__init__.py` to include your new provider as an option.

## Debugging and State Management

-   **Debugging**: Enable debug mode in `AgentConfig` and configure breakpoints to step through task execution. Use a `DebugCallback` to receive real-time debug information.
-   **State Management**: Configure state storage in `AgentConfig` to use JSON files or SQLite for persistence. Task checkpoints are automatically managed if enabled.

By following this guide, developers can effectively understand, utilize, and extend the `llm_agent` package to build sophisticated AI agents for various applications.
