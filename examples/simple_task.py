"""
Simple example of using the LLM Agent
"""
import asyncio
from pathlib import Path
import os
from dotenv import load_dotenv

from llm_agent import Agent, AgentConfig

async def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    # Configure the agent
    config = AgentConfig(
        llm_provider="openai",
        api_key=api_key,
        working_directory=Path.cwd(),
        auto_approve_tools=True  # For demonstration only
    )

    # Create agent instance
    agent = Agent(config)

    # Execute a simple task
    result = await agent.execute_task(
        "Create a simple Python function that calculates the factorial of a number"
    )
    
    print("\nTask completed!")
    print("Result:", result)

if __name__ == "__main__":
    asyncio.run(main())
