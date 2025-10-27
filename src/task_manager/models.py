"""
Domain models for the Task Manager application.

This module contains the core data structures including Task, Priority, and Status.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class Priority(Enum):
    """Task priority levels."""
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'


class Status(Enum):
    """Task status states."""
    ACTIVE = 'active'
    COMPLETED = 'completed'


class ValidationError(Exception):
    """Raised when task validation fails."""
    pass


@dataclass
class Task:
    """
    Represents a task with title, description, priority, due date, and status.

    Attributes:
        id: Unique identifier (UUID)
        title: Task title (required, max 200 chars)
        description: Task description (optional, max 1000 chars)
        priority: Task priority (HIGH, MEDIUM, LOW)
        due_date: Due date in YYYY-MM-DD format (optional)
        status: Task status (ACTIVE, COMPLETED)
        created_at: Creation timestamp (ISO format)
        completed_at: Completion timestamp (ISO format, optional)
    """

    title: str
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    due_date: Optional[str] = None
    status: Status = Status.ACTIVE
    id: str = None
    created_at: str = None
    completed_at: Optional[str] = None

    def __post_init__(self):
        """Initialize task with auto-generated fields and normalization."""
        # Auto-generate ID if not provided
        if self.id is None:
            self.id = str(uuid.uuid4())

        # Auto-set created_at if not provided
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

        # Strip whitespace from title
        if isinstance(self.title, str):
            self.title = self.title.strip()

        # Handle priority as string (case insensitive)
        if isinstance(self.priority, str):
            priority_str = self.priority.lower()
            if priority_str == 'high':
                self.priority = Priority.HIGH
            elif priority_str == 'medium':
                self.priority = Priority.MEDIUM
            elif priority_str == 'low':
                self.priority = Priority.LOW
            else:
                raise ValueError(f"Invalid priority: {self.priority}")

        # Handle status as string
        if isinstance(self.status, str):
            status_str = self.status.lower()
            if status_str == 'active':
                self.status = Status.ACTIVE
            elif status_str == 'completed':
                self.status = Status.COMPLETED
            else:
                raise ValueError(f"Invalid status: {self.status}")

    def validate(self) -> None:
        """
        Validate task fields.

        Raises:
            ValidationError: If validation fails
        """
        # Validate title
        if not self.title or not self.title.strip():
            raise ValidationError("Task title cannot be empty")

        if len(self.title) > 200:
            raise ValidationError("Task title cannot exceed 200 characters")

        # Validate description
        if self.description is not None and len(self.description) > 1000:
            raise ValidationError("Task description cannot exceed 1000 characters")

        # Validate due_date
        if self.due_date is not None:
            try:
                due_date_obj = datetime.strptime(self.due_date, "%Y-%m-%d")
                # Check if date is in the past
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                if due_date_obj.replace(hour=0, minute=0, second=0, microsecond=0) < today:
                    raise ValidationError("Invalid due_date: cannot be in the past")
            except ValueError:
                raise ValidationError("Invalid due_date format. Use YYYY-MM-DD")

    def mark_complete(self) -> None:
        """Mark task as completed and set completion timestamp."""
        self.status = Status.COMPLETED
        self.completed_at = datetime.now().isoformat()

    def mark_incomplete(self) -> None:
        """Mark task as active and clear completion timestamp."""
        self.status = Status.ACTIVE
        self.completed_at = None

    def to_dict(self) -> dict:
        """
        Serialize task to dictionary.

        Returns:
            Dictionary representation of the task
        """
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority.value if isinstance(self.priority, Priority) else self.priority,
            'due_date': self.due_date,
            'status': self.status.value if isinstance(self.status, Status) else self.status,
            'created_at': self.created_at,
            'completed_at': self.completed_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        """
        Create task from dictionary.

        Args:
            data: Dictionary containing task data

        Returns:
            Task instance

        Raises:
            ValidationError: If required fields are missing
            KeyError: If required fields are missing
        """
        # Ensure required fields are present
        if 'title' not in data:
            raise KeyError("Missing required field: title")

        # Create task with all fields from dict
        task = cls(
            id=data.get('id'),
            title=data['title'],
            description=data.get('description'),
            priority=data.get('priority', 'medium'),
            due_date=data.get('due_date'),
            status=data.get('status', 'active'),
            created_at=data.get('created_at'),
            completed_at=data.get('completed_at')
        )

        return task

    def __eq__(self, other: object) -> bool:
        """
        Compare tasks based on ID.

        Args:
            other: Another task to compare with

        Returns:
            True if tasks have the same ID, False otherwise
        """
        if not isinstance(other, Task):
            return False
        return self.id == other.id
