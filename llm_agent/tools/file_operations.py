"""
File operation tools implementation
"""

import os
from pathlib import Path
from typing import Any, Dict

from .base import BaseTool, ToolResult


class ReadFileTool(BaseTool):
    """Tool to read file contents"""

    async def _execute(self, args: Dict[str, Any]) -> ToolResult:
        """
        Read contents of a file

        Args:
            path: Path to the file to read

        Returns:
            ToolResult containing the file contents
        """
        path = args.get("path")
        if not path:
            return ToolResult(success=False, message="No path provided", data=None)

        try:
            file_path = Path(path)
            if not file_path.exists():
                return ToolResult(
                    success=False, message=f"File not found: {path}", data=None
                )

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            return ToolResult(
                success=True, message=f"Successfully read file: {path}", data=content
            )

        except Exception as e:
            return ToolResult(
                success=False, message=f"Error reading file: {str(e)}", data=None
            )


class WriteFileTool(BaseTool):
    """Tool to write content to a file with optional directory creation"""

    async def _execute(self, args: Dict[str, Any]) -> ToolResult:
        """
        Write content to a file

        Args:
            path: Path to write the file to
            content: Content to write
            create_dirs: Create parent directories if needed (default: True)

        Returns:
            ToolResult indicating success/failure
        """
        path = args.get("path")
        content = args.get("content")
        create_dirs = args.get("create_dirs", True)

        if not path or content is None:
            return ToolResult(
                success=False, message="Both path and content are required", data=None
            )

        try:
            file_path = Path(path)
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(str(content))

            return ToolResult(
                success=True, message=f"Successfully wrote to file: {path}", data=None
            )

        except Exception as e:
            return ToolResult(
                success=False, message=f"Error writing file: {str(e)}", data=None
            )


class SearchFilesTool(BaseTool):
    """Tool to search for files matching a pattern in a directory"""

    async def _execute(self, args: Dict[str, Any]) -> ToolResult:
        """
        Search for files matching pattern

        Args:
            directory: Directory to search in
            pattern: Pattern to match files against
            recursive: Search in subdirectories (default: True)

        Returns:
            ToolResult containing matching file paths
        """
        directory = args.get("directory", ".")
        pattern = args.get("pattern")
        recursive = args.get("recursive", True)

        if not pattern:
            return ToolResult(success=False, message="Pattern is required", data=None)

        try:
            base_path = Path(directory)
            if not base_path.exists():
                return ToolResult(
                    success=False,
                    message=f"Directory not found: {directory}",
                    data=None,
                )

            # Build search pattern
            search_path = f"**/{pattern}" if recursive else pattern
            matches = list(base_path.glob(search_path))

            # Convert to relative paths
            relative_matches = [str(p.relative_to(base_path)) for p in matches]

            return ToolResult(
                success=True,
                message=f"Found {len(matches)} matches",
                data=relative_matches,
            )

        except Exception as e:
            return ToolResult(
                success=False, message=f"Error searching files: {str(e)}", data=None
            )


class ListFilesTool(BaseTool):
    """Tool to list files in a directory with optional recursion"""

    async def _execute(self, args: Dict[str, Any]) -> ToolResult:
        """
        List files in directory

        Args:
            directory: Directory to list files from
            recursive: List files recursively (default: False)

        Returns:
            ToolResult containing file list
        """
        directory = args.get("directory", ".")
        recursive = args.get("recursive", False)

        try:
            base_path = Path(directory)
            if not base_path.exists():
                return ToolResult(
                    success=False,
                    message=f"Directory not found: {directory}",
                    data=None,
                )

            files = []
            if recursive:
                for root, _, filenames in os.walk(base_path):
                    root_path = Path(root)
                    for filename in filenames:
                        file_path = root_path / filename
                        files.append(str(file_path.relative_to(base_path)))
            else:
                files = [
                    str(p.relative_to(base_path))
                    for p in base_path.iterdir()
                    if p.is_file()
                ]

            return ToolResult(
                success=True, message=f"Listed {len(files)} files", data=sorted(files)
            )

        except Exception as e:
            return ToolResult(
                success=False, message=f"Error listing files: {str(e)}", data=None
            )
