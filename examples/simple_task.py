"""Simple task example"""
import os
import asyncio
from pathlib import Path
from llm_agent.agent import Agent
from llm_agent.config import AgentConfig
from llm_agent.state.config import StateStorageConfig

async def main():
    """Run a simple task"""
    config = AgentConfig(
        llm_provider="openai",
        api_key=os.environ["OPENAI_API_KEY"],
        working_directory=Path.cwd(),
        state_storage=StateStorageConfig(
            type="json",
            auto_checkpoint=True,
            max_checkpoints=10
        ),
        rate_limit=60,
        auto_approve_tools=True,
        max_consecutive_auto_approvals=5
    )

    agent = Agent(config)
    
    task = """Create a Python script that:
1. Reads data from a CSV file
2. Processes the data (e.g., filtering, transforming)
3. Writes the results to a new CSV file
4. Has proper error handling and type hints"""

    result = await agent.execute_task(task)
    print(f"Task completed with result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
