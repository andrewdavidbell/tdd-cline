"""
Task operations module.

This module provides business logic for task management operations including
CRUD operations, filtering, sorting, and bulk operations.
"""

from pathlib import Path
from typing import Optional, List

from task_manager.models import Task, Priority, Status
from task_manager.storage import TaskStorage


# Module-level storage instance (can be overridden for testing)
_storage: Optional[TaskStorage] = None


def _get_storage() -> TaskStorage:
    """Get the storage instance, creating default if needed."""
    global _storage
    if _storage is None:
        # Default storage location
        storage_path = Path.home() / ".task_manager" / "tasks.json"
        _storage = TaskStorage(storage_path)
    return _storage


def create_task(
    title: str,
    description: Optional[str] = None,
    priority: str = "medium",
    due_date: Optional[str] = None
) -> Task:
    """
    Create a new task and persist it to storage.

    Args:
        title: The task title (required)
        description: Optional task description
        priority: Task priority ('high', 'medium', or 'low'). Defaults to 'medium'
        due_date: Optional due date in YYYY-MM-DD format

    Returns:
        The created Task object

    Raises:
        ValidationError: If the task data is invalid
        StorageError: If there's an error saving to storage
    """
    from task_manager.models import ValidationError

    try:
        task = Task(
            title=title,
            description=description,
            priority=priority,
            due_date=due_date
        )
        task.validate()
    except ValueError as e:
        # Convert ValueError to ValidationError for consistent API
        raise ValidationError(str(e))

    storage = _get_storage()
    storage.add(task)

    return task


def get_task(task_id: str) -> Task:
    """
    Retrieve a task by its ID.

    Args:
        task_id: The unique task identifier

    Returns:
        The Task object

    Raises:
        TaskNotFoundError: If no task exists with the given ID
    """
    storage = _get_storage()
    return storage.get_by_id(task_id)


def list_tasks(
    status_filter: Optional[Status] = None,
    priority_filter: Optional[Priority] = None,
    sort_by: str = "created_at"
) -> List[Task]:
    """
    List all tasks with optional filtering and sorting.

    Args:
        status_filter: Optional status to filter by (ACTIVE or COMPLETED)
        priority_filter: Optional priority to filter by (HIGH, MEDIUM, or LOW)
        sort_by: Field to sort by ('created_at', 'due_date', or 'priority').
                Defaults to 'created_at'

    Returns:
        List of Task objects matching the filters, sorted as specified
    """
    storage = _get_storage()
    tasks = storage.get_all()

    # Apply filters
    if status_filter is not None:
        tasks = [t for t in tasks if t.status == status_filter]

    if priority_filter is not None:
        tasks = [t for t in tasks if t.priority == priority_filter]

    # Apply sorting
    if sort_by == "created_at":
        # Sort by created_at descending (newest first)
        tasks.sort(key=lambda t: t.created_at, reverse=True)
    elif sort_by == "due_date":
        # Sort by due_date ascending (earliest first), None values last
        tasks.sort(key=lambda t: (t.due_date is None, t.due_date or ""))
    elif sort_by == "priority":
        # Sort by priority: HIGH, MEDIUM, LOW
        priority_order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
        tasks.sort(key=lambda t: priority_order[t.priority])

    return tasks


def update_task_status(task_id: str, status: Status) -> Task:
    """
    Update a task's status (mark as complete or incomplete).

    Args:
        task_id: The unique task identifier
        status: The new status (ACTIVE or COMPLETED)

    Returns:
        The updated Task object

    Raises:
        TaskNotFoundError: If no task exists with the given ID
        StorageError: If there's an error saving to storage
    """
    storage = _get_storage()
    task = storage.get_by_id(task_id)

    # Update status using task methods
    if status == Status.COMPLETED:
        task.mark_complete()
    else:
        task.mark_incomplete()

    # Persist changes
    storage.update(task)

    return task


def delete_task(task_id: str) -> None:
    """
    Delete a task by its ID.

    Args:
        task_id: The unique task identifier

    Raises:
        TaskNotFoundError: If no task exists with the given ID
        StorageError: If there's an error saving to storage
    """
    storage = _get_storage()
    storage.remove(task_id)


def clear_completed_tasks() -> int:
    """
    Remove all completed tasks from storage.

    Returns:
        The number of tasks removed
    """
    storage = _get_storage()
    all_tasks = storage.get_all()

    # Find all completed tasks
    completed_tasks = [t for t in all_tasks if t.status == Status.COMPLETED]

    # Remove each completed task
    for task in completed_tasks:
        storage.remove(task.id)

    return len(completed_tasks)
