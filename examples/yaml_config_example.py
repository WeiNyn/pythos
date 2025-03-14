"""Example demonstrating how to use YAML configuration with the LLM Agent"""

import asyncio
import os
from pathlib import Path

import yaml
from termcolor import colored

from llm_agent.agent import Agent
from llm_agent.config import AgentConfig
from llm_agent.debug import BreakpointConfig, BreakpointType
from llm_agent.logging import LogConfig
from llm_agent.state.config import StateStorageConfig
from llm_agent.config import DebugSettings


def load_config(config_path: str) -> AgentConfig:
    """Load and parse the YAML configuration file"""
    with open(config_path, "r") as f:
        config_dict = yaml.safe_load(f)

    # Handle environment variable substitution
    if isinstance(config_dict.get("api_key"), str) and config_dict["api_key"].startswith("${"):
        env_var = config_dict["api_key"][2:-1]  # Remove ${ and }
        config_dict["api_key"] = os.environ.get(env_var)
        if not config_dict["api_key"]:
            raise ValueError(f"Environment variable {env_var} not found")

    # Convert working directory to Path
    if isinstance(config_dict.get("working_directory"), str):
        config_dict["working_directory"] = Path(config_dict["working_directory"]).resolve()

    # Create nested config objects
    config_dict["state_storage"] = StateStorageConfig(**config_dict["state_storage"])
    config_dict["logging"] = LogConfig(**config_dict["logging"])
    
    # Create debug settings
    debug_dict = config_dict["debug"]
    if "breakpoints" in debug_dict:
        for name, bp in debug_dict["breakpoints"].items():
            bp["type"] = BreakpointType(bp["type"])
            debug_dict["breakpoints"][name] = BreakpointConfig(**bp)
    config_dict["debug"] = DebugSettings(**debug_dict)

    return AgentConfig(**config_dict)


async def main() -> None:
    """Run a task using YAML configuration"""
    print(colored("\nInitializing Agent with YAML Configuration", "cyan"))
    print("=" * 80)

    # Load configuration from YAML
    config_path = Path(__file__).parent.parent / "config.yaml"
    config = load_config(str(config_path))
    
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