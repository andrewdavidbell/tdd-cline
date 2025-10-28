"""
Test suite for CLI layer.

This module tests the command-line interface including argument parsing,
command handlers, output formatting, and error handling.
"""

import pytest
import io
import sys
from unittest.mock import patch, MagicMock
from src.task_manager.cli import (
    create_parser,
    cmd_add,
    cmd_list,
    cmd_complete,
    cmd_incomplete,
    cmd_delete,
    cmd_clear,
    format_task,
    format_task_list,
    main,
)
from src.task_manager.models import Task, Priority, Status, ValidationError
from src.task_manager.storage import TaskNotFoundError, StorageError
from datetime import datetime, timedelta


# Test Argument Parsing

def test_parser_has_all_subcommands():
    """Verify parser has all required subcommands."""
    parser = create_parser()
    # Get subcommands from the parser
    import argparse
    subparsers_actions = [
        action for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    ]
    assert len(subparsers_actions) > 0
    subparsers = subparsers_actions[0]
    commands = list(subparsers.choices.keys())
    assert 'add' in commands
    assert 'list' in commands
    assert 'complete' in commands
    assert 'incomplete' in commands
    assert 'delete' in commands
    assert 'clear' in commands


def test_add_command_required_title():
    """Verify add command requires --title."""
    parser = create_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(['add'])


def test_add_command_optional_description():
    """Verify add command has optional --description."""
    parser = create_parser()
    args = parser.parse_args(['add', '--title', 'Test'])
    assert hasattr(args, 'description')
    assert args.description is None


def test_add_command_optional_priority():
    """Verify add command has optional --priority with default."""
    parser = create_parser()
    args = parser.parse_args(['add', '--title', 'Test'])
    assert hasattr(args, 'priority')
    assert args.priority == 'medium'


def test_add_command_optional_due_date():
    """Verify add command has optional --due-date."""
    parser = create_parser()
    args = parser.parse_args(['add', '--title', 'Test'])
    assert hasattr(args, 'due_date')
    assert args.due_date is None


def test_list_command_optional_status():
    """Verify list command has optional --status filter."""
    parser = create_parser()
    args = parser.parse_args(['list'])
    assert hasattr(args, 'status')
    assert args.status is None


def test_list_command_optional_priority():
    """Verify list command has optional --priority filter."""
    parser = create_parser()
    args = parser.parse_args(['list'])
    assert hasattr(args, 'priority')
    assert args.priority is None


def test_list_command_optional_sort():
    """Verify list command has optional --sort-by."""
    parser = create_parser()
    args = parser.parse_args(['list'])
    assert hasattr(args, 'sort_by')
    assert args.sort_by == 'created_at'


def test_complete_command_required_id():
    """Verify complete command requires task_id."""
    parser = create_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(['complete'])


def test_incomplete_command_required_id():
    """Verify incomplete command requires task_id."""
    parser = create_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(['incomplete'])


def test_delete_command_required_id():
    """Verify delete command requires task_id."""
    parser = create_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(['delete'])


def test_clear_command_no_args():
    """Verify clear command requires no arguments."""
    parser = create_parser()
    args = parser.parse_args(['clear'])
    assert args.command == 'clear'


# Test Command Handlers

@patch('src.task_manager.cli.operations')
def test_cmd_add_creates_task(mock_ops):
    """Verify cmd_add calls operations.create_task()."""
    mock_task = Task(title='Test Task')
    mock_ops.create_task.return_value = mock_task

    args = MagicMock(title='Test Task', description=None, priority='medium', due_date=None)
    cmd_add(args)

    mock_ops.create_task.assert_called_once_with('Test Task', None, 'medium', None)


@patch('src.task_manager.cli.operations')
def test_cmd_add_displays_success_message(mock_ops, capsys):
    """Verify cmd_add displays success message."""
    mock_task = Task(title='Test Task')
    mock_ops.create_task.return_value = mock_task

    args = MagicMock(title='Test Task', description=None, priority='medium', due_date=None)
    cmd_add(args)

    captured = capsys.readouterr()
    assert 'Task created successfully' in captured.out


@patch('src.task_manager.cli.operations')
def test_cmd_add_displays_task_details(mock_ops, capsys):
    """Verify cmd_add displays task details."""
    mock_task = Task(title='Test Task')
    mock_ops.create_task.return_value = mock_task

    args = MagicMock(title='Test Task', description=None, priority='medium', due_date=None)
    cmd_add(args)

    captured = capsys.readouterr()
    assert str(mock_task.id) in captured.out
    assert 'Test Task' in captured.out


@patch('src.task_manager.cli.operations')
def test_cmd_add_handles_validation_error(mock_ops, capsys):
    """Verify cmd_add handles ValidationError."""
    mock_ops.create_task.side_effect = ValidationError('Invalid title')

    args = MagicMock(title='', description=None, priority='medium', due_date=None)
    cmd_add(args)

    captured = capsys.readouterr()
    assert 'Error' in captured.out
    assert 'Invalid title' in captured.out


@patch('src.task_manager.cli.operations')
def test_cmd_list_displays_all_tasks(mock_ops, capsys):
    """Verify cmd_list displays all tasks."""
    tasks = [Task(title='Task 1'), Task(title='Task 2')]
    mock_ops.list_tasks.return_value = tasks

    args = MagicMock(status=None, priority=None, sort_by='created_at')
    cmd_list(args)

    captured = capsys.readouterr()
    assert 'Task 1' in captured.out
    assert 'Task 2' in captured.out


@patch('src.task_manager.cli.operations')
def test_cmd_list_displays_empty_message(mock_ops, capsys):
    """Verify cmd_list shows message when no tasks."""
    mock_ops.list_tasks.return_value = []

    args = MagicMock(status=None, priority=None, sort_by='created_at')
    cmd_list(args)

    captured = capsys.readouterr()
    assert 'No tasks found' in captured.out


@patch('src.task_manager.cli.operations')
def test_cmd_list_filters_by_status(mock_ops):
    """Verify cmd_list applies status filter."""
    mock_ops.list_tasks.return_value = []

    args = MagicMock(status='active', priority=None, sort_by='created_at')
    cmd_list(args)

    mock_ops.list_tasks.assert_called_once_with('active', None, 'created_at')


@patch('src.task_manager.cli.operations')
def test_cmd_list_filters_by_priority(mock_ops):
    """Verify cmd_list applies priority filter."""
    mock_ops.list_tasks.return_value = []

    args = MagicMock(status=None, priority='high', sort_by='created_at')
    cmd_list(args)

    mock_ops.list_tasks.assert_called_once_with(None, 'high', 'created_at')


@patch('src.task_manager.cli.operations')
def test_cmd_list_sorts_correctly(mock_ops):
    """Verify cmd_list applies sort order."""
    mock_ops.list_tasks.return_value = []

    args = MagicMock(status=None, priority=None, sort_by='due_date')
    cmd_list(args)

    mock_ops.list_tasks.assert_called_once_with(None, None, 'due_date')


@patch('src.task_manager.cli.operations')
def test_cmd_complete_marks_task_complete(mock_ops):
    """Verify cmd_complete calls update_task_status()."""
    args = MagicMock(task_id='test-id')
    cmd_complete(args)

    mock_ops.update_task_status.assert_called_once_with('test-id', Status.COMPLETED)


@patch('src.task_manager.cli.operations')
def test_cmd_complete_displays_success_message(mock_ops, capsys):
    """Verify cmd_complete displays success message."""
    args = MagicMock(task_id='test-id')
    cmd_complete(args)

    captured = capsys.readouterr()
    assert 'marked as completed' in captured.out or 'completed successfully' in captured.out.lower()


@patch('src.task_manager.cli.operations')
def test_cmd_complete_handles_not_found_error(mock_ops, capsys):
    """Verify cmd_complete handles TaskNotFoundError."""
    mock_ops.update_task_status.side_effect = TaskNotFoundError('Task not found')

    args = MagicMock(task_id='invalid-id')
    cmd_complete(args)

    captured = capsys.readouterr()
    assert 'Error' in captured.out
    assert 'not found' in captured.out.lower()


@patch('src.task_manager.cli.operations')
def test_cmd_incomplete_marks_task_active(mock_ops):
    """Verify cmd_incomplete calls update_task_status()."""
    args = MagicMock(task_id='test-id')
    cmd_incomplete(args)

    mock_ops.update_task_status.assert_called_once_with('test-id', Status.ACTIVE)


@patch('src.task_manager.cli.operations')
def test_cmd_incomplete_displays_success_message(mock_ops, capsys):
    """Verify cmd_incomplete displays success message."""
    args = MagicMock(task_id='test-id')
    cmd_incomplete(args)

    captured = capsys.readouterr()
    assert 'marked as active' in captured.out or 'incomplete' in captured.out.lower()


@patch('src.task_manager.cli.operations')
def test_cmd_delete_removes_task(mock_ops):
    """Verify cmd_delete calls delete_task()."""
    args = MagicMock(task_id='test-id')
    cmd_delete(args)

    mock_ops.delete_task.assert_called_once_with('test-id')


@patch('src.task_manager.cli.operations')
def test_cmd_delete_displays_success_message(mock_ops, capsys):
    """Verify cmd_delete displays success message."""
    args = MagicMock(task_id='test-id')
    cmd_delete(args)

    captured = capsys.readouterr()
    assert 'deleted' in captured.out.lower()


@patch('src.task_manager.cli.operations')
def test_cmd_delete_handles_not_found_error(mock_ops, capsys):
    """Verify cmd_delete handles TaskNotFoundError."""
    mock_ops.delete_task.side_effect = TaskNotFoundError('Task not found')

    args = MagicMock(task_id='invalid-id')
    cmd_delete(args)

    captured = capsys.readouterr()
    assert 'Error' in captured.out
    assert 'not found' in captured.out.lower()


@patch('src.task_manager.cli.operations')
def test_cmd_clear_removes_completed_tasks(mock_ops):
    """Verify cmd_clear calls clear_completed_tasks()."""
    mock_ops.clear_completed_tasks.return_value = 3

    args = MagicMock()
    cmd_clear(args)

    mock_ops.clear_completed_tasks.assert_called_once()


@patch('src.task_manager.cli.operations')
def test_cmd_clear_displays_count_message(mock_ops, capsys):
    """Verify cmd_clear displays count of removed tasks."""
    mock_ops.clear_completed_tasks.return_value = 3

    args = MagicMock()
    cmd_clear(args)

    captured = capsys.readouterr()
    assert '3' in captured.out
    assert 'removed' in captured.out.lower() or 'deleted' in captured.out.lower() or 'cleared' in captured.out.lower()


@patch('src.task_manager.cli.operations')
def test_cmd_clear_displays_none_message(mock_ops, capsys):
    """Verify cmd_clear shows message when no completed tasks."""
    mock_ops.clear_completed_tasks.return_value = 0

    args = MagicMock()
    cmd_clear(args)

    captured = capsys.readouterr()
    assert '0' in captured.out or 'No' in captured.out


# Test Output Formatting

def test_format_task_includes_all_fields():
    """Verify format_task includes all task fields."""
    task = Task(
        title='Test Task',
        description='Test description',
        priority=Priority.HIGH,
        due_date='2025-12-31'
    )
    result = format_task(task)

    assert str(task.id) in result
    assert 'Test Task' in result
    assert 'high' in result.lower()
    assert 'active' in result.lower()


def test_format_task_handles_none_values():
    """Verify format_task handles None values correctly."""
    task = Task(title='Test Task')
    result = format_task(task)

    # Should not crash with None description and due_date
    assert 'Test Task' in result


def test_format_task_displays_due_date():
    """Verify format_task displays due date correctly."""
    task = Task(title='Test Task', due_date='2025-12-31')
    result = format_task(task)

    assert '2025-12-31' in result


def test_format_task_list_as_table():
    """Verify format_task_list displays tasks in table format."""
    tasks = [
        Task(title='Task 1'),
        Task(title='Task 2')
    ]
    result = format_task_list(tasks)

    # Should contain both tasks
    assert 'Task 1' in result
    assert 'Task 2' in result


def test_format_task_list_headers():
    """Verify format_task_list has appropriate headers."""
    tasks = [Task(title='Test Task')]
    result = format_task_list(tasks)

    # Should have column headers
    assert 'ID' in result or 'Title' in result


def test_format_task_list_alignment():
    """Verify format_task_list has proper column alignment."""
    tasks = [Task(title='Test Task')]
    result = format_task_list(tasks)

    # Should have some structure (not just plain text)
    # At minimum should have line breaks
    assert '\n' in result


# Test Help Text

def test_main_help_lists_commands(capsys):
    """Verify --help shows all commands."""
    parser = create_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(['--help'])


def test_add_help_shows_options(capsys):
    """Verify add --help shows all options."""
    parser = create_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(['add', '--help'])


def test_list_help_shows_filters(capsys):
    """Verify list --help shows filter options."""
    parser = create_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(['list', '--help'])


# Test Error Handling

@patch('src.task_manager.cli.operations')
def test_handles_storage_error_gracefully(mock_ops, capsys):
    """Verify StorageError is displayed to user."""
    mock_ops.create_task.side_effect = StorageError('Disk full')

    args = MagicMock(title='Test', description=None, priority='medium', due_date=None)
    cmd_add(args)

    captured = capsys.readouterr()
    assert 'Error' in captured.out
    assert 'Disk full' in captured.out


def test_invalid_command_shows_error():
    """Verify unknown command shows error."""
    parser = create_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(['invalid_command'])


def test_missing_required_arg_shows_error():
    """Verify missing required argument shows usage."""
    parser = create_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(['add'])


# Test Entry Point

def test_main_entry_point_exists():
    """Verify main() function exists."""
    assert callable(main)


@patch('src.task_manager.cli.create_parser')
def test_main_entry_point_callable(mock_create_parser):
    """Verify main() can be called from command line."""
    mock_parser = MagicMock()
    mock_parser.parse_args.return_value = MagicMock(
        command='list',
        status=None,
        priority=None,
        sort_by='created_at'
    )
    mock_create_parser.return_value = mock_parser

    with patch('src.task_manager.cli.cmd_list'):
        result = main()
        assert result == 0
