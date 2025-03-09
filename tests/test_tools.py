"""
Tests for LLM Agent tools
"""

from pathlib import Path
from typing import List

import pytest

from llm_agent.tools.file_operations import (ListFilesTool, ReadFileTool,
                                             SearchFilesTool, WriteFileTool)


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
    result = await tool.execute(
        {"path": str(nested_path), "content": content, "create_dirs": True}
    )

    assert result.success
    assert nested_path.exists()
    assert nested_path.read_text() == content


@pytest.mark.asyncio
async def test_search_files_tool(nested_files: Path):
    """Test SearchFilesTool functionality"""
    tool = SearchFilesTool()

    # Test searching for .txt files
    result = await tool.execute(
        {"directory": str(nested_files), "pattern": "*.txt", "recursive": True}
    )

    assert result.success
    assert result.data is not None
    files: List[str] = result.data
    assert len(files) == 2  # Should find 2 .txt files

    # Test searching for Python files
    result = await tool.execute(
        {"directory": str(nested_files), "pattern": "*.py", "recursive": True}
    )

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
