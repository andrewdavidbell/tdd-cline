"""
Storage module for persisting tasks to JSON files.

This module provides the TaskStorage class for managing task persistence
with atomic writes and backup functionality.
"""

import json
import shutil
from pathlib import Path
from typing import List

from task_manager.models import Task


class StorageError(Exception):
    """Exception raised for storage-related errors."""
    pass


class TaskNotFoundError(Exception):
    """Exception raised when a task is not found."""
    pass


class TaskStorage:
    """
    Manages task persistence to JSON files with atomic writes.

    This class provides CRUD operations for tasks with safe file handling,
    including atomic writes and backup functionality to prevent data loss.
    """

    def __init__(self, file_path: str):
        """
        Initialise TaskStorage with the specified file path.

        Args:
            file_path: Path to the JSON file for storing tasks
        """
        self._file_path = Path(file_path)

        # Create directory if it doesn't exist
        self._file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create empty file if it doesn't exist
        if not self._file_path.exists():
            self._file_path.write_text('[]')

    def _validate_schema(self, data: any) -> None:
        """
        Validate that the loaded data has the correct schema.

        Args:
            data: Data loaded from JSON file

        Raises:
            StorageError: If the data schema is invalid
        """
        if not isinstance(data, list):
            raise StorageError("Invalid JSON schema: expected a list of tasks")

    def load(self) -> List[Task]:
        """
        Load all tasks from the JSON file.

        Returns:
            List of Task objects

        Raises:
            StorageError: If the file cannot be loaded or parsed
        """
        try:
            content = self._file_path.read_text()
            data = json.loads(content)

            # Validate schema
            self._validate_schema(data)

            # Convert dicts to Task objects
            tasks = [Task.from_dict(task_dict) for task_dict in data]
            return tasks

        except json.JSONDecodeError as e:
            raise StorageError(f"Failed to load tasks: invalid JSON format - {e}")
        except (OSError, IOError) as e:
            raise StorageError(f"Failed to load tasks: {e}")

    def save(self, tasks: List[Task]) -> None:
        """
        Save tasks to the JSON file using atomic write.

        Args:
            tasks: List of Task objects to save

        Raises:
            StorageError: If the file cannot be written
        """
        try:
            # Convert tasks to dicts
            data = [task.to_dict() for task in tasks]

            # Use atomic write
            self._atomic_write(data)

        except (OSError, IOError, PermissionError) as e:
            raise StorageError(f"Failed to save tasks: {e}")

    def _atomic_write(self, data: List[dict]) -> None:
        """
        Perform atomic write to prevent data corruption.

        Writes to a temporary file first, then renames it to the target file.
        This ensures the original file is not corrupted if the write fails.

        Args:
            data: List of task dictionaries to write

        Raises:
            OSError: If the write operation fails
        """
        # Write to temporary file
        temp_path = self._file_path.parent / f"{self._file_path.name}.tmp"

        try:
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2)

            # Atomically rename temp file to target file
            temp_path.rename(self._file_path)

            # Create backup after successful write (last known good state)
            self._create_backup()

        except Exception as e:
            # Clean up temp file if it exists
            if temp_path.exists():
                temp_path.unlink()
            raise

    def _create_backup(self) -> None:
        """
        Create a backup of the current storage file.

        The backup file is named with a .backup extension.
        """
        backup_path = self._file_path.parent / f"{self._file_path.name}.backup"
        try:
            shutil.copy2(self._file_path, backup_path)
        except (OSError, IOError):
            # Backup failure shouldn't prevent saves
            pass

    def get_all(self) -> List[Task]:
        """
        Get all tasks from storage.

        Returns:
            List of Task objects (new instances, not references)
        """
        tasks = self.load()
        # Return new instances to avoid reference issues
        return [Task.from_dict(task.to_dict()) for task in tasks]

    def get_by_id(self, task_id: str) -> Task:
        """
        Get a task by its ID.

        Args:
            task_id: The ID of the task to retrieve

        Returns:
            The Task object

        Raises:
            TaskNotFoundError: If no task with the given ID exists
        """
        tasks = self.load()
        for task in tasks:
            if task.id == task_id:
                return task

        raise TaskNotFoundError(f"Task with ID {task_id} not found")

    def add(self, task: Task) -> None:
        """
        Add a new task to storage.

        Args:
            task: The Task object to add

        Raises:
            StorageError: If a task with the same ID already exists
        """
        tasks = self.load()

        # Check for duplicate ID
        if any(t.id == task.id for t in tasks):
            raise StorageError(f"Task with ID {task.id} already exists")

        tasks.append(task)
        self.save(tasks)

    def remove(self, task_id: str) -> None:
        """
        Remove a task from storage.

        Args:
            task_id: The ID of the task to remove

        Raises:
            TaskNotFoundError: If no task with the given ID exists
        """
        tasks = self.load()

        # Find and remove the task
        original_length = len(tasks)
        tasks = [t for t in tasks if t.id != task_id]

        if len(tasks) == original_length:
            raise TaskNotFoundError(f"Task with ID {task_id} not found")

        self.save(tasks)

    def update(self, task: Task) -> None:
        """
        Update an existing task in storage.

        Args:
            task: The Task object with updated data

        Raises:
            TaskNotFoundError: If no task with the given ID exists
        """
        tasks = self.load()

        # Find and update the task
        updated = False
        for i, t in enumerate(tasks):
            if t.id == task.id:
                tasks[i] = task
                updated = True
                break

        if not updated:
            raise TaskNotFoundError(f"Task with ID {task.id} not found")

        self.save(tasks)
