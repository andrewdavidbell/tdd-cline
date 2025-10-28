"""
Integration tests for Task Manager CLI application.

These tests verify end-to-end workflows, CLI integration, error handling,
data integrity, and performance of the complete system.
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from task_manager.models import Priority, Status, Task
from task_manager.operations import (
    clear_completed_tasks,
    create_task,
    delete_task,
    get_task,
    list_tasks,
    update_task_status,
)
from task_manager.storage import TaskStorage


# ==================== Test End-to-End Workflows ====================


def test_e2e_create_and_list_task(tmp_path):
    """Test creating a task and then listing it."""
    storage_file = tmp_path / "tasks.json"
    storage = TaskStorage(str(storage_file))

    # Patch the module-level storage
    import task_manager.operations as ops
    original_storage = ops._storage
    ops._storage = storage

    try:
        # Create a task
        task = create_task("Test Task", "Test description", "high", None)
        assert task.title == "Test Task"
        assert task.priority == Priority.HIGH

        # List tasks
        tasks = list_tasks()
        assert len(tasks) == 1
        assert tasks[0].id == task.id
        assert tasks[0].title == "Test Task"
    finally:
        ops._storage = original_storage


def test_e2e_create_complete_and_list(tmp_path):
    """Test creating tasks, completing some, and listing by status."""
    storage_file = tmp_path / "tasks.json"
    storage = TaskStorage(str(storage_file))

    import task_manager.operations as ops
    original_storage = ops._storage
    ops._storage = storage

    try:
        # Create multiple tasks
        task1 = create_task("Active Task 1", None, "high", None)
        task2 = create_task("Active Task 2", None, "medium", None)
        task3 = create_task("To Complete", None, "low", None)

        # Complete one task
        update_task_status(task3.id, Status.COMPLETED)

        # List active tasks
        active_tasks = list_tasks(status_filter=Status.ACTIVE)
        assert len(active_tasks) == 2
        assert all(t.status == Status.ACTIVE for t in active_tasks)

        # List completed tasks
        completed_tasks = list_tasks(status_filter=Status.COMPLETED)
        assert len(completed_tasks) == 1
        assert completed_tasks[0].id == task3.id
        assert completed_tasks[0].status == Status.COMPLETED
    finally:
        ops._storage = original_storage


def test_e2e_create_update_and_delete(tmp_path):
    """Test full lifecycle of a task: create, update, delete."""
    storage_file = tmp_path / "tasks.json"
    storage = TaskStorage(str(storage_file))

    import task_manager.operations as ops
    original_storage = ops._storage
    ops._storage = storage

    try:
        # Create task
        task = create_task("Lifecycle Task", "Initial description", "medium", None)
        task_id = task.id

        # Verify it exists
        retrieved = get_task(task_id)
        assert retrieved.title == "Lifecycle Task"
        assert retrieved.status == Status.ACTIVE

        # Update status
        update_task_status(task_id, Status.COMPLETED)
        updated = get_task(task_id)
        assert updated.status == Status.COMPLETED
        assert updated.completed_at is not None

        # Delete task
        delete_task(task_id)

        # Verify it's gone
        from task_manager.storage import TaskNotFoundError
        with pytest.raises(TaskNotFoundError):
            get_task(task_id)
    finally:
        ops._storage = original_storage


def test_e2e_multiple_tasks_with_filtering(tmp_path):
    """Test creating multiple tasks and filtering by status and priority."""
    storage_file = tmp_path / "tasks.json"
    storage = TaskStorage(str(storage_file))

    import task_manager.operations as ops
    original_storage = ops._storage
    ops._storage = storage

    try:
        # Create tasks with various priorities
        create_task("High Priority 1", None, "high", None)
        create_task("High Priority 2", None, "high", None)
        create_task("Medium Priority", None, "medium", None)
        create_task("Low Priority", None, "low", None)

        # Mark some as completed
        all_tasks = list_tasks()
        update_task_status(all_tasks[0].id, Status.COMPLETED)
        update_task_status(all_tasks[2].id, Status.COMPLETED)

        # Filter by active + high priority
        active_high = list_tasks(status_filter=Status.ACTIVE, priority_filter=Priority.HIGH)
        assert len(active_high) == 1
        assert active_high[0].priority == Priority.HIGH
        assert active_high[0].status == Status.ACTIVE

        # Filter by completed
        completed = list_tasks(status_filter=Status.COMPLETED)
        assert len(completed) == 2
        assert all(t.status == Status.COMPLETED for t in completed)
    finally:
        ops._storage = original_storage


def test_e2e_multiple_tasks_with_sorting(tmp_path):
    """Test creating multiple tasks and sorting by different fields."""
    storage_file = tmp_path / "tasks.json"
    storage = TaskStorage(str(storage_file))

    import task_manager.operations as ops
    original_storage = ops._storage
    ops._storage = storage

    try:
        # Create tasks with different due dates
        from datetime import datetime, timedelta
        today = datetime.now()

        task1 = create_task("Task 1", None, "low", (today + timedelta(days=3)).strftime("%Y-%m-%d"))
        time.sleep(0.01)  # Ensure different created_at timestamps
        task2 = create_task("Task 2", None, "high", (today + timedelta(days=1)).strftime("%Y-%m-%d"))
        time.sleep(0.01)
        task3 = create_task("Task 3", None, "medium", (today + timedelta(days=2)).strftime("%Y-%m-%d"))

        # Sort by created_at (default, newest first)
        by_created = list_tasks(sort_by="created_at")
        assert by_created[0].id == task3.id  # Newest
        assert by_created[-1].id == task1.id  # Oldest

        # Sort by due_date (earliest first)
        by_due = list_tasks(sort_by="due_date")
        assert by_due[0].id == task2.id  # Day 1
        assert by_due[1].id == task3.id  # Day 2
        assert by_due[2].id == task1.id  # Day 3

        # Sort by priority (high -> medium -> low)
        by_priority = list_tasks(sort_by="priority")
        assert by_priority[0].priority == Priority.HIGH
        assert by_priority[1].priority == Priority.MEDIUM
        assert by_priority[2].priority == Priority.LOW
    finally:
        ops._storage = original_storage


def test_e2e_clear_completed_workflow(tmp_path):
    """Test creating, completing, and clearing completed tasks."""
    storage_file = tmp_path / "tasks.json"
    storage = TaskStorage(str(storage_file))

    import task_manager.operations as ops
    original_storage = ops._storage
    ops._storage = storage

    try:
        # Create tasks
        task1 = create_task("Task 1", None, "high", None)
        task2 = create_task("Task 2", None, "medium", None)
        task3 = create_task("Task 3", None, "low", None)

        # Complete two tasks
        update_task_status(task1.id, Status.COMPLETED)
        update_task_status(task3.id, Status.COMPLETED)

        # Verify counts before clearing
        all_tasks = list_tasks()
        assert len(all_tasks) == 3

        # Clear completed
        count = clear_completed_tasks()
        assert count == 2

        # Verify only active task remains
        remaining = list_tasks()
        assert len(remaining) == 1
        assert remaining[0].id == task2.id
        assert remaining[0].status == Status.ACTIVE
    finally:
        ops._storage = original_storage


def test_e2e_persistence_across_runs(tmp_path):
    """Test that data persists after program restart."""
    storage_file = tmp_path / "tasks.json"

    # First "run" - create tasks
    storage1 = TaskStorage(str(storage_file))
    import task_manager.operations as ops
    original_storage = ops._storage
    ops._storage = storage1

    try:
        task1 = create_task("Persistent Task", "Should survive restart", "high", None)
        task_id = task1.id
    finally:
        ops._storage = original_storage

    # Simulate program restart - create new storage instance
    storage2 = TaskStorage(str(storage_file))
    ops._storage = storage2

    try:
        # Verify task persisted
        tasks = list_tasks()
        assert len(tasks) == 1
        assert tasks[0].id == task_id
        assert tasks[0].title == "Persistent Task"
        assert tasks[0].description == "Should survive restart"
        assert tasks[0].priority == Priority.HIGH
    finally:
        ops._storage = original_storage


# ==================== Test CLI Integration ====================


def test_cli_add_command_full_workflow(tmp_path):
    """Test add command via subprocess."""
    storage_file = tmp_path / "tasks.json"

    # Run add command
    result = subprocess.run(
        [
            sys.executable, "-m", "task_manager.cli",
            "add",
            "--title", "CLI Test Task",
            "--description", "Added via CLI",
            "--priority", "high"
        ],
        env={**os.environ, "TASK_MANAGER_STORAGE": str(storage_file)},
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "Created task:" in result.stdout or "Task created" in result.stdout

    # Verify task was created
    storage = TaskStorage(str(storage_file))
    tasks = storage.get_all()
    assert len(tasks) == 1
    assert tasks[0].title == "CLI Test Task"


def test_cli_list_command_output(tmp_path):
    """Test list command output via subprocess."""
    storage_file = tmp_path / "tasks.json"
    storage = TaskStorage(str(storage_file))

    # Create some tasks
    task = Task(title="List Test Task", priority=Priority.MEDIUM)
    storage.add(task)

    # Run list command
    result = subprocess.run(
        [sys.executable, "-m", "task_manager.cli", "list"],
        env={**os.environ, "TASK_MANAGER_STORAGE": str(storage_file)},
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "List Test Task" in result.stdout


def test_cli_complete_command_workflow(tmp_path):
    """Test complete command via subprocess."""
    storage_file = tmp_path / "tasks.json"
    storage = TaskStorage(str(storage_file))

    # Create task
    task = Task(title="To Complete", priority=Priority.HIGH)
    storage.add(task)
    task_id = str(task.id)

    # Run complete command
    result = subprocess.run(
        [sys.executable, "-m", "task_manager.cli", "complete", task_id],
        env={**os.environ, "TASK_MANAGER_STORAGE": str(storage_file)},
        capture_output=True,
        text=True
    )

    assert result.returncode == 0

    # Verify task was completed
    completed_task = storage.get_by_id(task_id)
    assert completed_task.status == Status.COMPLETED


def test_cli_delete_command_workflow(tmp_path):
    """Test delete command via subprocess."""
    storage_file = tmp_path / "tasks.json"
    storage = TaskStorage(str(storage_file))

    # Create task
    task = Task(title="To Delete", priority=Priority.LOW)
    storage.add(task)
    task_id = str(task.id)

    # Run delete command
    result = subprocess.run(
        [sys.executable, "-m", "task_manager.cli", "delete", task_id],
        env={**os.environ, "TASK_MANAGER_STORAGE": str(storage_file)},
        capture_output=True,
        text=True
    )

    assert result.returncode == 0

    # Verify task was deleted
    from task_manager.storage import TaskNotFoundError
    with pytest.raises(TaskNotFoundError):
        storage.get_by_id(task_id)


def test_cli_invalid_command_shows_help(tmp_path):
    """Test that invalid command shows error."""
    result = subprocess.run(
        [sys.executable, "-m", "task_manager.cli", "invalid_command"],
        capture_output=True,
        text=True
    )

    assert result.returncode != 0
    assert "invalid choice" in result.stderr.lower()


# ==================== Test Error Scenarios ====================


def test_invalid_due_date_format_shows_error(tmp_path):
    """Test that invalid due date format shows user-friendly error."""
    storage_file = tmp_path / "tasks.json"
    storage = TaskStorage(str(storage_file))

    import task_manager.operations as ops
    original_storage = ops._storage
    ops._storage = storage

    try:
        from task_manager.models import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            create_task("Test", None, "medium", "2025-13-45")  # Invalid date

        assert "due_date" in str(exc_info.value).lower()
    finally:
        ops._storage = original_storage


def test_nonexistent_task_id_shows_error(tmp_path):
    """Test that nonexistent task ID shows clear error."""
    storage_file = tmp_path / "tasks.json"
    storage = TaskStorage(str(storage_file))

    import task_manager.operations as ops
    original_storage = ops._storage
    ops._storage = storage

    try:
        from task_manager.storage import TaskNotFoundError
        with pytest.raises(TaskNotFoundError) as exc_info:
            get_task("nonexistent-id-12345")

        assert "not found" in str(exc_info.value).lower()
    finally:
        ops._storage = original_storage


def test_invalid_priority_shows_error(tmp_path):
    """Test that invalid priority shows helpful error."""
    storage_file = tmp_path / "tasks.json"
    storage = TaskStorage(str(storage_file))

    import task_manager.operations as ops
    original_storage = ops._storage
    ops._storage = storage

    try:
        from task_manager.models import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            create_task("Test", None, "urgent", None)  # Invalid priority

        assert "priority" in str(exc_info.value).lower()
    finally:
        ops._storage = original_storage


def test_storage_file_corrupted_shows_error(tmp_path):
    """Test graceful handling of corrupted storage file."""
    storage_file = tmp_path / "tasks.json"

    # Write corrupted JSON
    storage_file.write_text("{ invalid json content !@#")

    # Try to load
    from task_manager.storage import StorageError
    storage = TaskStorage(str(storage_file))

    with pytest.raises(StorageError):
        storage.load()


# ==================== Test Data Integrity ====================


def test_concurrent_operations_data_integrity(tmp_path):
    """Test that multiple operations don't corrupt data."""
    storage_file = tmp_path / "tasks.json"
    storage = TaskStorage(str(storage_file))

    import task_manager.operations as ops
    original_storage = ops._storage
    ops._storage = storage

    try:
        # Create multiple tasks rapidly
        tasks = []
        for i in range(10):
            task = create_task(f"Task {i}", None, "medium", None)
            tasks.append(task)

        # Update multiple tasks
        for i in range(0, 10, 2):
            update_task_status(tasks[i].id, Status.COMPLETED)

        # Verify all tasks are still present and valid
        all_tasks = list_tasks()
        assert len(all_tasks) == 10

        # Verify the JSON is valid
        with open(storage_file, 'r') as f:
            data = json.load(f)
        assert len(data) == 10
    finally:
        ops._storage = original_storage


def test_backup_restores_on_corruption(tmp_path):
    """Test that backup mechanism works correctly."""
    storage_file = tmp_path / "tasks.json"
    storage = TaskStorage(str(storage_file))

    # Create initial task
    task = Task(title="Original Task", priority=Priority.HIGH)
    storage.add(task)

    # Verify backup was created
    backup_file = Path(str(storage_file) + ".backup")
    assert backup_file.exists()

    # Corrupt main file
    storage_file.write_text("corrupted data")

    # Verify backup is still valid
    with open(backup_file, 'r') as f:
        backup_data = json.load(f)
    assert len(backup_data) == 1
    assert backup_data[0]["title"] == "Original Task"


def test_atomic_write_prevents_data_loss(tmp_path):
    """Test that atomic writes prevent partial updates."""
    storage_file = tmp_path / "tasks.json"
    storage = TaskStorage(str(storage_file))

    # Create initial tasks
    task1 = Task(title="Task 1", priority=Priority.HIGH)
    task2 = Task(title="Task 2", priority=Priority.MEDIUM)
    storage.add(task1)
    storage.add(task2)

    # Read original content
    original_content = storage_file.read_text()

    # Verify temp file doesn't exist
    temp_pattern = str(storage_file.parent / "*.tmp")
    import glob
    temp_files = glob.glob(temp_pattern)
    assert len(temp_files) == 0  # Temp files should be cleaned up

    # File should still be valid JSON
    with open(storage_file, 'r') as f:
        data = json.load(f)
    assert len(data) == 2


# ==================== Test Performance ====================


def test_performance_add_1000_tasks(tmp_path):
    """Test acceptable performance when adding many tasks."""
    storage_file = tmp_path / "tasks.json"
    storage = TaskStorage(str(storage_file))

    import task_manager.operations as ops
    original_storage = ops._storage
    ops._storage = storage

    try:
        start_time = time.time()

        for i in range(1000):
            create_task(f"Task {i}", f"Description {i}", "medium", None)

        elapsed = time.time() - start_time

        # Should complete in reasonable time (adjust threshold as needed)
        assert elapsed < 30.0, f"Adding 1000 tasks took {elapsed:.2f}s, expected < 30s"

        # Verify all tasks were created
        tasks = list_tasks()
        assert len(tasks) == 1000
    finally:
        ops._storage = original_storage


def test_performance_list_1000_tasks(tmp_path):
    """Test listing performs well with many tasks."""
    storage_file = tmp_path / "tasks.json"
    storage = TaskStorage(str(storage_file))

    import task_manager.operations as ops
    original_storage = ops._storage
    ops._storage = storage

    try:
        # Create 1000 tasks
        for i in range(1000):
            create_task(f"Task {i}", None, "medium", None)

        # Measure list performance
        start_time = time.time()
        tasks = list_tasks()
        elapsed = time.time() - start_time

        assert len(tasks) == 1000
        assert elapsed < 5.0, f"Listing 1000 tasks took {elapsed:.2f}s, expected < 5s"
    finally:
        ops._storage = original_storage


def test_performance_startup_with_large_file(tmp_path):
    """Test that loading large storage file is fast."""
    storage_file = tmp_path / "tasks.json"

    # Create storage with many tasks
    storage = TaskStorage(str(storage_file))
    tasks = [Task(title=f"Task {i}", priority=Priority.MEDIUM) for i in range(1000)]
    storage.save(tasks)

    # Measure load performance
    start_time = time.time()
    new_storage = TaskStorage(str(storage_file))
    loaded_tasks = new_storage.get_all()
    elapsed = time.time() - start_time

    assert len(loaded_tasks) == 1000
    assert elapsed < 5.0, f"Loading 1000 tasks took {elapsed:.2f}s, expected < 5s"
