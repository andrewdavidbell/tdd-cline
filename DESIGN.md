# Software Design Document: Task Manager CLI

## 1. User Requirements

### 1.1 Target Users
- Individual users who need to manage personal tasks via command line
- Developers and technical users comfortable with CLI interfaces
- Users who prefer lightweight, text-based task management tools

### 1.2 User Stories
1. As a user, I want to create tasks with a title, description, priority level, and due date so that I can organise my work effectively
2. As a user, I want to mark tasks as complete or incomplete so that I can track my progress
3. As a user, I want to list all my tasks with filtering options so that I can focus on what's important
4. As a user, I want to delete tasks so that I can remove items that are no longer relevant
5. As a user, I want my tasks to persist between sessions so that I don't lose my data
6. As a user, I want to filter tasks by priority or status so that I can see high-priority items first
7. As a user, I want to sort tasks by due date or priority so that I can plan my work
8. As a user, I want to clear completed tasks so that my task list stays manageable

### 1.3 Use Cases

**UC1: Create Task**
- Actor: User
- Preconditions: Application is installed
- Main Flow: User runs `task_cli add` with title, optional description, priority, and due date
- Postconditions: Task is saved to storage and confirmation is displayed
- Alternative Flow: If required fields are missing, display error message

**UC2: List Tasks**
- Actor: User
- Preconditions: Application is installed
- Main Flow: User runs `task_cli list` with optional filters (status, priority)
- Postconditions: Filtered and sorted list of tasks is displayed
- Alternative Flow: If no tasks exist, display appropriate message

**UC3: Complete/Incomplete Task**
- Actor: User
- Preconditions: Task exists with given ID
- Main Flow: User runs `task_cli complete <id>` or `task_cli incomplete <id>`
- Postconditions: Task status is updated and saved
- Alternative Flow: If task ID doesn't exist, display error message

**UC4: Delete Task**
- Actor: User
- Preconditions: Task exists with given ID
- Main Flow: User runs `task_cli delete <id>`
- Postconditions: Task is removed from storage
- Alternative Flow: If task ID doesn't exist, display error message

**UC5: Clear Completed Tasks**
- Actor: User
- Preconditions: At least one completed task exists
- Main Flow: User runs `task_cli clear`
- Postconditions: All completed tasks are removed
- Alternative Flow: If no completed tasks exist, display appropriate message

## 2. Business Rules

### 2.1 Task Properties
- **ID**: Automatically generated unique identifier (UUID)
- **Title**: Required, non-empty string, maximum 200 characters
- **Description**: Optional string, maximum 1000 characters
- **Priority**: Required, must be one of: `high`, `medium`, `low` (default: `medium`)
- **Due Date**: Optional, must be valid ISO 8601 date format (YYYY-MM-DD)
- **Status**: Required, must be one of: `active`, `completed` (default: `active`)
- **Created At**: Automatically set to current timestamp (ISO 8601 format)
- **Completed At**: Automatically set when task is marked complete, null when active

### 2.2 Validation Rules
1. Title must not be empty or consist only of whitespace
2. Priority must be exactly one of the allowed values (case-insensitive input, stored as lowercase)
3. Due date, if provided, must be a valid date and cannot be in the past (when creating)
4. Task ID must be valid UUID format when referencing existing tasks
5. Description is optional but if provided, cannot exceed maximum length

### 2.3 Data Integrity Rules
1. Each task must have a unique ID
2. Tasks cannot be modified after deletion
3. Completed timestamp must not be set for active tasks
4. All timestamps must be in UTC

### 2.4 Sorting and Filtering Rules
1. Default sorting: by created_at timestamp (newest first)
2. When sorting by due date: tasks without due dates appear last
3. When sorting by priority: high → medium → low
4. Filtering by status: show only tasks matching the specified status
5. Multiple filters can be combined (AND logic)

## 3. Non-Functional Requirements

### 3.1 Performance
- Task list operations (add, delete, update) must complete in <100ms for up to 10,000 tasks
- Application startup (loading tasks) must complete in <500ms for up to 10,000 tasks
- CLI commands must respond immediately with feedback

### 3.2 Usability
- All commands must provide clear usage instructions via `--help` flag
- Error messages must be descriptive and suggest corrective actions
- Output must be human-readable and well-formatted
- Command names must be intuitive and follow common CLI conventions

### 3.3 Reliability
- Data must not be lost due to application crashes
- JSON file must be validated on load to detect corruption
- Atomic writes must be used to prevent partial updates
- Graceful degradation if storage file is corrupted (backup mechanism)

### 3.4 Maintainability
- Code must achieve 100% test coverage
- All public functions must have docstrings
- Code must follow PEP 8 style guidelines
- Modules must be loosely coupled for easy testing

### 3.5 Portability
- Must work on Linux, macOS, and Windows
- Must support Python 3.9+
- No platform-specific dependencies

### 3.6 Security
- User data stored in user's home directory with appropriate permissions
- No sensitive data collection or transmission
- Input sanitisation to prevent JSON injection attacks

## 4. Technical Requirements

### 4.1 Technology Stack
- **Language**: Python 3.9+
- **Package Manager**: uv
- **Testing Framework**: pytest with pytest-cov for coverage
- **Standard Library Modules**:
  - `json` - Data persistence
  - `uuid` - Unique ID generation
  - `datetime` - Date/time handling
  - `argparse` - CLI argument parsing
  - `pathlib` - Cross-platform file path handling
  - `typing` - Type hints for code clarity

### 4.2 Development Environment
- Virtual environment managed by `uv venv`
- Development dependencies: pytest, pytest-cov
- No runtime dependencies beyond Python standard library
- Git for version control (not initialised yet, but recommended)

### 4.3 Data Storage
- **Format**: JSON
- **Location**: `~/.task_manager/tasks.json` (user home directory)
- **Schema**:
```json
{
  "tasks": [
    {
      "id": "uuid-string",
      "title": "string",
      "description": "string or null",
      "priority": "high|medium|low",
      "due_date": "YYYY-MM-DD or null",
      "status": "active|completed",
      "created_at": "ISO 8601 timestamp",
      "completed_at": "ISO 8601 timestamp or null"
    }
  ],
  "version": "1.0"
}
```

### 4.4 Error Handling
- Use custom exception classes for domain-specific errors:
  - `TaskNotFoundError` - Task with given ID doesn't exist
  - `ValidationError` - Task data fails validation
  - `StorageError` - File I/O problems
- All exceptions must include descriptive error messages
- CLI must catch exceptions and display user-friendly messages

## 5. Architecture Design

### 5.1 System Architecture

```
┌─────────────────────────────────────────┐
│           CLI Layer                      │
│  (task_cli.py - argparse commands)       │
└──────────────┬──────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────┐
│       Business Logic Layer               │
│  (operations.py - CRUD operations)       │
└──────────┬───────────────────────────────┘
           │
           ↓
┌──────────────────────────┐  ┌───────────────────────┐
│   Domain Model Layer     │  │   Persistence Layer   │
│   (models.py - Task)     │←→│  (storage.py - JSON)  │
└──────────────────────────┘  └───────────────────────┘
```

### 5.2 Module Design

#### 5.2.1 models.py - Domain Models
**Responsibility**: Define data structures and validation logic

**Classes**:
- `Task` - Data class representing a task
  - Properties: id, title, description, priority, due_date, status, created_at, completed_at
  - Methods:
    - `validate()` - Validates all fields according to business rules
    - `to_dict()` - Serialises task to dictionary
    - `from_dict(data)` - Creates task from dictionary
    - `mark_complete()` - Sets status to completed and sets completed_at
    - `mark_incomplete()` - Sets status to active and clears completed_at

**Enums**:
- `Priority` - Enum for priority levels (HIGH, MEDIUM, LOW)
- `Status` - Enum for task status (ACTIVE, COMPLETED)

#### 5.2.2 operations.py - Business Logic
**Responsibility**: Implement core task operations

**Functions**:
- `create_task(title, description, priority, due_date)` - Creates and saves new task
- `get_task(task_id)` - Retrieves task by ID
- `list_tasks(status_filter, priority_filter, sort_by)` - Lists tasks with filters
- `update_task_status(task_id, status)` - Marks task complete/incomplete
- `delete_task(task_id)` - Removes task
- `clear_completed_tasks()` - Removes all completed tasks

**Design Notes**:
- All functions interact with storage layer
- Validation is delegated to Task model
- Returns Task objects or lists of Task objects
- Raises domain-specific exceptions on errors

#### 5.2.3 storage.py - Data Persistence
**Responsibility**: Handle JSON file I/O operations

**Class**:
- `TaskStorage` - Manages task persistence
  - `__init__(file_path)` - Initialises storage with file path
  - `load()` - Loads tasks from JSON file
  - `save(tasks)` - Saves tasks to JSON file (atomic write)
  - `get_all()` - Returns all stored tasks
  - `add(task)` - Adds task to storage
  - `remove(task_id)` - Removes task from storage
  - `update(task)` - Updates existing task

**Design Notes**:
- Uses atomic writes (write to temp file, then rename) to prevent corruption
- Creates storage directory if it doesn't exist
- Validates JSON schema on load
- Maintains backup of previous version before write

#### 5.2.4 cli.py - Command-Line Interface
**Responsibility**: Parse commands and display output

**Functions**:
- `main()` - Entry point, sets up argument parser
- `cmd_add(args)` - Handles add command
- `cmd_list(args)` - Handles list command
- `cmd_complete(args)` - Handles complete command
- `cmd_incomplete(args)` - Handles incomplete command
- `cmd_delete(args)` - Handles delete command
- `cmd_clear(args)` - Handles clear command
- `format_task(task)` - Formats task for display
- `format_task_list(tasks)` - Formats list of tasks as table

**Design Notes**:
- Each command function calls appropriate operations.py function
- Catches exceptions and displays user-friendly error messages
- Uses argparse subcommands for clean CLI structure
- Output formatting separated from business logic

### 5.3 Data Flow Examples

**Creating a Task**:
1. User runs: `task_cli add --title "Buy milk" --priority high --due-date 2025-10-25`
2. CLI layer parses arguments and calls `operations.create_task()`
3. operations.py creates Task object with provided data
4. Task validates itself (checks title, priority, date format)
5. operations.py calls `storage.add(task)`
6. storage.py loads existing tasks, adds new task, saves to JSON
7. Success confirmation displayed to user

**Listing Tasks**:
1. User runs: `task_cli list --status active --sort-by priority`
2. CLI layer calls `operations.list_tasks(status_filter='active', sort_by='priority')`
3. operations.py calls `storage.get_all()`
4. storage.py loads and returns all tasks
5. operations.py filters by status and sorts by priority
6. CLI layer formats tasks as table and displays

### 5.4 Component Interactions

```
CLI (cli.py)
  ↓ calls
Operations (operations.py)
  ↓ creates/uses
Task Model (models.py)
  ↓ passed to
Storage (storage.py)
  ↓ reads/writes
JSON File (tasks.json)
```

**Key Design Principles**:
- **Separation of Concerns**: Each module has single, well-defined responsibility
- **Dependency Flow**: CLI → Operations → Models/Storage (no circular dependencies)
- **Testability**: All modules can be tested independently with mocks
- **Loose Coupling**: Modules interact through well-defined interfaces

## 6. Testing Strategy

### 6.1 Unit Tests
**Coverage**: All modules (models, operations, storage, CLI)

**Test Files**:
- `tests/test_models.py` - Task model validation and methods
- `tests/test_operations.py` - Business logic functions
- `tests/test_storage.py` - File I/O operations (with temp files)
- `tests/test_cli.py` - Command parsing and output formatting

### 6.2 Test Patterns
- **Fixtures**: Use pytest fixtures for common test data (sample tasks)
- **Temp Files**: Use `tmp_path` fixture for storage tests
- **Mocking**: Mock storage layer in operations tests
- **Parametrised Tests**: Test validation with multiple invalid inputs

### 6.3 Test-Driven Development Process
1. Write test that defines expected behaviour
2. Run test and verify it fails (Red)
3. Write minimal code to make test pass (Green)
4. Refactor whilst keeping tests passing (Refactor)
5. Update STAGES.md to document progress

### 6.4 Coverage Goals
- Target: 100% code coverage
- All public methods must have tests
- All error conditions must be tested
- Edge cases (empty lists, invalid IDs, etc.) must be covered

## 7. Implementation Phases

### Phase 0: Project Setup
- Create directory structure
- Set up pyproject.toml with uv
- Initialise virtual environment
- Install pytest and pytest-cov

### Phase 1: Domain Models
- Implement Task data class
- Implement Priority and Status enums
- Implement validation logic
- Unit tests for all model functionality

### Phase 2: Storage Layer
- Implement TaskStorage class
- Implement JSON serialisation/deserialisation
- Implement atomic writes
- Unit tests with temp files

### Phase 3: Business Logic
- Implement operations.py functions
- Integrate with Task models
- Integrate with TaskStorage
- Unit tests with mocked storage

### Phase 4: CLI Layer
- Implement argument parsing
- Implement command handlers
- Implement output formatting
- Unit tests for CLI functions

### Phase 5: Integration & Polish
- Integration tests for end-to-end workflows
- Error handling improvements
- Help text and documentation
- Performance testing

## 8. Acceptance Criteria

### 8.1 Functional Criteria
✓ Users can create tasks with all required and optional fields
✓ Users can list tasks with filtering and sorting
✓ Users can mark tasks as complete or incomplete
✓ Users can delete individual tasks
✓ Users can clear all completed tasks
✓ Tasks persist between application runs
✓ All commands provide helpful error messages
✓ All commands support --help flag

### 8.2 Technical Criteria
✓ All tests pass with 100% code coverage
✓ Application can be installed via `uv pip install -e .`
✓ No runtime dependencies beyond Python stdlib
✓ Works on Linux, macOS, and Windows
✓ PEP 8 compliant code
✓ All public functions have docstrings

### 8.3 Quality Criteria
✓ No critical or high-severity bugs
✓ User-friendly error messages
✓ Clean, readable code
✓ Proper error handling throughout

## 9. Future Enhancements (Out of Scope)
- Task categories/tags
- Task search functionality
- Recurring tasks
- Task dependencies
- Export to other formats (CSV, Markdown)
- Cloud synchronisation
- Multiple task lists
- Colour-coded output
- Interactive mode (TUI)

## 10. Glossary
- **Task**: A single unit of work with properties like title, priority, and status
- **Active Task**: A task that has not been marked as completed
- **Completed Task**: A task that has been marked as done
- **Priority**: Importance level of a task (high, medium, low)
- **Due Date**: Optional deadline for task completion
- **UUID**: Universally Unique Identifier used for task IDs
- **TDD**: Test-Driven Development methodology
- **TD-AID**: Test-Driven AI Development methodology
