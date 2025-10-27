"""
Tests for the Task model and related enums.

This module tests the domain models following TD-AID methodology.
All tests written before implementation.
"""

import pytest
from datetime import datetime, timedelta
import uuid


# =============================================================================
# Test Priority Enum
# =============================================================================

def test_priority_enum_has_correct_values():
    """Verify Priority enum has HIGH, MEDIUM, LOW values."""
    from task_manager.models import Priority

    assert hasattr(Priority, 'HIGH')
    assert hasattr(Priority, 'MEDIUM')
    assert hasattr(Priority, 'LOW')


def test_priority_enum_values():
    """Verify Priority enum values are correct strings."""
    from task_manager.models import Priority

    assert Priority.HIGH.value == 'high'
    assert Priority.MEDIUM.value == 'medium'
    assert Priority.LOW.value == 'low'


# =============================================================================
# Test Status Enum
# =============================================================================

def test_status_enum_has_correct_values():
    """Verify Status enum has ACTIVE, COMPLETED values."""
    from task_manager.models import Status

    assert hasattr(Status, 'ACTIVE')
    assert hasattr(Status, 'COMPLETED')


def test_status_enum_values():
    """Verify Status enum values are correct strings."""
    from task_manager.models import Status

    assert Status.ACTIVE.value == 'active'
    assert Status.COMPLETED.value == 'completed'


# =============================================================================
# Test Task Creation
# =============================================================================

def test_create_task_with_minimal_fields():
    """Create task with only title."""
    from task_manager.models import Task

    task = Task(title="Test task")

    assert task.title == "Test task"
    assert task.description is None
    assert task.due_date is None


def test_create_task_with_all_fields():
    """Create task with all optional fields."""
    from task_manager.models import Task, Priority

    due_date = "2025-12-31"
    task = Task(
        title="Complete task",
        description="Task description",
        priority=Priority.HIGH,
        due_date=due_date
    )

    assert task.title == "Complete task"
    assert task.description == "Task description"
    assert task.priority == Priority.HIGH
    assert task.due_date == due_date


def test_task_auto_generates_id():
    """Verify UUID is auto-generated."""
    from task_manager.models import Task

    task = Task(title="Test task")

    assert task.id is not None
    assert isinstance(task.id, str)
    # Verify it's a valid UUID
    uuid.UUID(task.id)


def test_task_auto_sets_created_at():
    """Verify timestamp is auto-set."""
    from task_manager.models import Task

    before = datetime.now()
    task = Task(title="Test task")
    after = datetime.now()

    assert task.created_at is not None
    created = datetime.fromisoformat(task.created_at)
    assert before <= created <= after


def test_task_defaults_status_to_active():
    """Verify default status."""
    from task_manager.models import Task, Status

    task = Task(title="Test task")

    assert task.status == Status.ACTIVE


def test_task_defaults_priority_to_medium():
    """Verify default priority."""
    from task_manager.models import Task, Priority

    task = Task(title="Test task")

    assert task.priority == Priority.MEDIUM


def test_task_completed_at_is_none_for_new_task():
    """Verify null completed_at."""
    from task_manager.models import Task

    task = Task(title="Test task")

    assert task.completed_at is None


# =============================================================================
# Test Task Validation
# =============================================================================

def test_validate_empty_title_raises_error():
    """Empty string should fail."""
    from task_manager.models import Task, ValidationError

    with pytest.raises(ValidationError, match="title"):
        task = Task(title="")
        task.validate()


def test_validate_whitespace_only_title_raises_error():
    """Whitespace-only title should fail."""
    from task_manager.models import Task, ValidationError

    with pytest.raises(ValidationError, match="title"):
        task = Task(title="   ")
        task.validate()


def test_validate_title_too_long_raises_error():
    """Title >200 chars should fail."""
    from task_manager.models import Task, ValidationError

    long_title = "x" * 201
    with pytest.raises(ValidationError, match="title"):
        task = Task(title=long_title)
        task.validate()


def test_validate_description_too_long_raises_error():
    """Description >1000 chars should fail."""
    from task_manager.models import Task, ValidationError

    long_description = "x" * 1001
    with pytest.raises(ValidationError, match="description"):
        task = Task(title="Test", description=long_description)
        task.validate()


def test_validate_invalid_priority_raises_error():
    """Invalid priority string should fail."""
    from task_manager.models import Task, ValidationError

    with pytest.raises((ValidationError, ValueError)):
        task = Task(title="Test", priority="urgent")
        task.validate()


def test_validate_invalid_due_date_format_raises_error():
    """Invalid date format should fail."""
    from task_manager.models import Task, ValidationError

    with pytest.raises(ValidationError, match="due_date"):
        task = Task(title="Test", due_date="2025-13-45")
        task.validate()


def test_validate_past_due_date_raises_error():
    """Yesterday's date should fail."""
    from task_manager.models import Task, ValidationError

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    with pytest.raises(ValidationError, match="due_date"):
        task = Task(title="Test", due_date=yesterday)
        task.validate()


def test_validate_accepts_future_due_date():
    """Tomorrow's date should pass."""
    from task_manager.models import Task

    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    task = Task(title="Test", due_date=tomorrow)

    # Should not raise
    task.validate()


def test_validate_accepts_none_due_date():
    """None due_date should pass."""
    from task_manager.models import Task

    task = Task(title="Test", due_date=None)

    # Should not raise
    task.validate()


# =============================================================================
# Test Task Methods
# =============================================================================

def test_mark_complete_sets_status_to_completed():
    """Status changes to COMPLETED."""
    from task_manager.models import Task, Status

    task = Task(title="Test task")
    task.mark_complete()

    assert task.status == Status.COMPLETED


def test_mark_complete_sets_completed_at_timestamp():
    """Timestamp is set."""
    from task_manager.models import Task

    task = Task(title="Test task")
    before = datetime.now()
    task.mark_complete()
    after = datetime.now()

    assert task.completed_at is not None
    completed = datetime.fromisoformat(task.completed_at)
    assert before <= completed <= after


def test_mark_incomplete_sets_status_to_active():
    """Status changes to ACTIVE."""
    from task_manager.models import Task, Status

    task = Task(title="Test task")
    task.mark_complete()
    task.mark_incomplete()

    assert task.status == Status.ACTIVE


def test_mark_incomplete_clears_completed_at():
    """Timestamp is cleared."""
    from task_manager.models import Task

    task = Task(title="Test task")
    task.mark_complete()
    task.mark_incomplete()

    assert task.completed_at is None


def test_to_dict_serialises_all_fields():
    """All fields present in dict."""
    from task_manager.models import Task, Priority

    task = Task(
        title="Test task",
        description="Description",
        priority=Priority.HIGH,
        due_date="2025-12-31"
    )

    result = task.to_dict()

    assert result['id'] == task.id
    assert result['title'] == "Test task"
    assert result['description'] == "Description"
    assert result['priority'] == 'high'
    assert result['due_date'] == "2025-12-31"
    assert result['status'] == 'active'
    assert result['created_at'] == task.created_at
    assert result['completed_at'] is None


def test_to_dict_handles_none_values():
    """None values serialised correctly."""
    from task_manager.models import Task

    task = Task(title="Test task")
    result = task.to_dict()

    assert result['description'] is None
    assert result['due_date'] is None
    assert result['completed_at'] is None


def test_from_dict_creates_task():
    """Task created from valid dict."""
    from task_manager.models import Task

    data = {
        'id': str(uuid.uuid4()),
        'title': 'Test task',
        'description': 'Description',
        'priority': 'high',
        'due_date': '2025-12-31',
        'status': 'active',
        'created_at': datetime.now().isoformat(),
        'completed_at': None
    }

    task = Task.from_dict(data)

    assert task.id == data['id']
    assert task.title == data['title']
    assert task.description == data['description']


def test_from_dict_with_missing_required_fields_raises_error():
    """Missing title fails."""
    from task_manager.models import Task, ValidationError

    data = {
        'id': str(uuid.uuid4()),
        'description': 'Description',
        'priority': 'medium',
        'status': 'active',
        'created_at': datetime.now().isoformat()
    }

    with pytest.raises((ValidationError, KeyError)):
        Task.from_dict(data)


def test_from_dict_preserves_id():
    """ID from dict is preserved."""
    from task_manager.models import Task

    task_id = str(uuid.uuid4())
    data = {
        'id': task_id,
        'title': 'Test task',
        'description': None,
        'priority': 'medium',
        'due_date': None,
        'status': 'active',
        'created_at': datetime.now().isoformat(),
        'completed_at': None
    }

    task = Task.from_dict(data)

    assert task.id == task_id


def test_task_equality_based_on_id():
    """Two tasks with same ID are equal."""
    from task_manager.models import Task

    task_id = str(uuid.uuid4())
    task1 = Task(title="Task 1")
    task1.id = task_id

    task2 = Task(title="Task 2")
    task2.id = task_id

    assert task1 == task2


# =============================================================================
# Test Edge Cases
# =============================================================================

def test_priority_case_insensitive():
    """Priority values case insensitive."""
    from task_manager.models import Task, Priority

    task1 = Task(title="Test", priority="HIGH")
    task2 = Task(title="Test", priority="High")
    task3 = Task(title="Test", priority="high")

    assert task1.priority == Priority.HIGH
    assert task2.priority == Priority.HIGH
    assert task3.priority == Priority.HIGH


def test_title_strips_whitespace():
    """Leading/trailing spaces removed."""
    from task_manager.models import Task

    task = Task(title="  Test task  ")

    assert task.title == "Test task"


def test_unicode_in_title_and_description():
    """Unicode chars supported."""
    from task_manager.models import Task

    task = Task(
        title="测试任务 🚀",
        description="Emoji test: 👍 café résumé"
    )

    assert task.title == "测试任务 🚀"
    assert task.description == "Emoji test: 👍 café résumé"
