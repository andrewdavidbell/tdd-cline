"""
Tests for the storage module.

This module tests JSON persistence, atomic writes, and CRUD operations
for the TaskStorage class.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from task_manager.models import Task, Priority, Status
from task_manager.storage import TaskStorage, StorageError, TaskNotFoundError


@pytest.fixture
def temp_storage_dir():
    """Create a temporary directory for storage tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def storage_file(temp_storage_dir):
    """Create a storage file path."""
    return temp_storage_dir / "tasks.json"


@pytest.fixture
def storage(storage_file):
    """Create a TaskStorage instance."""
    return TaskStorage(str(storage_file))


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return Task(
        title="Test Task",
        description="Test Description",
        priority=Priority.HIGH,
        due_date="2026-12-31"
    )


@pytest.fixture
def multiple_tasks():
    """Create multiple sample tasks."""
    return [
        Task(title="Task 1", priority=Priority.HIGH),
        Task(title="Task 2", priority=Priority.MEDIUM),
        Task(title="Task 3", priority=Priority.LOW),
    ]


# Test Storage Initialisation


def test_storage_init_creates_directory_if_not_exists(temp_storage_dir):
    """Test that storage creates directory if it doesn't exist."""
    nested_path = temp_storage_dir / "nested" / "dir" / "tasks.json"
    storage = TaskStorage(str(nested_path))
    assert nested_path.parent.exists()
    assert nested_path.exists()


def test_storage_init_with_existing_directory(storage_file):
    """Test that storage works when directory already exists."""
    storage_file.parent.mkdir(parents=True, exist_ok=True)
    storage = TaskStorage(str(storage_file))
    assert storage_file.exists()


def test_storage_init_creates_empty_file_if_not_exists(storage_file):
    """Test that storage creates empty JSON file if it doesn't exist."""
    storage = TaskStorage(str(storage_file))
    assert storage_file.exists()
    with open(storage_file, 'r') as f:
        data = json.load(f)
    assert data == []


# Test Loading Tasks


def test_load_empty_file_returns_empty_list(storage):
    """Test that loading from empty file returns empty list."""
    tasks = storage.load()
    assert tasks == []


def test_load_tasks_from_file(storage, sample_task):
    """Test loading tasks from file."""
    # Save a task first
    storage.add(sample_task)
    # Load tasks
    tasks = storage.load()
    assert len(tasks) == 1
    assert tasks[0].title == "Test Task"


def test_load_validates_json_schema(storage_file):
    """Test that load validates JSON schema."""
    # Write invalid JSON structure (not a list)
    with open(storage_file, 'w') as f:
        json.dump({"invalid": "structure"}, f)

    storage = TaskStorage(str(storage_file))
    with pytest.raises(StorageError, match="Invalid JSON schema"):
        storage.load()


def test_load_handles_corrupted_file(storage_file):
    """Test that load handles corrupted file gracefully."""
    # Write invalid JSON
    with open(storage_file, 'w') as f:
        f.write("{invalid json content")

    storage = TaskStorage(str(storage_file))
    with pytest.raises(StorageError, match="Failed to load tasks"):
        storage.load()


def test_load_converts_dicts_to_task_objects(storage, sample_task):
    """Test that load returns Task instances."""
    storage.add(sample_task)
    tasks = storage.load()
    assert all(isinstance(task, Task) for task in tasks)


# Test Saving Tasks


def test_save_empty_list(storage):
    """Test saving empty list."""
    storage.save([])
    tasks = storage.load()
    assert tasks == []


def test_save_single_task(storage, sample_task):
    """Test saving a single task."""
    storage.save([sample_task])
    tasks = storage.load()
    assert len(tasks) == 1
    assert tasks[0].title == sample_task.title


def test_save_multiple_tasks(storage, multiple_tasks):
    """Test saving multiple tasks."""
    storage.save(multiple_tasks)
    tasks = storage.load()
    assert len(tasks) == 3


def test_save_uses_atomic_write(storage_file, sample_task):
    """Test that save uses atomic write (file not corrupted if save fails)."""
    storage = TaskStorage(str(storage_file))
    storage.add(sample_task)

    # Verify task is saved
    tasks = storage.load()
    assert len(tasks) == 1

    # Mock file write to fail partway through
    original_open = open

    def mock_open(*args, **kwargs):
        if 'w' in str(kwargs.get('mode', '')) or ('w' in str(args[1]) if len(args) > 1 else False):
            # Simulate failure during write
            raise IOError("Simulated write failure")
        return original_open(*args, **kwargs)

    with patch('builtins.open', side_effect=mock_open):
        try:
            storage.save([sample_task, Task(title="New Task")])
        except (StorageError, IOError):
            pass

    # Original data should still be intact
    tasks = storage.load()
    assert len(tasks) == 1
    assert tasks[0].title == "Test Task"


def test_save_creates_backup_before_write(storage_file, sample_task):
    """Test that save creates backup before writing."""
    storage = TaskStorage(str(storage_file))
    storage.add(sample_task)

    backup_file = storage_file.parent / f"{storage_file.name}.backup"

    # Add another task (should create backup)
    storage.add(Task(title="Second Task"))

    # Backup should exist
    assert backup_file.exists()


def test_save_preserves_task_order(storage, multiple_tasks):
    """Test that save preserves task order."""
    storage.save(multiple_tasks)
    tasks = storage.load()

    for i, task in enumerate(tasks):
        assert task.title == multiple_tasks[i].title


# Test Get All


def test_get_all_returns_empty_list_when_no_tasks(storage):
    """Test get_all returns empty list when no tasks exist."""
    tasks = storage.get_all()
    assert tasks == []


def test_get_all_returns_all_tasks(storage, multiple_tasks):
    """Test get_all returns all tasks."""
    for task in multiple_tasks:
        storage.add(task)

    tasks = storage.get_all()
    assert len(tasks) == 3


def test_get_all_returns_copies_not_references(storage, sample_task):
    """Test get_all returns new instances, not references."""
    storage.add(sample_task)

    tasks1 = storage.get_all()
    tasks2 = storage.get_all()

    # Should be equal but not the same object
    assert tasks1[0].id == tasks2[0].id
    assert tasks1[0] is not tasks2[0]


# Test Add Task


def test_add_task_to_empty_storage(storage, sample_task):
    """Test adding task to empty storage."""
    storage.add(sample_task)
    tasks = storage.get_all()
    assert len(tasks) == 1
    assert tasks[0].title == "Test Task"


def test_add_task_to_existing_storage(storage, sample_task):
    """Test adding task to storage with existing tasks."""
    storage.add(sample_task)

    new_task = Task(title="New Task")
    storage.add(new_task)

    tasks = storage.get_all()
    assert len(tasks) == 2


def test_add_task_persists_to_file(storage, sample_task):
    """Test that add persists task to file."""
    storage.add(sample_task)

    # Create new storage instance and load
    new_storage = TaskStorage(storage._file_path)
    tasks = new_storage.get_all()
    assert len(tasks) == 1


def test_add_duplicate_id_raises_error(storage, sample_task):
    """Test that adding task with duplicate ID raises error."""
    storage.add(sample_task)

    # Try to add task with same ID
    duplicate_task = Task(title="Duplicate")
    duplicate_task.id = sample_task.id

    with pytest.raises(StorageError, match="already exists"):
        storage.add(duplicate_task)


# Test Remove Task


def test_remove_existing_task(storage, sample_task):
    """Test removing an existing task."""
    storage.add(sample_task)
    storage.remove(sample_task.id)

    tasks = storage.get_all()
    assert len(tasks) == 0


def test_remove_nonexistent_task_raises_error(storage):
    """Test that removing nonexistent task raises TaskNotFoundError."""
    with pytest.raises(TaskNotFoundError):
        storage.remove("nonexistent-id")


def test_remove_persists_to_file(storage, sample_task):
    """Test that remove persists to file."""
    storage.add(sample_task)
    storage.remove(sample_task.id)

    # Create new storage instance and verify
    new_storage = TaskStorage(storage._file_path)
    tasks = new_storage.get_all()
    assert len(tasks) == 0


def test_remove_from_multiple_tasks(storage, multiple_tasks):
    """Test removing correct task from multiple tasks."""
    for task in multiple_tasks:
        storage.add(task)

    # Remove middle task
    storage.remove(multiple_tasks[1].id)

    tasks = storage.get_all()
    assert len(tasks) == 2
    assert multiple_tasks[1].id not in [t.id for t in tasks]


# Test Update Task


def test_update_existing_task(storage, sample_task):
    """Test updating an existing task."""
    storage.add(sample_task)

    # Modify task
    sample_task.title = "Updated Title"
    storage.update(sample_task)

    task = storage.get_by_id(sample_task.id)
    assert task.title == "Updated Title"


def test_update_nonexistent_task_raises_error(storage, sample_task):
    """Test that updating nonexistent task raises TaskNotFoundError."""
    with pytest.raises(TaskNotFoundError):
        storage.update(sample_task)


def test_update_persists_to_file(storage, sample_task):
    """Test that update persists to file."""
    storage.add(sample_task)
    sample_task.title = "Updated"
    storage.update(sample_task)

    # Create new storage instance and verify
    new_storage = TaskStorage(storage._file_path)
    task = new_storage.get_by_id(sample_task.id)
    assert task.title == "Updated"


def test_update_preserves_other_tasks(storage, multiple_tasks):
    """Test that update doesn't affect other tasks."""
    for task in multiple_tasks:
        storage.add(task)

    # Update first task
    multiple_tasks[0].title = "Updated"
    storage.update(multiple_tasks[0])

    tasks = storage.get_all()
    assert len(tasks) == 3
    assert tasks[1].title == "Task 2"
    assert tasks[2].title == "Task 3"


# Test Get By ID


def test_get_by_id_finds_existing_task(storage, sample_task):
    """Test get_by_id finds existing task."""
    storage.add(sample_task)

    task = storage.get_by_id(sample_task.id)
    assert task.id == sample_task.id
    assert task.title == sample_task.title


def test_get_by_id_nonexistent_raises_error(storage):
    """Test that get_by_id raises TaskNotFoundError for nonexistent task."""
    with pytest.raises(TaskNotFoundError):
        storage.get_by_id("nonexistent-id")


# Test Error Handling


def test_storage_error_on_permission_denied(temp_storage_dir):
    """Test that permission errors are handled gracefully."""
    storage_file = temp_storage_dir / "tasks.json"
    storage = TaskStorage(str(storage_file))

    # Make directory read-only to prevent writing
    temp_storage_dir.chmod(0o555)

    try:
        with pytest.raises(StorageError, match="Failed to save tasks"):
            storage.add(Task(title="Test"))
    finally:
        # Restore permissions for cleanup
        temp_storage_dir.chmod(0o755)


def test_storage_error_on_disk_full(storage, sample_task, monkeypatch):
    """Test that disk full errors are handled gracefully."""
    def mock_write_fail(*args, **kwargs):
        raise OSError(28, "No space left on device")

    with patch('builtins.open', side_effect=mock_write_fail):
        with pytest.raises(StorageError):
            storage.add(sample_task)


def test_corrupted_backup_falls_back_gracefully(storage_file, sample_task):
    """Test that corrupted backup doesn't break storage."""
    storage = TaskStorage(str(storage_file))
    storage.add(sample_task)

    # Corrupt the backup file
    backup_file = storage_file.parent / f"{storage_file.name}.backup"
    if backup_file.exists():
        with open(backup_file, 'w') as f:
            f.write("{corrupted backup")

    # Should still be able to load from main file
    tasks = storage.load()
    assert len(tasks) == 1


# Test Concurrency Safety


def test_atomic_write_prevents_partial_updates(storage_file, sample_task):
    """Test that atomic write prevents partial file updates."""
    storage = TaskStorage(str(storage_file))
    storage.add(sample_task)

    original_content = storage_file.read_text()

    # Simulate failure during write by mocking
    with patch('pathlib.Path.rename', side_effect=OSError("Simulated failure")):
        try:
            storage.add(Task(title="New Task"))
        except StorageError:
            pass

    # Original file should be unchanged
    current_content = storage_file.read_text()
    assert current_content == original_content
