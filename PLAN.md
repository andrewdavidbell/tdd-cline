# Implementation Plan: Task Manager CLI

This document outlines the phased implementation plan for the Task Manager CLI application, following Test-Driven AI Development (TD-AID) methodology.

## Planning Principles

1. **Test-First Always**: Every phase begins by writing ALL tests before any implementation
2. **Compilable Artefacts**: Each phase produces working, testable code
3. **Incremental Building**: Each phase builds upon previous phases
4. **Refactor Stage**: Each phase includes refactoring before marking complete
5. **Documentation**: Update STAGES.md after completing each phase

## Phase Dependencies

```
Phase 0 (Setup)
    ↓
Phase 1 (Domain Models) ←─────┐
    ↓                          │
Phase 2 (Storage Layer)        │
    ↓                          │
Phase 3 (Business Logic) ──────┘
    ↓
Phase 4 (CLI Layer)
    ↓
Phase 5 (Integration & Polish)
```

---

## Phase 0: Project Setup

**Goal**: Establish project structure and tooling infrastructure

**Prerequisites**: None

**Test Requirements**: None (infrastructure phase)

**Tasks**:
1. Create directory structure:
   ```
   task_manager/
   ├── src/
   │   └── task_manager/
   │       └── __init__.py
   ├── tests/
   │   └── __init__.py
   └── pyproject.toml
   ```

2. Create `pyproject.toml` with:
   - Project metadata (name, version, description)
   - Python version requirement (>=3.9)
   - Entry point for `task_cli` command
   - Development dependencies: pytest, pytest-cov

3. Set up virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate  # Unix/macOS
   ```

4. Install development dependencies:
   ```bash
   uv pip install pytest pytest-cov
   ```

5. Verify setup by running pytest (should show "no tests collected")

**Deliverables**:
- Working directory structure
- Configured `pyproject.toml`
- Active virtual environment
- pytest installed and working

**Definition of Done**:
- ✓ Directory structure created
- ✓ `pyproject.toml` configured correctly
- ✓ Virtual environment activated
- ✓ `pytest` command runs successfully
- ✓ STAGES.md updated with Phase 0 completion

---

## Phase 1: Domain Models

**Goal**: Implement core data structures with validation

**Prerequisites**: Phase 0 complete

**Test Files**:
- `tests/test_models.py`

**Test Requirements** (Write ALL these tests FIRST):

### Test File: `tests/test_models.py`

#### Test Priority Enum:
1. `test_priority_enum_has_correct_values` - Verify HIGH, MEDIUM, LOW exist
2. `test_priority_enum_values` - Verify enum values are correct strings

#### Test Status Enum:
3. `test_status_enum_has_correct_values` - Verify ACTIVE, COMPLETED exist
4. `test_status_enum_values` - Verify enum values are correct strings

#### Test Task Creation:
5. `test_create_task_with_minimal_fields` - Create task with only title
6. `test_create_task_with_all_fields` - Create task with all optional fields
7. `test_task_auto_generates_id` - Verify UUID is auto-generated
8. `test_task_auto_sets_created_at` - Verify timestamp is auto-set
9. `test_task_defaults_status_to_active` - Verify default status
10. `test_task_defaults_priority_to_medium` - Verify default priority
11. `test_task_completed_at_is_none_for_new_task` - Verify null completed_at

#### Test Task Validation:
12. `test_validate_empty_title_raises_error` - Empty string should fail
13. `test_validate_whitespace_only_title_raises_error` - "   " should fail
14. `test_validate_title_too_long_raises_error` - >200 chars should fail
15. `test_validate_description_too_long_raises_error` - >1000 chars should fail
16. `test_validate_invalid_priority_raises_error` - "urgent" should fail
17. `test_validate_invalid_due_date_format_raises_error` - "2025-13-45" should fail
18. `test_validate_past_due_date_raises_error` - Yesterday's date should fail
19. `test_validate_accepts_future_due_date` - Tomorrow's date should pass
20. `test_validate_accepts_none_due_date` - None should pass

#### Test Task Methods:
21. `test_mark_complete_sets_status_to_completed` - Status changes to COMPLETED
22. `test_mark_complete_sets_completed_at_timestamp` - Timestamp is set
23. `test_mark_incomplete_sets_status_to_active` - Status changes to ACTIVE
24. `test_mark_incomplete_clears_completed_at` - Timestamp is cleared
25. `test_to_dict_serialises_all_fields` - All fields present in dict
26. `test_to_dict_handles_none_values` - None values serialised correctly
27. `test_from_dict_creates_task` - Task created from valid dict
28. `test_from_dict_with_missing_required_fields_raises_error` - Missing title fails
29. `test_from_dict_preserves_id` - ID from dict is preserved
30. `test_task_equality_based_on_id` - Two tasks with same ID are equal

#### Test Edge Cases:
31. `test_priority_case_insensitive` - "HIGH", "High", "high" all work
32. `test_title_strips_whitespace` - Leading/trailing spaces removed
33. `test_unicode_in_title_and_description` - Unicode chars supported

**Implementation Tasks** (Only after ALL tests written):
1. Create `src/task_manager/models.py`
2. Implement `Priority` enum (HIGH, MEDIUM, LOW)
3. Implement `Status` enum (ACTIVE, COMPLETED)
4. Implement `ValidationError` custom exception
5. Implement `Task` class:
   - Properties: id, title, description, priority, due_date, status, created_at, completed_at
   - `__init__()` with defaults
   - `validate()` method with all validation rules
   - `mark_complete()` method
   - `mark_incomplete()` method
   - `to_dict()` method
   - `from_dict()` class method
   - `__eq__()` method for equality

**Refactoring**:
- Extract validation logic into separate methods if needed
- Add type hints to all methods
- Add docstrings to all public methods
- Ensure PEP 8 compliance

**Deliverables**:
- `src/task_manager/models.py` with Priority, Status, Task, ValidationError
- `tests/test_models.py` with 33 passing tests
- 100% coverage of models.py

**Definition of Done**:
- ✓ All 33 tests written and initially failing
- ✓ All tests passing
- ✓ Code refactored and clean
- ✓ Type hints added
- ✓ Docstrings added
- ✓ Coverage report shows 100% for models.py
- ✓ STAGES.md updated with Phase 1 completion

---

## Phase 2: Storage Layer

**Goal**: Implement JSON persistence with atomic writes

**Prerequisites**: Phase 1 complete (Task model available)

**Test Files**:
- `tests/test_storage.py`

**Test Requirements** (Write ALL these tests FIRST):

### Test File: `tests/test_storage.py`

#### Test TaskStorage Initialisation:
1. `test_storage_init_creates_directory_if_not_exists` - Storage dir created
2. `test_storage_init_with_existing_directory` - No error if dir exists
3. `test_storage_init_creates_empty_file_if_not_exists` - Empty JSON created

#### Test Loading Tasks:
4. `test_load_empty_file_returns_empty_list` - Empty file → []
5. `test_load_tasks_from_file` - Load multiple tasks successfully
6. `test_load_validates_json_schema` - Invalid JSON raises StorageError
7. `test_load_handles_corrupted_file` - Corrupted file raises StorageError
8. `test_load_converts_dicts_to_task_objects` - Returns Task instances

#### Test Saving Tasks:
9. `test_save_empty_list` - Save empty list successfully
10. `test_save_single_task` - Save one task
11. `test_save_multiple_tasks` - Save multiple tasks
12. `test_save_uses_atomic_write` - File not corrupted if save fails
13. `test_save_creates_backup_before_write` - Backup file created
14. `test_save_preserves_task_order` - Order maintained

#### Test Get All:
15. `test_get_all_returns_empty_list_when_no_tasks` - No tasks → []
16. `test_get_all_returns_all_tasks` - All tasks returned
17. `test_get_all_returns_copies_not_references` - Returns new instances

#### Test Add Task:
18. `test_add_task_to_empty_storage` - Add to empty storage
19. `test_add_task_to_existing_storage` - Add to storage with tasks
20. `test_add_task_persists_to_file` - Task saved to JSON
21. `test_add_duplicate_id_raises_error` - Duplicate ID fails

#### Test Remove Task:
22. `test_remove_existing_task` - Remove task successfully
23. `test_remove_nonexistent_task_raises_error` - TaskNotFoundError raised
24. `test_remove_persists_to_file` - Removal saved to JSON
25. `test_remove_from_multiple_tasks` - Correct task removed

#### Test Update Task:
26. `test_update_existing_task` - Update task successfully
27. `test_update_nonexistent_task_raises_error` - TaskNotFoundError raised
28. `test_update_persists_to_file` - Update saved to JSON
29. `test_update_preserves_other_tasks` - Other tasks unchanged

#### Test Get By ID:
30. `test_get_by_id_finds_existing_task` - Returns correct task
31. `test_get_by_id_nonexistent_raises_error` - TaskNotFoundError raised

#### Test Error Handling:
32. `test_storage_error_on_permission_denied` - Permission errors handled
33. `test_storage_error_on_disk_full` - Disk full errors handled
34. `test_corrupted_backup_falls_back_gracefully` - Handles corrupted backup

#### Test Concurrency Safety:
35. `test_atomic_write_prevents_partial_updates` - No partial writes

**Implementation Tasks** (Only after ALL tests written):
1. Create `src/task_manager/storage.py`
2. Implement `StorageError` custom exception
3. Implement `TaskNotFoundError` custom exception
4. Implement `TaskStorage` class:
   - `__init__(file_path)` - Initialise with path, create directory/file
   - `_validate_schema(data)` - Validate JSON structure
   - `load()` - Load tasks from JSON
   - `save(tasks)` - Save tasks to JSON with atomic write
   - `get_all()` - Return all tasks
   - `get_by_id(task_id)` - Find task by ID
   - `add(task)` - Add task to storage
   - `remove(task_id)` - Remove task from storage
   - `update(task)` - Update existing task
   - `_atomic_write(data)` - Write to temp file then rename
   - `_create_backup()` - Backup current file

**Refactoring**:
- Extract file operations into helper methods
- Ensure all file operations are exception-safe
- Add comprehensive error messages
- Add type hints and docstrings

**Deliverables**:
- `src/task_manager/storage.py` with TaskStorage class
- `tests/test_storage.py` with 35 passing tests
- 100% coverage of storage.py

**Definition of Done**:
- ✓ All 35 tests written and initially failing
- ✓ All tests passing
- ✓ Code refactored and clean
- ✓ Atomic writes implemented correctly
- ✓ Error handling comprehensive
- ✓ Coverage report shows 100% for storage.py
- ✓ STAGES.md updated with Phase 2 completion

---

## Phase 3: Business Logic

**Goal**: Implement task operations (CRUD + filtering/sorting)

**Prerequisites**: Phase 1 and Phase 2 complete

**Test Files**:
- `tests/test_operations.py`

**Test Requirements** (Write ALL these tests FIRST):

### Test File: `tests/test_operations.py`

#### Test Create Task:
1. `test_create_task_with_minimal_fields` - Create with only title
2. `test_create_task_with_all_fields` - Create with all fields
3. `test_create_task_validates_input` - Invalid input raises ValidationError
4. `test_create_task_persists_to_storage` - Task saved via storage
5. `test_create_task_returns_task_object` - Returns created Task

#### Test Get Task:
6. `test_get_existing_task` - Retrieve task by ID
7. `test_get_nonexistent_task_raises_error` - TaskNotFoundError raised
8. `test_get_task_returns_correct_task` - Correct task returned

#### Test List Tasks:
9. `test_list_all_tasks_empty` - Empty list when no tasks
10. `test_list_all_tasks` - All tasks returned
11. `test_list_tasks_filter_by_active_status` - Only active tasks
12. `test_list_tasks_filter_by_completed_status` - Only completed tasks
13. `test_list_tasks_filter_by_high_priority` - Only high priority
14. `test_list_tasks_filter_by_medium_priority` - Only medium priority
15. `test_list_tasks_filter_by_low_priority` - Only low priority
16. `test_list_tasks_combined_filters` - Status AND priority filters
17. `test_list_tasks_sort_by_created_at_desc` - Default sort (newest first)
18. `test_list_tasks_sort_by_due_date_asc` - Sort by due date (earliest first)
19. `test_list_tasks_sort_by_due_date_none_last` - Tasks without due dates last
20. `test_list_tasks_sort_by_priority` - Sort by priority (high→medium→low)
21. `test_list_tasks_filter_and_sort` - Combined filtering and sorting

#### Test Update Task Status:
22. `test_mark_task_complete` - Mark active task as completed
23. `test_mark_task_incomplete` - Mark completed task as active
24. `test_mark_complete_sets_timestamp` - Completed_at timestamp set
25. `test_mark_incomplete_clears_timestamp` - Completed_at cleared
26. `test_update_status_persists_to_storage` - Status change saved
27. `test_update_nonexistent_task_raises_error` - TaskNotFoundError raised
28. `test_mark_already_completed_task_complete` - Idempotent operation

#### Test Delete Task:
29. `test_delete_existing_task` - Task removed successfully
30. `test_delete_nonexistent_task_raises_error` - TaskNotFoundError raised
31. `test_delete_persists_to_storage` - Deletion saved
32. `test_delete_removes_correct_task` - Only specified task removed

#### Test Clear Completed Tasks:
33. `test_clear_completed_tasks_removes_all_completed` - All completed removed
34. `test_clear_completed_tasks_preserves_active` - Active tasks preserved
35. `test_clear_completed_tasks_empty_list` - No error when no completed tasks
36. `test_clear_completed_tasks_persists_to_storage` - Changes saved
37. `test_clear_completed_returns_count` - Returns number removed

#### Test Edge Cases:
38. `test_operations_with_storage_error` - Handles storage errors gracefully
39. `test_concurrent_operations_safe` - Multiple operations don't corrupt data
40. `test_list_tasks_large_dataset` - Performance with 1000+ tasks

**Implementation Tasks** (Only after ALL tests written):
1. Create `src/task_manager/operations.py`
2. Create module-level storage instance (singleton pattern)
3. Implement `create_task(title, description=None, priority="medium", due_date=None)`:
   - Create Task object
   - Validate via Task.validate()
   - Add to storage
   - Return Task
4. Implement `get_task(task_id)`:
   - Retrieve from storage
   - Raise TaskNotFoundError if not found
5. Implement `list_tasks(status_filter=None, priority_filter=None, sort_by="created_at")`:
   - Get all tasks from storage
   - Apply status filter if provided
   - Apply priority filter if provided
   - Sort by specified field
   - Return filtered/sorted list
6. Implement `update_task_status(task_id, status)`:
   - Get task from storage
   - Call mark_complete() or mark_incomplete()
   - Update in storage
7. Implement `delete_task(task_id)`:
   - Remove from storage
   - Raise TaskNotFoundError if not found
8. Implement `clear_completed_tasks()`:
   - Get all tasks
   - Filter for completed tasks
   - Remove each completed task
   - Return count of removed tasks

**Refactoring**:
- Extract filtering logic into separate functions
- Extract sorting logic into separate functions
- Add comprehensive error handling
- Add type hints and docstrings

**Deliverables**:
- `src/task_manager/operations.py` with all CRUD functions
- `tests/test_operations.py` with 40 passing tests
- 100% coverage of operations.py

**Definition of Done**:
- ✓ All 40 tests written and initially failing
- ✓ All tests passing
- ✓ Code refactored and clean
- ✓ All functions have comprehensive error handling
- ✓ Coverage report shows 100% for operations.py
- ✓ STAGES.md updated with Phase 3 completion

---

## Phase 4: CLI Layer

**Goal**: Implement command-line interface with argparse

**Prerequisites**: Phase 3 complete (all operations available)

**Test Files**:
- `tests/test_cli.py`

**Test Requirements** (Write ALL these tests FIRST):

### Test File: `tests/test_cli.py`

#### Test Argument Parsing:
1. `test_parser_has_all_subcommands` - add, list, complete, incomplete, delete, clear exist
2. `test_add_command_required_title` - --title is required
3. `test_add_command_optional_description` - --description is optional
4. `test_add_command_optional_priority` - --priority is optional with default
5. `test_add_command_optional_due_date` - --due-date is optional
6. `test_list_command_optional_status` - --status filter is optional
7. `test_list_command_optional_priority` - --priority filter is optional
8. `test_list_command_optional_sort` - --sort-by is optional
9. `test_complete_command_required_id` - task_id is required
10. `test_incomplete_command_required_id` - task_id is required
11. `test_delete_command_required_id` - task_id is required
12. `test_clear_command_no_args` - No arguments required

#### Test Command Handlers:
13. `test_cmd_add_creates_task` - Calls operations.create_task()
14. `test_cmd_add_displays_success_message` - Success output shown
15. `test_cmd_add_displays_task_details` - Task details shown
16. `test_cmd_add_handles_validation_error` - ValidationError caught and displayed
17. `test_cmd_list_displays_all_tasks` - All tasks formatted and shown
18. `test_cmd_list_displays_empty_message` - Message when no tasks
19. `test_cmd_list_filters_by_status` - Status filter applied
20. `test_cmd_list_filters_by_priority` - Priority filter applied
21. `test_cmd_list_sorts_correctly` - Sort order applied
22. `test_cmd_complete_marks_task_complete` - Calls update_task_status()
23. `test_cmd_complete_displays_success_message` - Success output shown
24. `test_cmd_complete_handles_not_found_error` - TaskNotFoundError caught
25. `test_cmd_incomplete_marks_task_active` - Calls update_task_status()
26. `test_cmd_incomplete_displays_success_message` - Success output shown
27. `test_cmd_delete_removes_task` - Calls delete_task()
28. `test_cmd_delete_displays_success_message` - Success output shown
29. `test_cmd_delete_handles_not_found_error` - TaskNotFoundError caught
30. `test_cmd_clear_removes_completed_tasks` - Calls clear_completed_tasks()
31. `test_cmd_clear_displays_count_message` - Count of removed tasks shown
32. `test_cmd_clear_displays_none_message` - Message when no completed tasks

#### Test Output Formatting:
33. `test_format_task_includes_all_fields` - ID, title, priority, status, etc.
34. `test_format_task_handles_none_values` - None values display correctly
35. `test_format_task_displays_due_date` - Due date formatted correctly
36. `test_format_task_list_as_table` - Tasks displayed in table format
37. `test_format_task_list_headers` - Table has appropriate headers
38. `test_format_task_list_alignment` - Columns aligned properly

#### Test Help Text:
39. `test_main_help_lists_commands` - --help shows all commands
40. `test_add_help_shows_options` - add --help shows all options
41. `test_list_help_shows_filters` - list --help shows filter options

#### Test Error Handling:
42. `test_handles_storage_error_gracefully` - StorageError displayed to user
43. `test_invalid_command_shows_error` - Unknown command shows help
44. `test_missing_required_arg_shows_error` - Missing arg shows usage

#### Test Entry Point:
45. `test_main_entry_point_exists` - main() function exists
46. `test_main_entry_point_callable` - Can be called from command line

**Implementation Tasks** (Only after ALL tests written):
1. Create `src/task_manager/cli.py`
2. Implement `create_parser()`:
   - Main parser with description
   - Subparsers for each command
   - Add subcommand with --title, --description, --priority, --due-date
   - List subcommand with --status, --priority, --sort-by
   - Complete/incomplete/delete subcommands with task_id
   - Clear subcommand
3. Implement command handler functions:
   - `cmd_add(args)` - Create task and display confirmation
   - `cmd_list(args)` - List tasks with formatting
   - `cmd_complete(args)` - Mark complete and confirm
   - `cmd_incomplete(args)` - Mark active and confirm
   - `cmd_delete(args)` - Delete and confirm
   - `cmd_clear(args)` - Clear completed and show count
4. Implement formatting functions:
   - `format_task(task)` - Format single task for display
   - `format_task_list(tasks)` - Format list as table
   - `format_error(error)` - Format error message
5. Implement `main()` entry point:
   - Parse arguments
   - Call appropriate handler
   - Catch and display exceptions
   - Return exit code

**Refactoring**:
- Extract formatting logic into separate module if needed
- Ensure consistent output formatting
- Add colour support (optional, if time permits)
- Comprehensive error messages

**Deliverables**:
- `src/task_manager/cli.py` with full CLI implementation
- `tests/test_cli.py` with 46 passing tests
- Entry point configured in `pyproject.toml`
- `task_cli` command working from command line
- 100% coverage of cli.py

**Definition of Done**:
- ✓ All 46 tests written and initially failing
- ✓ All tests passing
- ✓ Code refactored and clean
- ✓ `task_cli` command works from terminal
- ✓ All commands have helpful --help text
- ✓ Error messages are user-friendly
- ✓ Coverage report shows 100% for cli.py
- ✓ STAGES.md updated with Phase 4 completion

---

## Phase 5: Integration & Polish

**Goal**: End-to-end testing, error handling improvements, documentation

**Prerequisites**: Phases 0-4 complete

**Test Files**:
- `tests/test_integration.py`

**Test Requirements** (Write ALL these tests FIRST):

### Test File: `tests/test_integration.py`

#### Test End-to-End Workflows:
1. `test_e2e_create_and_list_task` - Create task then list it
2. `test_e2e_create_complete_and_list` - Create, complete, list active/completed
3. `test_e2e_create_update_and_delete` - Full lifecycle of a task
4. `test_e2e_multiple_tasks_with_filtering` - Create multiple, filter by status
5. `test_e2e_multiple_tasks_with_sorting` - Create multiple, sort by different fields
6. `test_e2e_clear_completed_workflow` - Create, complete, clear workflow
7. `test_e2e_persistence_across_runs` - Data persists after program restart

#### Test CLI Integration:
8. `test_cli_add_command_full_workflow` - Run add command via subprocess
9. `test_cli_list_command_output` - Run list command and verify output
10. `test_cli_complete_command_workflow` - Run complete command via subprocess
11. `test_cli_delete_command_workflow` - Run delete command via subprocess
12. `test_cli_invalid_command_shows_help` - Invalid command shows error

#### Test Error Scenarios:
13. `test_invalid_due_date_format_shows_error` - User-friendly error shown
14. `test_nonexistent_task_id_shows_error` - Clear error message
15. `test_invalid_priority_shows_error` - Helpful error message
16. `test_storage_file_corrupted_shows_error` - Graceful degradation

#### Test Data Integrity:
17. `test_concurrent_operations_data_integrity` - Multiple operations safe
18. `test_backup_restores_on_corruption` - Backup mechanism works
19. `test_atomic_write_prevents_data_loss` - Partial writes prevented

#### Test Performance:
20. `test_performance_add_1000_tasks` - Acceptable performance at scale
21. `test_performance_list_1000_tasks` - Listing performs well
22. `test_performance_startup_with_large_file` - Loads quickly

**Implementation Tasks** (Only after ALL tests written):
1. Create `tests/test_integration.py` with all integration tests
2. Fix any bugs discovered during integration testing
3. Improve error messages based on test scenarios
4. Add input validation at CLI layer for better UX
5. Optimise performance if tests reveal issues
6. Add graceful handling of edge cases

**Documentation Tasks**:
1. Add comprehensive docstrings to all public functions
2. Create README.md with:
   - Installation instructions
   - Usage examples for each command
   - Configuration options
   - Troubleshooting section
3. Add inline comments for complex logic
4. Ensure all help text is clear and accurate

**Polish Tasks**:
1. Run pytest with coverage report
2. Ensure 100% coverage across all modules
3. Run type checker (mypy) if time permits
4. Run linter (flake8/pylint) and fix issues
5. Manual testing of all commands
6. Test on different platforms (if available)

**Deliverables**:
- `tests/test_integration.py` with 22 passing tests
- README.md with complete documentation
- All docstrings added
- 100% overall code coverage
- All linter warnings resolved
- Working application ready for use

**Definition of Done**:
- ✓ All 22 integration tests written and initially failing
- ✓ All tests passing (154 total tests across all phases)
- ✓ 100% code coverage achieved
- ✓ README.md created with full documentation
- ✓ All docstrings added
- ✓ Code passes linter checks
- ✓ Manual testing completed successfully
- ✓ STAGES.md updated with Phase 5 completion
- ✓ Project ready for release

---

## Summary Statistics

**Total Tests**: 154 tests across 5 test files
- `test_models.py`: 33 tests
- `test_storage.py`: 35 tests
- `test_operations.py`: 40 tests
- `test_cli.py`: 46 tests
- `test_integration.py`: 22 tests

**Total Phases**: 6 (including Phase 0)

**Coverage Target**: 100% for all modules

**Development Time Estimate**:
- Phase 0: 30 minutes
- Phase 1: 2-3 hours
- Phase 2: 2-3 hours
- Phase 3: 2-3 hours
- Phase 4: 3-4 hours
- Phase 5: 2-3 hours
- **Total**: 12-16 hours

---

## How to Use This Plan

### Starting a Phase:
1. User issues command: `begin phase [N]`
2. Read phase requirements from this document
3. Create ALL test files specified for that phase
4. Write ALL tests for that phase BEFORE any implementation
5. Run tests to verify they fail appropriately (Red)
6. Implement minimal code to make tests pass (Green)
7. Refactor while maintaining passing tests (Refactor)
8. Update STAGES.md with completion status

### Tracking Progress:
- Use STAGES.md to document:
  - Phase start date/time
  - Tests written (count)
  - Tests passing (count)
  - Issues encountered
  - Phase completion date/time

### Quality Gates:
Each phase must meet these criteria before moving to next:
1. ✓ All specified tests written
2. ✓ All tests passing
3. ✓ Code refactored and clean
4. ✓ Coverage target met for phase modules
5. ✓ STAGES.md updated

---

## Notes

- **Never skip test writing**: If tempted to write implementation first, STOP and write tests
- **Never modify tests to pass**: If tests fail, fix implementation, not tests
- **Keep tests independent**: Each test should be able to run in isolation
- **Use fixtures liberally**: Reduce duplication in test setup
- **Test behaviour, not implementation**: Tests should verify "what", not "how"

This plan follows TD-AID principles strictly. Adherence to these guidelines will ensure high-quality, well-tested, maintainable code.
