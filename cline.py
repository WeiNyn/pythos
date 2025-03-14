"""
Cline CLI Application

A command-line interface for the Cline LLM Agent Framework.
"""

import asyncio
import os
from pathlib import Path
from typing import Optional
import traceback

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.traceback import install as install_rich_traceback

from llm_agent.agent import Agent
from llm_agent.callbacks import ConsoleApprovalCallback
from llm_agent.config import AgentConfig, DebugSettings, BreakpointConfig
from llm_agent.debug import BreakpointType
from llm_agent.logging import LogConfig, TyperLogger
from llm_agent.state.config import StateStorageConfig
from dotenv import load_dotenv

# Install rich traceback handler
install_rich_traceback(show_locals=True)

load_dotenv()
# Initialize Typer app
app = typer.Typer(
    name="cline",
    help="Cline LLM Agent Framework CLI",
    add_completion=False,
)

# Initialize Rich console
console = Console()

def display_error(error: Exception, context: str = "Task execution failed"):
    """Display error with rich formatting"""
    console.print(f"\n[bold red]Error: {context}[/bold red]")
    console.print(Panel(
        str(error),
        title="Error Details",
        border_style="red",
        title_align="left"
    ))
    
    # Show traceback in a panel
    console.print(Panel(
        "".join(traceback.format_exception(type(error), error, error.__traceback__)),
        title="Traceback",
        border_style="red",
        title_align="left"
    ))

def load_config(config_path: Path) -> AgentConfig:
    """Load configuration from YAML file"""
    import yaml
    
    if not config_path.exists():
        console.print(f"[red]Error: Config file not found at {config_path}[/red]")
        raise typer.Exit(1)
    
    try:
        return AgentConfig.from_yaml(config_path)
    except yaml.YAMLError as e:
        console.print(f"[red]Error: Invalid YAML configuration: {str(e)}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: Failed to load configuration: {str(e)}[/red]")
        raise typer.Exit(1)

def display_welcome():
    """Display welcome message"""
    console.print(Panel.fit(
        "[bold cyan]Welcome to Cline LLM Agent Framework[/bold cyan]\n"
        "An interactive CLI for executing tasks with LLM-powered agents.",
        title="Cline CLI",
        border_style="cyan"
    ))

def display_task_history(agent: Agent):
    """Display recent task history"""
    console.print("\n[bold cyan]Recent Tasks:[/bold cyan]")
    
    try:
        # Get recent tasks
        tasks = asyncio.run(agent.search_task_history("", limit=5))
        
        if not tasks:
            console.print("[dim]No recent tasks found[/dim]")
            return
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Task ID", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Status", style="green")
        table.add_column("Duration", style="yellow")
        
        for task in tasks:
            status = "✓" if task["completed"] else "✗"
            status_color = "green" if task["completed"] else "red"
            duration = task.get("summary", {}).get("duration", "N/A")
            
            table.add_row(
                task["task_id"][:8],
                task["task"][:50] + "..." if len(task["task"]) > 50 else task["task"],
                f"[{status_color}]{status}[/{status_color}]",
                str(duration)
            )
        
        console.print(table)
    except Exception as e:
        display_error(e, "Failed to display task history")
        console.print("[yellow]Continuing with task input...[/yellow]")

def get_task_input() -> Optional[str]:
    """Get task input from user"""
    console.print("\n[bold cyan]Enter your task:[/bold cyan]")
    console.print("[dim]Press Ctrl+C to exit[/dim]")
    
    try:
        task = Prompt.ask("Task")
        return task.strip() if task else None
    except KeyboardInterrupt:
        return None
    except Exception as e:
        display_error(e, "Failed to get task input")
        return None

def display_task_result(result: any):
    """Display task result"""
    console.print("\n[bold cyan]Task Result:[/bold cyan]")
    console.print(Panel(str(result), title="Result", border_style="green"))

@app.command()
def run(
    config_path: Path = typer.Option(
        "config.yml",
        "--config",
        "-c",
        help="Path to configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
):
    """Run the Cline CLI in interactive mode"""
    try:
        # Load configuration
        config = load_config(config_path)
        
        # Initialize logger
        logger = TyperLogger("cline", LogConfig(
            level="INFO",
            console_logging=True,
            file_logging=True,
            use_colors=True,
            show_separators=True
        ))
        
        # Initialize agent
        agent = Agent(config, approval_callback=ConsoleApprovalCallback())
        
        # Display welcome message
        display_welcome()
        
        while True:
            try:
                # Display task history
                display_task_history(agent)
                
                # Get task input
                task = get_task_input()
                if task is None:
                    break
                
                # Execute task
                try:
                    logger.start_task("Executing task...")
                    result = asyncio.run(agent.execute_task(task))
                    logger.end_task("Task completed", success=True)
                    display_task_result(result)
                except Exception as e:
                    logger.error(f"Task execution failed: {str(e)}")
                    display_error(e, "Task execution failed")
                    if Confirm.ask("[yellow]Would you like to try again?[/yellow]"):
                        continue
                    break
                
                # Ask if user wants to continue
                if not Confirm.ask("\n[cyan]Would you like to execute another task?[/cyan]"):
                    break
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]Operation interrupted by user[/yellow]")
                break
            except Exception as e:
                display_error(e, "Unexpected error occurred")
                if not Confirm.ask("[yellow]Would you like to continue?[/yellow]"):
                    break
        
        console.print("\n[green]Thank you for using Cline![/green]")
        
    except Exception as e:
        display_error(e, "Fatal error occurred")
        raise typer.Exit(1)

if __name__ == "__main__":
    app() 