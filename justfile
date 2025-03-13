# List all recipes
default:
    @just --list

# Install dependencies with uv
install:
    uv pip install -e ".[dev]"

# Run tests with pytest
test:
    pytest

# Run tests with coverage
test-cov:
    pytest --cov=llm_agent --cov-report=term-missing

# Format code with ruff
fmt:
    ruff format .
    ruff check --fix .

# Check code style and type hints
check:
    ruff check .
    mypy llm_agent tests

# Clean python cache files
clean:
    find . -type d -name "__pycache__" -exec rm -r {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type f -name "*.pyd" -delete
    find . -type d -name "*.egg-info" -exec rm -r {} +
    find . -type d -name "*.egg" -exec rm -r {} +
    find . -type d -name ".pytest_cache" -exec rm -r {} +
    find . -type d -name ".ruff_cache" -exec rm -r {} +
    find . -type d -name ".mypy_cache" -exec rm -r {} +
    find . -type d -name "htmlcov" -exec rm -r {} +
    find . -type f -name ".coverage" -delete