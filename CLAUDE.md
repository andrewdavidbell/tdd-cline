# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is a command-line task manager application built in Python following Test-Driven AI Development (TD-AID) methodology. The application allows users to create, manage, and track daily tasks with features including priority levels, due dates, and status tracking.

## Development Methodology
**CRITICAL**: This project follows Test-Driven AI Development (TD-AID). Read `INSTRUCTIONS.md` for complete instructions. Key rules:
- **Always write tests before implementation code** (no exceptions)
- Never delete or modify tests to make them pass - fix the implementation instead
- Write only the minimum code necessary to make tests pass
- Update `STAGES.md` after each significant action

## TD-AID Commands
The user may issue these special commands that trigger specific workflows:
- `design the software` - Create/update `DESIGN.md`
- `plan the software` - Create `PLAN.md` with phased implementation
- `begin phase [N]` - Start implementation of phase N from `PLAN.md`
- `test status` - Run tests and generate comprehensive test coverage report
- `realign tests to the project plan` - Synchronise tests with `PLAN.md`
- `refactor with tests` - Refactor code whilst ensuring all tests pass
- `refresh project session` - Reload all project context after history compaction

## Project Structure
```
task_manager/
├── src/
│   └── task_manager/
│       ├── __init__.py
│       ├── models.py       # Task model and data structures
│       ├── operations.py   # Core task operations (add, delete, update)
│       └── storage.py      # JSON file handling
├── tests/
│   ├── __init__.py
│   └── test_operations.py
├── pyproject.toml          # Project configuration and dependencies
└── tasks.json              # Persistent task storage (created at runtime)
```

## Development Commands

### Environment Setup
```bash
# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Unix/macOS
uv pip install -e .

# Install development dependencies
uv pip install pytest pytest-cov
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src/task_manager --cov-report=term-missing

# Run specific test file
pytest tests/test_operations.py

# Run specific test
pytest tests/test_operations.py::test_function_name

# Run tests in verbose mode
pytest -v
```

### Running the Application
```bash
# Install package in development mode
uv pip install -e .

# Run CLI
task_cli <command> [options]

# Example commands
task_cli add --title "Task title" --priority high
task_cli list
task_cli complete <task_id>
task_cli delete <task_id>
```

## Architecture Notes

### Core Components
- **models.py**: Contains the `Task` data class with validation logic for priorities (high/medium/low) and due dates
- **operations.py**: Implements CRUD operations for tasks (create, read, update, delete, filter, sort)
- **storage.py**: Handles JSON serialisation/deserialisation for persistent storage in `tasks.json`

### Data Flow
1. CLI command → operations.py function
2. operations.py validates input and calls storage.py if needed
3. storage.py reads/writes JSON file
4. Results returned back through the chain

### Testing Strategy
- Unit tests for all public methods in models, operations, and storage modules
- Use pytest fixtures for test setup/teardown (e.g., temporary JSON files)
- Mock file I/O in tests where appropriate
- Aim for 100% code coverage

## Key Technical Decisions
- **No external dependencies**: Uses only Python standard library (json, datetime, etc.)
- **JSON storage**: Simple, human-readable persistence format
- **Data validation**: Enforced in the Task model before storage
- **CLI interface**: Simple subcommand structure for ease of use
