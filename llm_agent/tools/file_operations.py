"""
File operation tools
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import aiofiles
from pydantic import BaseModel

from .base import BaseTool, ToolResult

class FileToolArguments(BaseModel):
    """Base arguments for file operation tools"""
    path: str

class ReadFileArguments(FileToolArguments):
    """Arguments for ReadFileTool"""
    pass

class WriteFileArguments(FileToolArguments):
    """Arguments for WriteFileTool"""
    content: str
    create_dirs: bool = True

class SearchFilesArguments(BaseModel):
    """Arguments for SearchFilesTool"""
    directory: str
    pattern: str
    recursive: bool = True

class ListFilesArguments(BaseModel):
    """Arguments for ListFilesTool"""
    directory: str
    recursive: bool = False

class ReadFileTool(BaseTool):
    """Tool for reading file contents"""
    
    def __init__(self):
        super().__init__(
            name="read_file",
            description="Read contents of a file at the specified path"
        )

    async def execute(self, args: Dict[str, Any]) -> ToolResult:
        try:
            arguments = ReadFileArguments(**args)
            path = Path(arguments.path)

            if not path.exists():
                return ToolResult(
                    success=False,
                    message=f"File not found: {path}",
                    data=None
                )

            async with aiofiles.open(path, mode='r') as f:
                content = await f.read()

            return ToolResult(
                success=True,
                message="File read successfully",
                data=content
            )
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Failed to read file: {str(e)}",
                data=None
            )

class WriteFileTool(BaseTool):
    """Tool for writing content to files"""
    
    def __init__(self):
        super().__init__(
            name="write_file",
            description="Write content to a file at the specified path"
        )

    async def execute(self, args: Dict[str, Any]) -> ToolResult:
        try:
            arguments = WriteFileArguments(**args)
            path = Path(arguments.path)

            if arguments.create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(path, mode='w') as f:
                await f.write(arguments.content)

            return ToolResult(
                success=True,
                message=f"Content written to {path}",
                data=None
            )
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Failed to write file: {str(e)}",
                data=None
            )

class SearchFilesTool(BaseTool):
    """Tool for searching files"""
    
    def __init__(self):
        super().__init__(
            name="search_files",
            description="Search for files matching a pattern"
        )

    async def execute(self, args: Dict[str, Any]) -> ToolResult:
        try:
            arguments = SearchFilesArguments(**args)
            directory = Path(arguments.directory)
            
            if not directory.exists():
                return ToolResult(
                    success=False,
                    message=f"Directory not found: {directory}",
                    data=None
                )

            matches = []
            pattern = arguments.pattern

            if arguments.recursive:
                for root, _, files in os.walk(directory):
                    for file in files:
                        if pattern in file:
                            matches.append(str(Path(root) / file))
            else:
                matches = [
                    str(f) for f in directory.glob(pattern)
                    if f.is_file()
                ]

            return ToolResult(
                success=True,
                message=f"Found {len(matches)} matches",
                data=matches
            )
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Search failed: {str(e)}",
                data=None
            )

class ListFilesTool(BaseTool):
    """Tool for listing files in a directory"""
    
    def __init__(self):
        super().__init__(
            name="list_files",
            description="List files in a directory"
        )

    async def execute(self, args: Dict[str, Any]) -> ToolResult:
        try:
            arguments = ListFilesArguments(**args)
            directory = Path(arguments.directory)
            
            if not directory.exists():
                return ToolResult(
                    success=False,
                    message=f"Directory not found: {directory}",
                    data=None
                )

            files: List[str] = []
            
            if arguments.recursive:
                for root, _, filenames in os.walk(directory):
                    for filename in filenames:
                        files.append(str(Path(root) / filename))
            else:
                files = [str(f) for f in directory.iterdir() if f.is_file()]

            return ToolResult(
                success=True,
                message=f"Listed {len(files)} files",
                data=files
            )
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Failed to list files: {str(e)}",
                data=None
            )
