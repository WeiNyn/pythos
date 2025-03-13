"""Simple task example demonstrating memory and debug features"""

import asyncio
import os
from pathlib import Path

from termcolor import colored

from llm_agent.agent import Agent
from llm_agent.config import AgentConfig, BreakpointConfig, DebugSettings
from llm_agent.debug import BreakpointType
from llm_agent.logging import LogConfig
from llm_agent.state.config import StateStorageConfig


async def main() -> None:
    """Run a simple task with enhanced debugging"""
    print(colored("\nInitializing Agent with Debug Features", "cyan"))
    print("=" * 80)

    # Configure logging
    log_config = LogConfig(
        level="DEBUG",
        file_path=Path.cwd() / ".llm_agent" / "logs" / "agent.log",
        console_logging=True,
        file_logging=True,
        use_colors=True,
        show_separators=True,
        format="%(asctime)s - %(name)s - %(levelname)s\n%(message)s",
    )

    # Configure debug settings
    debug_settings = DebugSettings(
        enabled=True,
        step_by_step=False,
        breakpoints={
            "tool_execution": BreakpointConfig(
                type=BreakpointType.TOOL,
                enabled=True,
            )
        },
    )

    config = AgentConfig(
        llm_provider="openai",
        api_key=os.environ["OPENAI_API_KEY"],
        working_directory=Path.cwd(),
        state_storage=StateStorageConfig(
            type="json",  # Using SQLite for better query support
            # path=None,  # Default to working_directory/.llm_agent/state
            auto_checkpoint=True,
            max_checkpoints=10,
        ),
        rate_limit=60,
        auto_approve_tools=True,
        max_consecutive_auto_approvals=5,
        debug=debug_settings,
        logging=log_config,
    )

    agent = Agent(config)

    print(colored("\nStarting Task Sequence", "cyan"))
    print("=" * 80)

    setup_task = """Create a python script that:
    1. receives a number as input
    2. calculates the square of the number
    3. print a rectangle, square or triangle that has the area equal to
       the square of the number"""

    print(colored("\nExecuting Setup Task...", "yellow"))
    result = await agent.execute_task(setup_task)
    print(colored(f"Setup Task Completed\nResult: {result}\n", "green"))

    #     # First task to establish context
    #     setup_task = """Create a Python utility module that:
    # 1. Has functions for CSV data processing
    # 2. Includes type hints and docstrings
    # 3. Has proper error handling
    # 4. Is well-organized and reusable"""

    #     print(colored("\nExecuting Setup Task...", "yellow"))
    #     result = await agent.execute_task(setup_task)
    #     print(colored(f"Setup Task Completed\nResult: {result}\n", "green"))

    #     # Second task that builds on the first
    #     processing_task = """Using the utility module we just created:
    # 1. Create a script that processes a sample CSV file
    # 2. Add input validation
    # 3. Include error reporting
    # 4. Show example usage"""

    #     print(colored("\nExecuting Processing Task...", "yellow"))
    #     result = await agent.execute_task(processing_task)
    #     print(colored(f"Processing Task Completed\nResult: {result}\n", "green"))

    # Demonstrate memory features
    print(colored("\nDemonstrating Memory Features", "cyan"))
    print("=" * 80)

    print("\nSearching Task History...")
    history = await agent.search_task_history("CSV")
    for task in history:
        print(colored("\nFound Task:", "magenta"))
        print(f"- Description: {task['task']}")
        print(f"- Relevance: {task['relevance']}")
        print(f"- Status: {'Completed' if task['completed'] else 'In Progress'}")

    print("\nGetting Related Tasks...")
    related = await agent.get_related_tasks(limit=3)
    for task in related:
        status = "Completed" if task["completed"] else "In Progress"
        print(colored("\nRelated Task:", "magenta"))
        print(f"- Description: {task['task']}")
        print(f"- Similarity: {task['similarity']:.2f}")
        print(f"- Status: {status}")

    print("\nDone!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(colored("\nTask interrupted by user", "red"))
    except Exception as e:
        print(colored(f"\nError: {str(e)}", "red"))
