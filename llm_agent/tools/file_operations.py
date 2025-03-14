"""
File operation tools implementation
"""

import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

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
                return ToolResult(success=False, message=f"File not found: {path}", data=None)

            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            return ToolResult(success=True, message=f"Successfully read file: {path}", data=content)

        except Exception as e:
            return ToolResult(success=False, message=f"Error reading file: {str(e)}", data=None)

    def get_example(self) -> str:
        """Get example usage for ReadFileTool"""
        return """
<ReadFileTool>
<args>
    <path>src/main.py</path>
</args>
</ReadFileTool>"""

    def get_parameters_description(self) -> List[Tuple[str, str]]:
        """Get parameter descriptions for ReadFileTool"""
        return [("path", "Path to the file to read (relative or absolute)")]


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
            return ToolResult(success=False, message="Both path and content are required", data=None)

        try:
            file_path = Path(path)
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(str(content))

            return ToolResult(success=True, message=f"Successfully wrote to file: {path}", data=None)

        except Exception as e:
            return ToolResult(success=False, message=f"Error writing file: {str(e)}", data=None)

    def get_example(self) -> str:
        """Get example usage for WriteFileTool"""
        return """
<WriteFileTool>
<args>
    <path>src/output.txt</path>
    <content>![CDATA[Hello, world!]]></content>
    <create_dirs>true</create_dirs>
</args>
</WriteFileTool>"""

    def get_parameters_description(self) -> List[Tuple[str, str]]:
        """Get parameter descriptions for WriteFileTool"""
        return [
            ("path", "Path to write the file to (relative or absolute)"),
            ("content", "Content to write to the file"),
            (
                "create_dirs",
                "Create parent directories if they don't exist (default: true)",
            ),
        ]


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
            return ToolResult(success=False, message=f"Error searching files: {str(e)}", data=None)

    def get_example(self) -> str:
        """Get example usage for SearchFilesTool"""
        return """
<SearchFilesTool>
<args>
    <directory>src</directory>
    <pattern>*.py</pattern>
    <recursive>true</recursive>
</args>
</SearchFilesTool>"""

    def get_parameters_description(self) -> List[Tuple[str, str]]:
        """Get parameter descriptions for SearchFilesTool"""
        return [
            ("directory", "Directory to search in (default: current directory)"),
            ("pattern", "Glob pattern to match files against (e.g., *.py)"),
            ("recursive", "Search in subdirectories (default: true)"),
        ]


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
                files = [str(p.relative_to(base_path)) for p in base_path.iterdir() if p.is_file()]

            return ToolResult(success=True, message=f"Listed {len(files)} files", data=sorted(files))

        except Exception as e:
            return ToolResult(success=False, message=f"Error listing files: {str(e)}", data=None)

    def get_example(self) -> str:
        """Get example usage for ListFilesTool"""
        return """
<ListFilesTool>
<args>
    <directory>src</directory>
    <recursive>false</recursive>
</args>
</ListFilesTool>"""

    def get_parameters_description(self) -> List[Tuple[str, str]]:
        """Get parameter descriptions for ListFilesTool"""
        return [
            ("directory", "Directory to list files from (default: current directory)"),
            (
                "recursive",
                "List files recursively including subdirectories (default: false)",
            ),
        ]


class ReplaceInFileTool(BaseTool):
    """Tool to make targeted replacements in a file using git-like comparison markers"""

    async def _execute(self, args: Dict[str, Any]) -> ToolResult:
        """
        Replace content in a file using git-like comparison markers

        Args:
            path: Path to the file to modify
            content: The replacement content in git-like format with markers:
                     <<<<<<< SEARCH
                     [exact content to find]
                     =======
                     [new content to replace with]
                     >>>>>>> REPLACE
            count: Maximum number of replacements to make (default: 0 for all)

        Returns:
            ToolResult indicating success/failure and number of replacements made
        """
        path = args.get("path")
        content = args.get("content")
        count = int(args.get("count", 0))  # 0 means replace all occurrences

        if not path or not content:
            return ToolResult(
                success=False,
                message="Required parameters: path and content",
                data=None,
            )

        try:
            file_path = Path(path)
            if not file_path.exists():
                return ToolResult(success=False, message=f"File not found: {path}", data=None)

            # Read the original content
            with open(file_path, encoding="utf-8") as f:
                original_content = f.read()

            # Parse the replacement format to extract search and replace content
            import re

            pattern = r"<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE"
            matches = re.findall(pattern, content, re.DOTALL)

            if not matches:
                return ToolResult(
                    success=False,
                    message="Invalid replacement format. Use git-like comparison markers.",
                    data=None,
                )

            search_text, replacement_text = matches[0]

            # Perform the replacement
            if count > 0:
                # Split by search_text and join with replacement_text for limited count
                parts = original_content.split(search_text, count + 1)
                if len(parts) <= 1:
                    # No matches found
                    return ToolResult(
                        success=True,
                        message=f"Search text not found in file: {path}",
                        data={"replacements_made": 0},
                    )

                # Perform the replacement for the specified count
                new_content = replacement_text.join(parts[:count]) + replacement_text + search_text.join(parts[count:])
                num_replacements = min(count, len(parts) - 1)
            else:
                # Replace all occurrences
                new_content = original_content.replace(search_text, replacement_text)
                num_replacements = original_content.count(search_text)

            if num_replacements == 0:
                return ToolResult(
                    success=True,
                    message=f"Search text not found in file: {path}",
                    data={"replacements_made": 0},
                )

            # Write the modified content back
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return ToolResult(
                success=True,
                message=f"Successfully replaced {num_replacements} occurrences in file: {path}",
                data={"replacements_made": num_replacements},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Error replacing content in file: {str(e)}",
                data=None,
            )

    def get_example(self) -> str:
        """Get example usage for ReplaceInFileTool"""
        return """
<ReplaceInFileTool>
<args>
    <path>src/main.py</path>
    <content><![CDATA[<<<<<<< SEARCH
def old_function():
    return "old"
=======
def new_function():
    return "new"
>>>>>>> REPLACE]]></content>
    <count>1</count>
</args>
</ReplaceInFileTool>"""

    def get_parameters_description(self) -> List[Tuple[str, str]]:
        """Get parameter descriptions for ReplaceInFileTool"""
        return [
            ("path", "Path to the file to modify (relative or absolute)"),
            (
                "content",
                "Replacement content using git-like comparison markers:\n"
                "<<<<<<< SEARCH\n"
                "[exact content to find]\n"
                "=======\n"
                "[new content to replace with]\n"
                ">>>>>>> REPLACE",
            ),
            (
                "count",
                "Maximum number of replacements to make (default: 0 for all matches)",
            ),
        ]


class RunCommandLineTool(BaseTool):
    """Tool to run command line operations and detect source code modifications"""

    def __init__(self) -> None:
        """Initialize tool with file tracking capability"""
        super().__init__()
        self.source_extensions = {
            ".py",
            ".js",
            ".ts",
            ".html",
            ".css",
            ".md",
            ".json",
            ".xml",
            ".yaml",
            ".yml",
        }

    async def _execute(self, args: Dict[str, Any]) -> ToolResult:
        """
        Run a command line operation and detect if source code was modified

        Args:
            command: Command to execute
            working_dir: Working directory for the command (default: current dir)
            track_files: Whether to track file modifications (default: true)

        Returns:
            ToolResult with command output and source modification status
        """
        command = args.get("command")
        working_dir = args.get("working_dir", ".")
        track_files = args.get("track_files", True)

        if not command:
            return ToolResult(success=False, message="Command is required", data=None)

        try:
            # Convert working_dir to Path object
            work_dir = Path(working_dir)
            if not work_dir.exists():
                return ToolResult(
                    success=False,
                    message=f"Working directory not found: {working_dir}",
                    data=None,
                )

            # Snapshot files before command execution if tracking is enabled
            files_before = self._get_source_files(work_dir) if track_files else set()
            modified_times_before = self._get_file_mtimes(files_before) if track_files else {}

            # Execute the command
            process = subprocess.run(command, shell=True, cwd=str(work_dir), capture_output=True, text=True)

            # Get command output
            stdout = process.stdout
            stderr = process.stderr
            return_code = process.returncode

            # Check for modified files if tracking is enabled
            modified_files = []
            if track_files:
                files_after = self._get_source_files(work_dir)
                modified_times_after = self._get_file_mtimes(files_after)

                # Detect new files
                new_files = files_after - files_before
                modified_files.extend([str(f.relative_to(work_dir)) for f in new_files])

                # Detect modified files
                for file in files_before & files_after:
                    if modified_times_after.get(file) != modified_times_before.get(file):
                        modified_files.append(str(file.relative_to(work_dir)))

            # Prepare result data
            result_data = {
                "stdout": stdout,
                "stderr": stderr,
                "return_code": return_code,
                "modified_source_code": bool(modified_files),
                "modified_files": sorted(modified_files) if modified_files else [],
            }

            if return_code == 0:
                result_message = "Command executed successfully"
                if modified_files:
                    result_message += f", modified {len(modified_files)} source files"
            else:
                result_message = f"Command failed with exit code {return_code}"

            return ToolResult(success=return_code == 0, message=result_message, data=result_data)

        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Error running command: {str(e)}",
                data={"error": str(e)},
            )

    def _get_source_files(self, directory: Path) -> Set[Path]:
        """Get all source code files in the directory"""
        result = set()
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in self.source_extensions:
                    result.add(file_path)
        return result

    def _get_file_mtimes(self, files: Set[Path]) -> Dict[Path, float]:
        """Get modification times for a set of files"""
        result = {}
        for file in files:
            if file.exists():
                result[file] = file.stat().st_mtime
        return result

    def get_example(self) -> str:
        """Get example usage for RunCommandLineTool"""
        return """
<RunCommandLineTool>
<args>
    <command>pip install requests</command>
    <working_dir>.</working_dir>
    <track_files>true</track_files>
</args>
</RunCommandLineTool>"""

    def get_parameters_description(self) -> List[Tuple[str, str]]:
        """Get parameter descriptions for RunCommandLineTool"""
        return [
            ("command", "The command line operation to execute"),
            (
                "working_dir",
                "Working directory for the command (default: current directory)",
            ),
            ("track_files", "Whether to track file modifications (default: true)"),
        ]
