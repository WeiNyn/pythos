"""Simple task example demonstrating memory features"""
import os
import asyncio
from pathlib import Path
from llm_agent.agent import Agent
from llm_agent.config import AgentConfig
from llm_agent.state.config import StateStorageConfig

async def main():
    """Run a simple task with memory features"""
    config = AgentConfig(
        llm_provider="openai",
        api_key=os.environ["OPENAI_API_KEY"],
        working_directory=Path.cwd(),
        state_storage=StateStorageConfig(
            type="json",  # Using SQLite for better query support
            # path=None,  # Default to working_directory/.llm_agent/state
            auto_checkpoint=True,
            max_checkpoints=50
        ),
        rate_limit=10,
        auto_approve_tools=True,
        max_consecutive_auto_approvals=50
    )

    agent = Agent(config)

    # First task to establish context
    setup_task = """Create a Python utility module that:
1. Has functions for CSV data processing
2. Includes type hints and docstrings
3. Has proper error handling
4. Is well-organized and reusable"""

    print("\nExecuting setup task...")
    result = await agent.execute_task(setup_task)
    print(f"Setup task completed: {result}")

    # Second task that builds on the first
    processing_task = """Using the utility module we just created:
1. Create a script that processes a sample CSV file
2. Add input validation
3. Include error reporting
4. Show example usage"""

    print("\nExecuting processing task...")
    result = await agent.execute_task(processing_task)
    print(f"Processing task completed: {result}")

    # Demonstrate memory features
    print("\nSearching task history...")
    history = await agent.search_task_history("CSV")
    for task in history:
        print(f"Found task: {task['task']} (Relevance: {task['relevance']})")

    print("\nGetting related tasks...")
    related = await agent.get_related_tasks(limit=3)
    for task in related:
        status = "Completed" if task["completed"] else "In Progress"
        print(f"Related task: {task['task']} ({status})")

if __name__ == "__main__":
    asyncio.run(main())
