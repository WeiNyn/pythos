"""
Tests for LLM Agent tools
"""

from pathlib import Path
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from llm_agent.tools.file_operations import (
    ListFilesTool,
    ReadFileTool,
    ReplaceInFileTool,
    RunCommandLineTool,
    SearchFilesTool,
    WriteFileTool,
)


@pytest.fixture
def sample_text() -> str:
    return "Hello, this is a test file.\nIt has multiple lines.\nEnd of file."


@pytest.fixture
def sample_file(temp_dir: Path, sample_text: str) -> Path:
    file_path = temp_dir / "test.txt"
    file_path.write_text(sample_text)
    return file_path


@pytest.fixture
def nested_files(temp_dir: Path) -> Path:
    # Create a nested directory structure with various files
    (temp_dir / "dir1").mkdir()
    (temp_dir / "dir1" / "file1.txt").write_text("File 1")
    (temp_dir / "dir1" / "file2.py").write_text("def test(): pass")

    (temp_dir / "dir2").mkdir()
    (temp_dir / "dir2" / "file3.txt").write_text("File 3")

    return temp_dir


@pytest.mark.asyncio
async def test_read_file_tool(sample_file: Path):
    """Test ReadFileTool functionality"""
    tool = ReadFileTool()

    # Test successful read
    result = await tool.execute({"path": str(sample_file)})
    assert result.success
    assert result.data == sample_file.read_text()

    # Test nonexistent file
    result = await tool.execute({"path": "nonexistent.txt"})
    assert not result.success
    assert "not found" in result.message


@pytest.mark.asyncio
async def test_write_file_tool(temp_dir: Path):
    """Test WriteFileTool functionality"""
    tool = WriteFileTool()
    file_path = temp_dir / "output.txt"
    content = "Test content"

    # Test writing to new file
    result = await tool.execute({"path": str(file_path), "content": content})

    assert result.success
    assert file_path.exists()
    assert file_path.read_text() == content

    # Test writing to nested path
    nested_path = temp_dir / "nested" / "test.txt"
    result = await tool.execute({"path": str(nested_path), "content": content, "create_dirs": True})

    assert result.success
    assert nested_path.exists()
    assert nested_path.read_text() == content


@pytest.mark.asyncio
async def test_search_files_tool(nested_files: Path):
    """Test SearchFilesTool functionality"""
    tool = SearchFilesTool()

    # Test searching for .txt files
    result = await tool.execute({"directory": str(nested_files), "pattern": "*.txt", "recursive": True})

    assert result.success
    assert result.data is not None
    files: List[str] = result.data
    assert len(files) == 2  # Should find 2 .txt files

    # Test searching for Python files
    result = await tool.execute({"directory": str(nested_files), "pattern": "*.py", "recursive": True})

    assert result.success
    assert result.data is not None
    files: List[str] = result.data
    assert len(files) == 1  # Should find 1 .py file


@pytest.mark.asyncio
async def test_list_files_tool(nested_files: Path):
    """Test ListFilesTool functionality"""
    tool = ListFilesTool()

    # Test non-recursive listing
    result = await tool.execute({"directory": str(nested_files), "recursive": False})

    assert result.success
    assert result.data is not None
    files: List[str] = result.data
    assert len(files) == 0  # No files in root, only directories

    # Test recursive listing
    result = await tool.execute({"directory": str(nested_files), "recursive": True})

    assert result.success
    assert result.data is not None
    files: List[str] = result.data
    assert len(files) == 3  # Should find all 3 files

    # Test invalid directory
    result = await tool.execute({"directory": "nonexistent", "recursive": True})

    assert not result.success
    assert "not found" in result.message


@pytest.mark.asyncio
async def test_replace_in_file_tool(temp_dir: Path):
    """Test ReplaceInFileTool functionality"""
    tool = ReplaceInFileTool()

    # Create a test file
    test_file = temp_dir / "replace_test.txt"
    original_content = """function testFunction() {
    console.log('This is a test');
    return 'old value';
}"""
    test_file.write_text(original_content)

    # Test successful replacement with git-style markers
    replacement_content = """<<<<<<< SEARCH
function testFunction() {
    console.log('This is a test');
    return 'old value';
}
=======
function testFunction() {
    console.log('This is a test');
    return 'new value';
}
>>>>>>> REPLACE"""

    result = await tool.execute({"path": str(test_file), "content": replacement_content})

    assert result.success
    assert result.data["replacements_made"] == 1
    assert "new value" in test_file.read_text()
    assert "old value" not in test_file.read_text()

    # Test replacement with count limit
    test_file.write_text("repeat repeat repeat")
    replacement_content = """<<<<<<< SEARCH
repeat
=======
REPLACED
>>>>>>> REPLACE"""

    result = await tool.execute({"path": str(test_file), "content": replacement_content, "count": 2})

    assert result.success
    assert result.data["replacements_made"] == 2
    new_content = test_file.read_text()
    assert new_content == "REPLACED REPLACED repeat"

    # Test replacement not found
    replacement_content = """<<<<<<< SEARCH
not_existing_text
=======
any_replacement
>>>>>>> REPLACE"""

    result = await tool.execute({"path": str(test_file), "content": replacement_content})

    assert result.success  # Tool execution should still succeed even if no replacements were made
    assert result.data["replacements_made"] == 0
    assert "Search text not found" in result.message

    # Test invalid file path
    result = await tool.execute({"path": "nonexistent.txt", "content": replacement_content})

    assert not result.success
    assert "not found" in result.message

    # Test invalid format
    invalid_content = "This is not in the right format"
    result = await tool.execute({"path": str(test_file), "content": invalid_content})

    assert not result.success
    assert "Invalid replacement format" in result.message


@pytest.mark.asyncio
async def test_run_command_line_tool(temp_dir: Path):
    """Test RunCommandLineTool functionality"""
    tool = RunCommandLineTool()

    # Create test files that might be "modified"
    test_py_file = temp_dir / "test.py"
    test_py_file.write_text("print('hello')")
    test_txt_file = temp_dir / "test.txt"
    test_txt_file.write_text("hello")

    # Mock the subprocess.run function to avoid actual command execution
    with patch("subprocess.run") as mock_run:
        # Set up mock return value for command success
        mock_process = MagicMock()
        mock_process.stdout = "Command output"
        mock_process.stderr = ""
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        # Test basic command execution with no file changes
        result = await tool.execute({"command": "echo 'test'", "working_dir": str(temp_dir)})

        assert result.success
        assert result.data["stdout"] == "Command output"
        assert result.data["return_code"] == 0
        assert result.data["modified_source_code"] is False
        assert len(result.data["modified_files"]) == 0

        # Test with file modification detection
        # We'll simulate a modified file by changing its modification time
        # and using our internal mocks to override the detection mechanism
        with patch.object(tool, "_get_file_mtimes") as mock_mtimes:
            # First call returns initial mtimes
            # Second call returns changed mtimes for test.py
            mock_mtimes.side_effect = [
                {test_py_file: 1000, test_txt_file: 2000},  # Initial
                {test_py_file: 1001, test_txt_file: 2000},  # After (test.py changed)
            ]

            result = await tool.execute(
                {
                    "command": "modify file",
                    "working_dir": str(temp_dir),
                    "track_files": True,
                }
            )

            assert result.success
            assert "modified 1 source files" in result.message
            assert result.data["modified_source_code"] is True
            assert len(result.data["modified_files"]) == 1
            assert "test.py" in result.data["modified_files"][0]

        # Test command failure
        mock_process.returncode = 1
        mock_process.stderr = "Command failed"
        mock_run.return_value = mock_process

        result = await tool.execute({"command": "failing_command", "working_dir": str(temp_dir)})

        assert not result.success
        assert result.data["stderr"] == "Command failed"
        assert result.data["return_code"] == 1

        # Test with invalid working directory
        result = await tool.execute({"command": "echo test", "working_dir": "/nonexistent/path"})

        assert not result.success
        assert "not found" in result.message
