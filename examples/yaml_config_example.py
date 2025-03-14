"""Example demonstrating how to use YAML configuration with the LLM Agent"""

import asyncio
from pathlib import Path

from termcolor import colored

from llm_agent.agent import Agent
from llm_agent.config import AgentConfig


async def main() -> None:
    """Run a task using YAML configuration"""
    print(colored("\nInitializing Agent with YAML Configuration", "cyan"))
    print("=" * 80)

    # Load configuration from YAML
    config_path = Path(__file__).parent.parent / "config.yaml"
    config = AgentConfig.from_yaml(str(config_path))

    # Create agent instance
    agent = Agent(config)

    print(colored("\nStarting Task Sequence", "cyan"))
    print("=" * 80)

    # Example task
    task = """Create a Python script that:
    1. Reads a CSV file
    2. Calculates the average of a numeric column
    3. Writes the result to a new file
    """

    print(colored("\nExecuting Task...", "yellow"))
    result = await agent.execute_task(task)
    print(colored(f"Task Completed\nResult: {result}\n", "green"))

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
        import traceback

        traceback_str = traceback.format_exc()
        print(colored(f"\nError: {str(e)}", "red"))
        print(colored(f"Traceback:\n{traceback_str}", "red"))
