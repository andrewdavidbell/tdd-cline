"""
Tests for task_manager.operations module.

This module tests the business logic layer for task operations including
CRUD operations, filtering, sorting, and edge cases.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import os

from task_manager.models import Task, Priority, Status, ValidationError
from task_manager.storage import TaskStorage, StorageError, TaskNotFoundError
import task_manager.operations as operations


@pytest.fixture
def temp_storage_file():
    """Create a temporary storage file for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "test_tasks.json"
        yield storage_path


@pytest.fixture
def storage(temp_storage_file):
    """Create a TaskStorage instance for testing."""
    return TaskStorage(temp_storage_file)


@pytest.fixture(autouse=True)
def setup_operations(storage):
    """Set up operations module with test storage before each test."""
    operations._storage = storage
    yield
    # Cleanup after test
    operations._storage = None


# Test Create Task

def test_create_task_with_minimal_fields():
    """Test creating a task with only the required title field."""
    task = operations.create_task("Buy groceries")

    assert task.title == "Buy groceries"
    assert task.description is None
    assert task.priority == Priority.MEDIUM
    assert task.due_date is None
    assert task.status == Status.ACTIVE


def test_create_task_with_all_fields():
    """Test creating a task with all optional fields provided."""
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    task = operations.create_task(
        title="Complete project",
        description="Finish the task manager implementation",
        priority="high",
        due_date=tomorrow
    )

    assert task.title == "Complete project"
    assert task.description == "Finish the task manager implementation"
    assert task.priority == Priority.HIGH
    assert task.due_date == tomorrow
    assert task.status == Status.ACTIVE


def test_create_task_validates_input():
    """Test that create_task validates input and raises ValidationError for invalid data."""
    with pytest.raises(ValidationError):
        operations.create_task("")  # Empty title

    with pytest.raises(ValidationError):
        operations.create_task("Task", priority="invalid")  # Invalid priority

    with pytest.raises(ValidationError):
        operations.create_task("Task", due_date="2020-01-01")  # Past date


def test_create_task_persists_to_storage(storage):
    """Test that created tasks are saved to storage."""
    task = operations.create_task("Test task")

    # Verify task is in storage
    stored_tasks = storage.get_all()
    assert len(stored_tasks) == 1
    assert stored_tasks[0].id == task.id


def test_create_task_returns_task_object():
    """Test that create_task returns a Task instance."""
    task = operations.create_task("Test task")

    assert isinstance(task, Task)
    assert task.id is not None
    assert task.created_at is not None


# Test Get Task

def test_get_existing_task():
    """Test retrieving an existing task by ID."""
    created_task = operations.create_task("Test task")

    retrieved_task = operations.get_task(created_task.id)

    assert retrieved_task.id == created_task.id
    assert retrieved_task.title == "Test task"


def test_get_nonexistent_task_raises_error():
    """Test that getting a nonexistent task raises TaskNotFoundError."""
    with pytest.raises(TaskNotFoundError):
        operations.get_task("nonexistent-id")


def test_get_task_returns_correct_task():
    """Test that get_task returns the correct task when multiple exist."""
    task1 = operations.create_task("Task 1")
    task2 = operations.create_task("Task 2")
    task3 = operations.create_task("Task 3")

    retrieved = operations.get_task(task2.id)

    assert retrieved.id == task2.id
    assert retrieved.title == "Task 2"


# Test List Tasks

def test_list_all_tasks_empty():
    """Test that list_tasks returns an empty list when no tasks exist."""
    tasks = operations.list_tasks()

    assert tasks == []


def test_list_all_tasks():
    """Test that list_tasks returns all tasks when no filters applied."""
    task1 = operations.create_task("Task 1")
    task2 = operations.create_task("Task 2")
    task3 = operations.create_task("Task 3")

    tasks = operations.list_tasks()

    assert len(tasks) == 3
    task_ids = [t.id for t in tasks]
    assert task1.id in task_ids
    assert task2.id in task_ids
    assert task3.id in task_ids


def test_list_tasks_filter_by_active_status():
    """Test filtering tasks by active status."""
    task1 = operations.create_task("Active task")
    task2 = operations.create_task("To be completed")
    operations.update_task_status(task2.id, Status.COMPLETED)

    active_tasks = operations.list_tasks(status_filter=Status.ACTIVE)

    assert len(active_tasks) == 1
    assert active_tasks[0].id == task1.id


def test_list_tasks_filter_by_completed_status():
    """Test filtering tasks by completed status."""
    task1 = operations.create_task("Active task")
    task2 = operations.create_task("Completed task")
    operations.update_task_status(task2.id, Status.COMPLETED)

    completed_tasks = operations.list_tasks(status_filter=Status.COMPLETED)

    assert len(completed_tasks) == 1
    assert completed_tasks[0].id == task2.id


def test_list_tasks_filter_by_high_priority():
    """Test filtering tasks by high priority."""
    task1 = operations.create_task("High priority", priority="high")
    task2 = operations.create_task("Medium priority", priority="medium")
    task3 = operations.create_task("Low priority", priority="low")

    high_tasks = operations.list_tasks(priority_filter=Priority.HIGH)

    assert len(high_tasks) == 1
    assert high_tasks[0].id == task1.id


def test_list_tasks_filter_by_medium_priority():
    """Test filtering tasks by medium priority."""
    task1 = operations.create_task("High priority", priority="high")
    task2 = operations.create_task("Medium priority", priority="medium")

    medium_tasks = operations.list_tasks(priority_filter=Priority.MEDIUM)

    assert len(medium_tasks) == 1
    assert medium_tasks[0].id == task2.id


def test_list_tasks_filter_by_low_priority():
    """Test filtering tasks by low priority."""
    task1 = operations.create_task("Medium priority", priority="medium")
    task2 = operations.create_task("Low priority", priority="low")

    low_tasks = operations.list_tasks(priority_filter=Priority.LOW)

    assert len(low_tasks) == 1
    assert low_tasks[0].id == task2.id


def test_list_tasks_combined_filters():
    """Test filtering by both status and priority."""
    task1 = operations.create_task("Active high", priority="high")
    task2 = operations.create_task("Active medium", priority="medium")
    task3 = operations.create_task("Completed high", priority="high")
    operations.update_task_status(task3.id, Status.COMPLETED)

    filtered = operations.list_tasks(
        status_filter=Status.ACTIVE,
        priority_filter=Priority.HIGH
    )

    assert len(filtered) == 1
    assert filtered[0].id == task1.id


def test_list_tasks_sort_by_created_at_desc():
    """Test default sorting by created_at (newest first)."""
    task1 = operations.create_task("First")
    task2 = operations.create_task("Second")
    task3 = operations.create_task("Third")

    tasks = operations.list_tasks(sort_by="created_at")

    # Newest first
    assert tasks[0].id == task3.id
    assert tasks[1].id == task2.id
    assert tasks[2].id == task1.id


def test_list_tasks_sort_by_due_date_asc():
    """Test sorting by due date (earliest first)."""
    today = datetime.now()
    tomorrow = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    next_week = (today + timedelta(days=7)).strftime("%Y-%m-%d")

    task1 = operations.create_task("Due next week", due_date=next_week)
    task2 = operations.create_task("Due tomorrow", due_date=tomorrow)

    tasks = operations.list_tasks(sort_by="due_date")

    # Earliest first
    assert tasks[0].id == task2.id
    assert tasks[1].id == task1.id


def test_list_tasks_sort_by_due_date_none_last():
    """Test that tasks without due dates appear last when sorting by due_date."""
    today = datetime.now()
    tomorrow = (today + timedelta(days=1)).strftime("%Y-%m-%d")

    task1 = operations.create_task("No due date")
    task2 = operations.create_task("Has due date", due_date=tomorrow)

    tasks = operations.list_tasks(sort_by="due_date")

    # Tasks with due dates first, None last
    assert tasks[0].id == task2.id
    assert tasks[1].id == task1.id


def test_list_tasks_sort_by_priority():
    """Test sorting by priority (high→medium→low)."""
    task1 = operations.create_task("Low priority", priority="low")
    task2 = operations.create_task("High priority", priority="high")
    task3 = operations.create_task("Medium priority", priority="medium")

    tasks = operations.list_tasks(sort_by="priority")

    # High, Medium, Low order
    assert tasks[0].id == task2.id
    assert tasks[1].id == task3.id
    assert tasks[2].id == task1.id


def test_list_tasks_filter_and_sort():
    """Test combined filtering and sorting."""
    today = datetime.now()
    tomorrow = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    next_week = (today + timedelta(days=7)).strftime("%Y-%m-%d")

    task1 = operations.create_task("Active high tomorrow", priority="high", due_date=tomorrow)
    task2 = operations.create_task("Active high next week", priority="high", due_date=next_week)
    task3 = operations.create_task("Active medium", priority="medium")
    task4 = operations.create_task("Completed high", priority="high")
    operations.update_task_status(task4.id, Status.COMPLETED)

    filtered = operations.list_tasks(
        status_filter=Status.ACTIVE,
        priority_filter=Priority.HIGH,
        sort_by="due_date"
    )

    assert len(filtered) == 2
    assert filtered[0].id == task1.id  # Tomorrow (earliest)
    assert filtered[1].id == task2.id  # Next week


# Test Update Task Status

def test_mark_task_complete():
    """Test marking an active task as completed."""
    task = operations.create_task("Test task")
    assert task.status == Status.ACTIVE

    updated = operations.update_task_status(task.id, Status.COMPLETED)

    assert updated.status == Status.COMPLETED


def test_mark_task_incomplete():
    """Test marking a completed task as active."""
    task = operations.create_task("Test task")
    operations.update_task_status(task.id, Status.COMPLETED)

    updated = operations.update_task_status(task.id, Status.ACTIVE)

    assert updated.status == Status.ACTIVE


def test_mark_complete_sets_timestamp():
    """Test that marking a task complete sets the completed_at timestamp."""
    task = operations.create_task("Test task")
    assert task.completed_at is None

    updated = operations.update_task_status(task.id, Status.COMPLETED)

    assert updated.completed_at is not None


def test_mark_incomplete_clears_timestamp():
    """Test that marking a task incomplete clears the completed_at timestamp."""
    task = operations.create_task("Test task")
    operations.update_task_status(task.id, Status.COMPLETED)

    updated = operations.update_task_status(task.id, Status.ACTIVE)

    assert updated.completed_at is None


def test_update_status_persists_to_storage(storage):
    """Test that status changes are persisted to storage."""
    task = operations.create_task("Test task")
    operations.update_task_status(task.id, Status.COMPLETED)

    # Verify in storage
    stored_task = storage.get_by_id(task.id)
    assert stored_task.status == Status.COMPLETED


def test_update_nonexistent_task_raises_error():
    """Test that updating a nonexistent task raises TaskNotFoundError."""
    with pytest.raises(TaskNotFoundError):
        operations.update_task_status("nonexistent-id", Status.COMPLETED)


def test_mark_already_completed_task_complete():
    """Test that marking an already completed task as complete is idempotent."""
    task = operations.create_task("Test task")
    operations.update_task_status(task.id, Status.COMPLETED)

    # Mark complete again
    updated = operations.update_task_status(task.id, Status.COMPLETED)

    assert updated.status == Status.COMPLETED
    assert updated.completed_at is not None


# Test Delete Task

def test_delete_existing_task():
    """Test deleting an existing task."""
    task = operations.create_task("Test task")

    operations.delete_task(task.id)

    # Verify task is gone
    with pytest.raises(TaskNotFoundError):
        operations.get_task(task.id)


def test_delete_nonexistent_task_raises_error():
    """Test that deleting a nonexistent task raises TaskNotFoundError."""
    with pytest.raises(TaskNotFoundError):
        operations.delete_task("nonexistent-id")


def test_delete_persists_to_storage(storage):
    """Test that task deletion is persisted to storage."""
    task = operations.create_task("Test task")
    operations.delete_task(task.id)

    # Verify not in storage
    all_tasks = storage.get_all()
    assert len(all_tasks) == 0


def test_delete_removes_correct_task():
    """Test that only the specified task is removed when multiple exist."""
    task1 = operations.create_task("Task 1")
    task2 = operations.create_task("Task 2")
    task3 = operations.create_task("Task 3")

    operations.delete_task(task2.id)

    remaining = operations.list_tasks()
    assert len(remaining) == 2
    assert task1.id in [t.id for t in remaining]
    assert task3.id in [t.id for t in remaining]
    assert task2.id not in [t.id for t in remaining]


# Test Clear Completed Tasks

def test_clear_completed_tasks_removes_all_completed():
    """Test that clear_completed_tasks removes all completed tasks."""
    task1 = operations.create_task("Task 1")
    task2 = operations.create_task("Task 2")
    task3 = operations.create_task("Task 3")

    operations.update_task_status(task1.id, Status.COMPLETED)
    operations.update_task_status(task3.id, Status.COMPLETED)

    count = operations.clear_completed_tasks()

    assert count == 2
    remaining = operations.list_tasks()
    assert len(remaining) == 1
    assert remaining[0].id == task2.id


def test_clear_completed_tasks_preserves_active():
    """Test that clear_completed_tasks preserves all active tasks."""
    task1 = operations.create_task("Active 1")
    task2 = operations.create_task("Completed")
    task3 = operations.create_task("Active 2")

    operations.update_task_status(task2.id, Status.COMPLETED)
    operations.clear_completed_tasks()

    remaining = operations.list_tasks()
    assert len(remaining) == 2
    assert all(t.status == Status.ACTIVE for t in remaining)


def test_clear_completed_tasks_empty_list():
    """Test that clear_completed_tasks handles empty task list gracefully."""
    count = operations.clear_completed_tasks()

    assert count == 0


def test_clear_completed_tasks_persists_to_storage(storage):
    """Test that clearing completed tasks persists changes to storage."""
    task1 = operations.create_task("Active")
    task2 = operations.create_task("Completed")
    operations.update_task_status(task2.id, Status.COMPLETED)

    operations.clear_completed_tasks()

    # Verify in storage
    all_tasks = storage.get_all()
    assert len(all_tasks) == 1
    assert all_tasks[0].id == task1.id


def test_clear_completed_returns_count():
    """Test that clear_completed_tasks returns the count of removed tasks."""
    operations.create_task("Active")
    task2 = operations.create_task("Completed 1")
    task3 = operations.create_task("Completed 2")
    task4 = operations.create_task("Completed 3")

    operations.update_task_status(task2.id, Status.COMPLETED)
    operations.update_task_status(task3.id, Status.COMPLETED)
    operations.update_task_status(task4.id, Status.COMPLETED)

    count = operations.clear_completed_tasks()

    assert count == 3


# Test Edge Cases

def test_operations_with_storage_error(storage, monkeypatch):
    """Test that operations handle storage errors gracefully."""
    # Create a task first
    task = operations.create_task("Test task")

    # Mock storage.update to raise StorageError
    def mock_update(task):
        raise StorageError("Simulated storage error")

    monkeypatch.setattr(storage, "update", mock_update)

    # Should propagate StorageError
    with pytest.raises(StorageError):
        operations.update_task_status(task.id, Status.COMPLETED)


def test_concurrent_operations_safe(storage):
    """Test that multiple operations don't corrupt data."""
    # Create multiple tasks
    tasks = []
    for i in range(10):
        task = operations.create_task(f"Task {i}", priority="high" if i % 2 == 0 else "low")
        tasks.append(task)

    # Perform various operations
    operations.update_task_status(tasks[0].id, Status.COMPLETED)
    operations.update_task_status(tasks[2].id, Status.COMPLETED)
    operations.delete_task(tasks[5].id)
    operations.update_task_status(tasks[7].id, Status.COMPLETED)

    # Verify data integrity
    all_tasks = storage.get_all()
    assert len(all_tasks) == 9  # 10 created, 1 deleted

    completed = [t for t in all_tasks if t.status == Status.COMPLETED]
    assert len(completed) == 3


def test_list_tasks_large_dataset():
    """Test performance with 1000+ tasks."""
    # Create 1000 tasks
    for i in range(1000):
        priority = ["high", "medium", "low"][i % 3]
        operations.create_task(f"Task {i}", priority=priority)

    # This should complete reasonably quickly
    all_tasks = operations.list_tasks()
    assert len(all_tasks) == 1000

    # Test filtering on large dataset
    high_priority = operations.list_tasks(priority_filter=Priority.HIGH)
    assert len(high_priority) > 0

    # Test sorting on large dataset
    sorted_tasks = operations.list_tasks(sort_by="priority")
    assert len(sorted_tasks) == 1000
