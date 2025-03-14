"""Simple task example demonstrating memory and debug features"""

import asyncio
import os
from pathlib import Path

from termcolor import colored

from llm_agent.agent import Agent
from llm_agent.callbacks import ConsoleApprovalCallback
from llm_agent.config import AgentConfig, BreakpointConfig, DebugSettings
from llm_agent.debug import BreakpointType
from llm_agent.logging import LogConfig, TyperLogger
from llm_agent.state.config import StateStorageConfig
from dotenv import load_dotenv

load_dotenv()

async def main() -> None:
    """Run a simple task with enhanced debugging"""
    # Configure logging with TyperLogger
    log_config = LogConfig(
        level="DEBUG",
        file_path=Path.cwd() / ".llm_agent" / "logs" / "agent.log",
        console_logging=True,
        file_logging=True,
        use_colors=True,
        show_separators=True,
        format="%(asctime)s - %(name)s - %(levelname)s\n%(message)s",
    )

    # Create TyperLogger instance
    logger = TyperLogger("agent", log_config)
    logger.show_panel("Initializing Agent", "Setting up with enhanced debugging", style="cyan")

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
        base_url=os.environ["OPENAI_BASE_URL"],
        working_directory=Path.cwd(),
        state_storage=StateStorageConfig(
            type="json",
            auto_checkpoint=True,
            max_checkpoints=10,
        ),
        rate_limit=9,
        auto_approve_tools=False,  # Disable auto-approval to demonstrate callback
        max_consecutive_auto_approvals=5,
        debug=debug_settings,
        logging=log_config,
    )

    # Create a custom approval callback
    approval_callback = ConsoleApprovalCallback()
    
    # Initialize agent with the callback
    agent = Agent(config, approval_callback=approval_callback)

    logger.show_panel("Starting Task Sequence", "Initializing task execution", style="yellow")

    setup_task = """Write a python script to draw a circle with random radius from 1 to 10
    """

    logger.start_task("Executing Setup Task...")
    result = await agent.execute_task(setup_task)
    logger.end_task("Setup Task Completed", success=True)
    logger.show_panel("Task Result", str(result), style="green")

    # Demonstrate memory features
    logger.show_panel("Memory Features", "Demonstrating task history and related tasks", style="cyan")

    logger.start_task("Searching Task History...")
    history = await agent.search_task_history("CSV")
    logger.end_task("Task History Search Complete", success=True)

    for task in history:
        logger.show_table(
            "Found Task",
            {
                "Description": task["task"],
                "Relevance": task["relevance"],
                "Status": "Completed" if task["completed"] else "In Progress",
            }
        )

    logger.start_task("Getting Related Tasks...")
    related = await agent.get_related_tasks(limit=3)
    logger.end_task("Related Tasks Retrieved", success=True)

    for task in related:
        status = "Completed" if task["completed"] else "In Progress"
        logger.show_table(
            "Related Task",
            {
                "Description": task["task"],
                "Similarity": f"{task['similarity']:.2f}",
                "Status": status,
            }
        )

    logger.show_panel("Task Complete", "All operations finished successfully", style="green")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(colored("\nTask interrupted by user", "red"))
    except Exception as e:
        import traceback

        traceback_str = traceback.format_exc()
        print(colored(f"\nError: {str(e)}", "red"))
        print(colored(f"Traceback:\n{traceback_str}", "red"))
